"""Step-by-step reporting walks each investigation's own report in template order."""
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from primer.curriculum import Curriculum
from primer import radiology_catalog

FLAGSHIPS = ('ra.ct-coronary', 'ra.mri-prostate')
# Investigation-specific anatomy or reporting-aim overrides.
CORRECTED = {
    'ra.hip-arthroplasty': 'hip',
    'ra.mri-diabetic-foot': 'ankle', 'ra.paediatric-elbow-fractures': 'elbow',
    'ra.vascular-anomalies': 'aorta', 'ra.carotid-obstruction': 'neck',
    'ra.paediatric-neck-masses': 'neck', 'ra.paediatric-cystic-abdominal-masses': 'abdomen',
    'ra.paediatric-solid-abdominal-masses': 'abdomen', 'ra.paediatric-renal-tumours': 'renal',
    'ra.paediatric-ultrasound-values': 'abdomen', 'ra.recist': 'abdomen',
    'ra.aortic-aneurysm-rupture': 'aorta',
    'ra.cardiovascular-devices': 'heart',
    'ra.cardiac-masses': 'heart',
    'ra.mri-cardiomyopathy': 'heart',
    'ra.mra-peripheral-vessels': 'aorta',
    'ra.ct-cardiovascular-pearls': 'heart',
    'ra.pulmonary-hypertension': 'thorax',
    'ra.hrct-cystic-lung': 'thorax',
    'ra.hrct-lung': 'thorax',
}


@pytest.fixture(scope='module')
def curriculum():
    return Curriculum()


@pytest.fixture(scope='module')
def references(curriculum):
    return {item['id']: radiology_catalog.detail(curriculum, item)['radiology_reference']
            for item in radiology_catalog.catalogue()['investigations']}


@pytest.fixture
def fresh_steps():
    radiology_catalog._steps.cache_clear()
    yield
    radiology_catalog._steps.cache_clear()


def _landmarks():
    source = (ROOT / 'web/radiology-reference-models.js').read_text(encoding='utf-8')
    return {match.group(1): set(re.findall(r"(\w+)\s*:\s*'", match.group(2)))
            for match in re.finditer(r"family\('(\w+)',\s*\{([^}]*)\}", source)}


def test_every_investigation_has_a_complete_authored_walkthrough(references):
    assert len(references) == 137
    for identifier, ref in references.items():
        walk = ref['walkthrough']
        headings = [section['heading'] for section in ref['report_templates'][0]['sections']]
        assert walk['complete'], identifier
        assert walk['template_id'] == ref['report_templates'][0]['id']
        assert 5 <= len(walk['steps']) <= 8, identifier
        owned = [heading for step in walk['steps'] for heading in step['sections']]
        # Introduction, steps and impression partition the template, in its order.
        assert walk['start']['sections'] + owned + walk['finish']['sections'] == headings, identifier
        assert walk['start']['sections'] and any('IMPRESSION' in h for h in walk['finish']['sections'])
        for step in walk['steps']:
            assert step['label'] and step['detail'] and step['look'], identifier
            assert 1 <= len(step['findings']) <= 6, identifier
            assert set(step['normal']) <= set(step['sections']), identifier
        figures = {image['id'] for image in ref['key_images']}
        available = figures | {image['id'] for image in ref.get('structure_atlas', [])}
        placed = set(walk['start']['images']).union(*(step['images'] for step in walk['steps']))
        assert figures <= placed <= available, identifier
        measured = [name for step in walk['steps'] for name in step['measurements']]
        assert set(measured) == {row['name'] for row in ref['reporting']['measurements']}, identifier


def test_steps_follow_the_scoped_reporting_guide(references):
    for identifier, ref in references.items():
        if identifier in FLAGSHIPS:
            continue
        guide = [[section['heading']] for section in ref['reporting']['template_sections']]
        assert [step['sections'] for step in ref['walkthrough']['steps']] == guide, identifier


def test_step_landmarks_and_mesh_parts_exist(references):
    families = _landmarks()
    manifest = json.loads(radiology_catalog.MESH_MANIFEST.read_text(encoding='utf-8'))
    for identifier, ref in references.items():
        model = ref['walkthrough']['spatial_model']
        steps = ref['walkthrough']['steps']
        assert model['family'] in families, identifier
        assert model['focus'][0] == steps[0]['landmark'] or not model['scenario'].startswith('radiology-investigation:')
        region = radiology_catalog.mesh_region(model['family'])
        parts = {part['id'] for part in manifest['regions'][region]['parts']} if region else set()
        for step in steps:
            assert step['landmark'] in families[model['family']], (identifier, step['landmark'])
            assert set(step['parts']) <= parts, identifier
    shoulder = references['ra.mri-shoulder']['walkthrough']['steps']
    cuff = {manifest['parts'][part]['name'].lower() for part in shoulder[0]['parts']}
    assert any('supraspinatus' in name for name in cuff)


def test_investigation_anatomy_or_scope_is_overridden(references):
    corrected = {identifier: ref['walkthrough']['spatial_model']['family'] for identifier, ref in references.items()
                 if ref['walkthrough']['spatial_model']['scenario'].startswith('radiology-investigation:')}
    assert corrected == CORRECTED
    for identifier in CORRECTED:
        model = references[identifier]['walkthrough']['spatial_model']
        assert model['scenario'] == 'radiology-investigation:' + identifier
        assert model['id'] == 'radiology-model-' + identifier
        assert model['reporting_aim'] in model['instructions']
    # The paediatric elbow reference no longer shows the hip module's anatomy or fields.
    elbow = references['ra.paediatric-elbow-fractures']
    assert 'OSSIFICATION AND GROWTH PLATES' in [s['heading'] for s in elbow['report_templates'][0]['sections']]
    assert not re.search(r'\bhip\b', json.dumps(elbow['reporting']['template_sections']).lower())


def test_index_reports_step_counts(curriculum, references):
    modules = radiology_catalog.index(curriculum)['modules']
    assert {m['id']: m['step_count'] for m in modules} == {
        identifier: len(ref['walkthrough']['steps']) for identifier, ref in references.items()}
    assert {m['id']: m['model_family'] for m in modules if m['id'] in CORRECTED} == dict(CORRECTED, **{'ra.mri-diabetic-foot': 'foot'})


def _mutated(monkeypatch, identifier, mutate):
    data = copy.deepcopy(radiology_catalog._steps())
    mutate(data['investigations'][identifier])
    monkeypatch.setattr(radiology_catalog, '_steps', lambda: data)


@pytest.mark.parametrize('mutate, message', [
    (lambda e: e['steps'][0].update(sections=['NOT A SECTION']), 'own template'),
    (lambda e: e['steps'][1].update(sections=e['steps'][0]['sections']), 'one step'),
    (lambda e: e['steps'].pop(1), 'Every finding section'),
    (lambda e: e['steps'][-1].update(normal=None, sections=[*e['steps'][-1]['sections'], 'IMPRESSION']),
     'introductory and impression'),
    (lambda e: e['steps'][0].update(images=['ra-mri-shoulder-missing']), 'unknown or repeated figure'),
    (lambda e: e['steps'][0].update(measurements=['Invented measure']), 'unknown or repeated measurement'),
    (lambda e: e['steps'][0].update(parts=['FJ0000']), 'unknown or repeated anatomical part'),
    (lambda e: e['steps'][0].update(images=e['steps'][0]['images'][:1] * 2), 'unknown or repeated figure'),
    (lambda e: e['steps'][0].pop('look'), 'needs look'),
    (lambda e: e['steps'][0].update(tip=' '), 'needs tip'),
    (lambda e: e['steps'][0].update(findings=[]), 'one to six'),
    (lambda e: e['steps'][0].update(findings=['Finding __.'] * 7), 'one to six'),
    (lambda e: e['steps'][0].update(normal={'IMPRESSION': 'Normal.'}), 'belong to the step sections'),
    (lambda e: e['steps'][0].update(normal={'ROTATOR CUFF': ''}), 'Empty normal'),
    (lambda e: e['steps'][0].update(landmark=''), '3D landmark'),
    (lambda e: e['steps'][0].update(measurements=[]), 'Every measurement'),
    (lambda e: e['steps'][0].update(sections=['ROTATOR CUFF', 'MUSCLE QUALITY'], normal='Normal.')
     or e['steps'].pop(1), 'shared normal'),
    (lambda e: e.update(model={'family': 'elbow'}), 'reporting aim'),
])
def test_invalid_step_guides_are_rejected(curriculum, monkeypatch, mutate, message):
    _mutated(monkeypatch, 'ra.mri-shoulder', mutate)
    with pytest.raises(ValueError, match=message):
        radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.mri-shoulder'))


def test_unauthored_investigation_walks_its_own_fields(curriculum, monkeypatch):
    monkeypatch.setattr(radiology_catalog, '_steps', lambda: {'investigations': {}, 'reviewed_at': {}})
    for identifier in ('ra.mri-shoulder', 'ra.paediatric-elbow-fractures', *FLAGSHIPS):
        ref = radiology_catalog.detail(curriculum, radiology_catalog.resolve(identifier))['radiology_reference']
        walk = ref['walkthrough']
        assert not walk['complete']
        assert walk['reviewed_at'] == ref['reporting']['reviewed_at']
        assert not ref['walkthrough']['spatial_model']['scenario'].startswith('radiology-investigation:')
        assert all(step['label'] and step['detail'] and step['landmark'] for step in walk['steps'])
        if identifier not in FLAGSHIPS:
            assert [s['sections'] for s in walk['steps']] == [
                [s['heading']] for s in ref['reporting']['template_sections']]


def _write_steps(directory, name, section, investigations, reviewed='2026-09-25'):
    (directory / name).write_text(json.dumps(
        {'reviewed_at': reviewed, 'section': section, 'investigations': investigations}), encoding='utf-8')


def test_step_files_are_filed_once_under_their_specialty(tmp_path, monkeypatch, fresh_steps):
    monkeypatch.setattr(radiology_catalog, 'STEP_DIR', tmp_path)
    entry = {'steps': []}
    _write_steps(tmp_path, 'a.json', 'Musculoskeletal', {'ra.mri-shoulder': entry})
    assert radiology_catalog._steps()['reviewed_at'] == {'ra.mri-shoulder': '2026-09-25'}
    for name, section, investigations, message in (
            ('b.json', 'Musculoskeletal', {'ra.mri-shoulder': entry}, 'Duplicate'),
            ('b.json', 'Abdomen', {'ra.mri-knee': entry}, 'wrong specialty'),
            ('b.json', 'Musculoskeletal', {'ra.not-a-source': entry}, 'no Radiology Assistant')):
        _write_steps(tmp_path, name, section, investigations)
        radiology_catalog._steps.cache_clear()
        with pytest.raises(ValueError, match=message):
            radiology_catalog._steps()
    _write_steps(tmp_path, 'b.json', 'Abdomen', {}, reviewed='25 September')
    radiology_catalog._steps.cache_clear()
    with pytest.raises(ValueError):
        radiology_catalog._steps()


def test_step_files_are_canonical_and_cover_each_specialty():
    sections = {}
    for path in sorted(radiology_catalog.STEP_DIR.glob('*.json')):
        text = path.read_text(encoding='utf-8')
        data = json.loads(text)
        assert text == json.dumps(data, indent=2, ensure_ascii=False) + '\n', path.name
        assert data['section'] not in sections
        sections[data['section']] = set(data['investigations'])
    expected = {}
    for item in radiology_catalog.catalogue()['investigations']:
        expected.setdefault(item['section'], set()).add(item['id'])
    assert sections == expected


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')
def test_walkthrough_helpers_and_step_models_build(references):
    served = [{'id': identifier, 'model': ref['walkthrough']['spatial_model'],
               'landmarks': [step['landmark'] for step in ref['walkthrough']['steps']]}
              for identifier, ref in references.items()]
    result = subprocess.run(['node', str(ROOT / 'tools/check_radiology_walkthrough.js')],
                            input=json.dumps(served), cwd=ROOT, capture_output=True, text=True,
                            timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report == {'investigations': 137, 'corrected': len(CORRECTED),
                      'builds': report['builds'], 'status': 'passed'}
    assert report['builds'] >= 137


def test_reviewed_source_figures_are_linked_to_bowel_steps_without_forcing_gallery_into_intro(references):
    for key, count in [('ra.ct-bowel-wall', 10), ('ra.ct-bowel-ischaemia', 8), ('ra.ct-bowel-obstruction', 10)]:
        ref = references[key]
        atlas = {r['id'] for r in ref['structure_atlas']}
        placed = {i for s in ref['walkthrough']['steps'] for i in s['images'] if i in atlas}
        assert len(placed) == count and placed == atlas
        assert not atlas.intersection(ref['walkthrough']['start']['images'])
    for key, ref in references.items():
        atlas = {r['id'] for r in ref.get('structure_atlas', [])}
        authored_start = radiology_catalog._steps()['investigations'][key].get('start', {})
        if 'images' in authored_start:
            assert ref['walkthrough']['start']['images'] == authored_start['images'], key
            assert len(atlas.intersection(authored_start['images'])) < len(atlas), key
        else:
            assert not atlas.intersection(ref['walkthrough']['start']['images']), key


def test_walkthrough_rejects_foreign_atlas_figures_and_ambiguous_collection_ids(monkeypatch, curriculum):
    key = 'ra.ct-bowel-wall'
    _mutated(monkeypatch, key, lambda e: e['steps'][0].update(images=['open-adrenal-pmc6349247-fig1']))
    with pytest.raises(ValueError, match='unknown or repeated figure'):
        radiology_catalog.detail(curriculum, radiology_catalog.resolve(key))
    monkeypatch.undo()
    ref = radiology_catalog.detail(curriculum, radiology_catalog.resolve(key))['radiology_reference']
    ref['structure_atlas'][0]['id'] = ref['key_images'][0]['id']
    with pytest.raises(ValueError, match='distinct across image collections'):
        radiology_catalog._walkthrough(radiology_catalog.resolve(key), ref)
