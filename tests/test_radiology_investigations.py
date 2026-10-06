"""Source-derived investigation boundaries and detailed visual contracts."""
from collections import Counter
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from primer.curriculum import Curriculum
from primer import radiology_catalog


@pytest.fixture(scope='module')
def curriculum():
    return Curriculum()


def test_all_reference_headings_are_backed_by_radiology_assistant():
    cat = radiology_catalog.catalogue()
    sources = json.loads((ROOT/'data/radiology/source-catalog.json').read_text())['articles']
    refs = cat['investigations']
    assert len(refs) == 137
    counts = Counter(a for item in refs for a in item['article_ids'])
    assert set(counts) == {a['id'] for a in sources}
    assert all(count == 1 for count in counts.values())
    assert {i['section'] for i in refs} == {'Abdomen', 'Breast', 'Cardiovascular', 'Chest', 'Head/Neck', 'Musculoskeletal', 'Neuroradiology', 'Pediatrics', 'More'}


def test_unsupported_reference_topics_are_removed(curriculum):
    items = radiology_catalog.index(curriculum)['modules']
    offered = {i['module_id'] for i in items}
    unsupported = [n['id'] for n in curriculum.nodes.values()
                   if n['domain'] == 'radiology' and n['id'].startswith('rad.')
                   and not n['reference_count']]
    assert len(unsupported) == 13
    assert not offered.intersection(unsupported)
    assert all(radiology_catalog.resolve(identifier) is None for identifier in unsupported)


def test_msk_filter_contains_only_source_msk_investigations(curriculum):
    items = radiology_catalog.index(curriculum)['modules']
    msk = [item for item in items if item['section']=='Musculoskeletal']
    assert len(msk) == 22
    assert {'ra.mri-shoulder','ra.ultrasound-shoulder','ra.mri-ankle','ra.mri-diabetic-foot'} <= {i['id'] for i in msk}
    assert not any(i['module_id'] in ('rad.5.prostate-mri','rad.5.coronary-ct') for i in msk)


def test_every_investigation_has_its_own_source_gallery(curriculum):
    for item in radiology_catalog.catalogue()['investigations']:
        ref = radiology_catalog.detail(curriculum, item)['radiology_reference']
        assert ref['key_images'] or ref.get('structure_atlas'), item['id']
        for figure in ref.get('structure_atlas', []):
            assert figure.get('src') and figure.get('source_url'), (item['id'], figure.get('id'))
        allowed = {a['url'].rstrip('/') for a in ref['reading']}
        assert len({i['src'] for i in ref.get('structure_atlas', [])}) == len(ref.get('structure_atlas', []))
        assert all(i['source_url'].rstrip('/') in allowed for i in ref['key_images']), item['id']
        assert len({i['src'] for i in ref['key_images']}) == len(ref['key_images'])


def test_split_investigations_do_not_inherit_the_wrong_modality_or_classification(curriculum):
    entries = radiology_catalog.catalogue()['investigations']
    defecography = next(i for i in entries if 'defecography' in i['title'].lower())
    ref = radiology_catalog.detail(curriculum, defecography)['radiology_reference']
    technique = next(s['body'] for s in ref['report_templates'][0]['sections'] if s['heading']=='TECHNIQUE AND QUALITY').lower()
    assert 'fluoroscop' in technique or 'barium' in technique
    assert 'mri' not in technique
    solid = next(i for i in entries if 'solid renal' in i['title'].lower())
    ref = radiology_catalog.detail(curriculum, solid)['radiology_reference']
    assert ref['reporting']['classification'] is None
    assert not ref['reporting'].get('criteria_table')


def test_shoulder_modalities_have_distinct_reporting_content(curriculum):
    mr = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.mri-shoulder'))
    us = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.ultrasound-shoulder'))
    assert mr['title'] == 'MRI shoulder'
    assert mr['modality'] == 'MRI' and us['modality']=='Ultrasound'
    assert mr['radiology_reference']['report_templates'] != us['radiology_reference']['report_templates']
    us_report = str(us['radiology_reference']['reporting']).lower()
    assert 'anisotrop' in us_report and 'dynamic' in us_report
    assert mr['radiology_reference']['key_images'] and us['radiology_reference']['key_images']
    for reference in (mr,us):
        allowed={a['url'].rstrip('/') for a in reference['radiology_reference']['reading']}
        assert all(i['source_url'].rstrip('/') in allowed for i in reference['radiology_reference']['key_images'])


def test_paediatric_elbow_never_inherits_the_shared_hip_model(curriculum):
    model = radiology_catalog.detail(curriculum, radiology_catalog.resolve(
        'ra.paediatric-elbow-fractures'))['radiology_reference']['spatial_model']
    assert model['family'] == 'elbow'
    assert model['scenario'] == 'radiology-reference:rad.5.elbow-mri'
    assert 'Adult elbow reference only' in model['population_note']
    assert 'ossification centres' in model['population_note']


def test_native_anatomy_manifest_has_traceable_geometry():
    import hashlib,struct
    directory=ROOT/'web/anatomy/bodyparts3d'
    m=json.loads((directory/'manifest.json').read_text())
    assert m['dataset']=='BodyParts3D 4.0' and m['license']=='CC BY 4.0'
    assert {'shoulder','elbow','hip','knee','ankle','wrist'} <= set(m['regions'])
    assert len(m['parts'])>=57
    for part in m['parts'].values():
        data=(ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(data).hexdigest()==part['sha256']
        magic,vertices,indices=struct.unpack('<III',data[:12])
        assert magic==0x44335042 and len(data)==12+vertices*24+indices*4
    shoulder=m['regions']['shoulder']
    names=' '.join(m['parts'][p['id']]['name'].lower() for p in shoulder['parts'])
    for structure in ('scapula','humerus','clavicle','supraspinatus','infraspinatus','subscapularis','teres minor'):
        assert structure in names


def test_reference_media_has_no_ai_generated_imagery(curriculum):
    # Generated photorealistic plates and scenes were removed; every picture is
    # a source figure, an original diagram or the licensed mesh viewer.
    assert not (ROOT/'data/radiology/anatomical-illustrations.json').exists()
    assert not (ROOT/'web/reference-media/shoulder-bones-illustration.png').exists()
    for item in radiology_catalog.catalogue()['investigations']:
        detail=radiology_catalog.detail(curriculum,item)
        assert 'anatomical_illustrations' not in detail['radiology_reference'], item['id']
        assert not any(media['kind']=='photograph' for media in detail['lesson_media']), item['id']
        assert not any('generated' in (image.get('attribution') or '').lower()
                       for image in detail['radiology_reference']['key_images']), item['id']
def test_msk_reporting_uses_sourced_anatomy_in_place_of_generated_bone_images(curriculum):
    ref=radiology_catalog.detail(curriculum,radiology_catalog.resolve('ra.mri-shoulder'))['radiology_reference']
    assert not ref.get('anatomical_illustrations')
    assert any(image['kind'] == 'schematic' for image in ref['structure_atlas'])


def test_open_msk_figures_are_local_fingerprinted_and_modality_scoped(curriculum):
    from PIL import Image
    for investigation in ('ra.mri-shoulder', 'ra.mri-elbow', 'ra.wrist-instability'):
        ref = radiology_catalog.detail(curriculum, radiology_catalog.resolve(investigation))['radiology_reference']
        assert ref['structure_atlas']
        for image in ref['structure_atlas']:
            assert image['license'] == 'CC BY 4.0'
            assert image['structures_visible'] and image['limits']
            path = ROOT / 'web' / image['src'].removeprefix('/app/')
            assert Image.open(path).size == (image['width'], image['height'])
        if investigation == 'ra.wrist-instability':
            assert 'MRI' in ref['structure_atlas'][0]['limits']


def test_wrist_fracture_reference_reuses_exact_anatomy_without_claiming_mri_was_performed(curriculum):
    instability = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.wrist-instability'))
    fractures = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.wrist-fractures'))
    assert fractures['radiology_reference']['structure_atlas'] == instability['radiology_reference']['structure_atlas']
    assert fractures['radiology_reference']['structure_atlas'] is not instability['radiology_reference']['structure_atlas']
    assert fractures['modality'] != 'MRI'
    authored = json.loads((ROOT / 'data/radiology/investigation-overrides.json').read_text())['ra.wrist-fractures']['reporting']
    assert fractures['radiology_reference']['reporting'] == authored


def test_diabetic_foot_uses_whole_pedal_source_without_rewriting_the_broad_lesson(curriculum):
    import copy
    broad = curriculum.node('rad.5.marrow-muscle')['radiology_reference']
    ankle = curriculum.node('rad.5.ankle-foot')['radiology_reference']
    broad_before, ankle_before = copy.deepcopy(broad), copy.deepcopy(ankle)
    reference = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.mri-diabetic-foot'))['radiology_reference']
    model = reference['spatial_model']
    assert model['family'] == 'foot'
    assert model['scenario'] == 'radiology-reference:rad.5.ankle-foot'
    assert model['source_view'] == 'whole-foot'
    assert model['source_atlas'] == 'z-anatomy'
    assert 'Adult right-foot reference only' in model['population_note']
    assert 'plantar-plate' in model['population_note'] and 'clinical fidelity review remain outstanding' in model['population_note']
    override = json.loads((ROOT/'data/radiology/investigation-overrides.json').read_text())['ra.mri-diabetic-foot']
    assert reference['reporting'] == override['reporting']
    assert reference['report_templates'] == override['report_templates']
    assert broad == broad_before and ankle == ankle_before
    assert broad['spatial_model']['family'] == 'longbone'
    ankle_investigation = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.mri-ankle'))['radiology_reference']['spatial_model']
    assert ankle_investigation['family'] == 'ankle'
    assert 'source_view' not in ankle_investigation


def test_ultrasound_shoulder_shares_only_its_selected_modalities(curriculum):
    ref = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.ultrasound-shoulder'))['radiology_reference']
    figures = ref['structure_atlas']
    assert [image['id'] for image in figures] == [
        'open-shoulder-rotator-interval-ultrasound-xue-fig1b',
        'open-shoulder-rotator-interval-kadi-supp-fig6',
        'open-shoulder-cuff-footprints-perez-fig2',
    ]
    assert [image['modality'] for image in figures] == ['Ultrasound', 'Schematic', 'Schematic']
    assert 'anisotrop' in str(ref['reporting']).lower()
    assert 'dynamic' in str(ref['reporting']).lower()
    mri = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.mri-shoulder'))['radiology_reference']
    authored = {image['id']: image for image in mri['structure_atlas']}
    assert all(image == authored[image['id']] for image in figures)
    assert ref['report_templates'] != mri['report_templates']


@pytest.mark.parametrize('selection', [
    {'source': 'ra.mri-shoulder', 'include_ids': []},
    {'source': 'ra.mri-shoulder', 'include_ids': ['unknown']},
    {'source': 'ra.mri-shoulder', 'include_ids': ['open-shoulder-cuff-footprints-perez-fig2'] * 2},
    {'source': 'ra.mri-knee', 'include_ids': ['open-knee-anterior-meniscal-roots-fig10']},
])
def test_selected_atlas_sharing_rejects_empty_unknown_duplicate_or_cross_region_sources(monkeypatch, selection):
    import copy
    original = radiology_catalog._read
    def changed(name, default=None):
        data = copy.deepcopy(original(name, default))
        if name == 'msk-atlas-sharing.json':
            data['ra.ultrasound-shoulder'] = selection
        return data
    monkeypatch.setattr(radiology_catalog, '_read', changed)
    radiology_catalog._structure_atlases.cache_clear()
    try:
        with pytest.raises(ValueError, match='Shared MSK'):
            radiology_catalog._structure_atlases()
    finally:
        radiology_catalog._structure_atlases.cache_clear()


def test_selected_ultrasound_anatomy_has_only_ultrasound_clinical_evidence_bindings():
    records = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']
    asset = next(a for a in records if a['id'] == 'open-shoulder-rotator-interval-ultrasound-xue-fig1b')
    assert asset['modality'] == 'Ultrasound'
    assert asset['investigation_ids'] == ['ra.ultrasound-shoulder']
    assert asset['source_context']['selected_panels'] == ['b']
    assert asset['source_context']['panel_types']['b'] == 'Ultrasound'
    assert not any('dynamic' in target or 'footprint' in target for target in asset['structure_ids'])
    assert asset['anatomical_review']['status'] == 'pending'


def test_hip_originals_keep_their_source_license_version(curriculum):
    ref = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.hip-fai'))['radiology_reference']
    aubry = [image for image in ref['structure_atlas'] if 'aubry' in image['id']]
    assert len(aubry) == 3
    assert all(image['license'] == 'CC BY 2.0' and
               image['license_url'] == 'https://creativecommons.org/licenses/by/2.0/' for image in aubry)


@pytest.mark.parametrize('change', [
    {'source_bytes_sha256': '0' * 64},
    {'source_bytes_md5': '0' * 32},
    {'license_url': 'https://creativecommons.org/licenses/by/4.0/'},
    {'license_use_plan': {'mode': 'adapted_figure', 'preserve_original_bytes': False}},
])
def test_nd_figures_cannot_silently_be_relicensed_or_adapted(monkeypatch, change):
    import copy
    original = radiology_catalog._read
    def changed(name, default=None):
        data = copy.deepcopy(original(name, default))
        if name == 'msk-open-images.json':
            image = next(item for item in data['ra.mri-knee']
                         if item['id'] == 'open-knee-lateral-posterior-root-mri-wang2018-fig6')
            image.update(change)
        return data
    monkeypatch.setattr(radiology_catalog, '_read', changed)
    radiology_catalog._structure_atlases.cache_clear()
    try:
        with pytest.raises(ValueError, match='ND reference|commercial-use license'):
            radiology_catalog._structure_atlases()
    finally:
        radiology_catalog._structure_atlases.cache_clear()


def test_joint_injection_uses_regional_anatomy_instead_of_generic_vascular_access(curriculum):
    item = next(x for x in radiology_catalog.catalogue()['investigations'] if x['id']=='ra.ultrasound-joint-injection')
    ref = radiology_catalog.detail(curriculum,item)['radiology_reference']
    models = ref['spatial_model_options']
    assert [m['family'] for m in models] == ['shoulder','elbow','hand','hip','knee','ankle']
    assert ref['spatial_model']['scenario'] == models[0]['scenario']
    assert ref['spatial_model']['family'] == 'shoulder'
    assert all('No needle' in m['population_note'] for m in models)
    assert all('unverified' in m['population_note'] for m in models)
    assert curriculum.node('rad.5.ir-basics')['radiology_reference']['spatial_model']['family']=='access'


def test_hamstring_model_uses_whole_source_muscle_framing(curriculum):
    item = next(x for x in radiology_catalog.catalogue()['investigations'] if x['id']=='ra.mri-hamstring')
    model = radiology_catalog.detail(curriculum,item)['radiology_reference']['spatial_model']
    assert model['source_view']=='hamstrings'
    assert model['source_atlas']=='z-anatomy'
    assert model['family']=='knee'
    assert 'tendon volumes' in model['population_note']


def test_arthritis_regions_include_whole_foot_without_claiming_bilateral_survey(curriculum):
    item=next(x for x in radiology_catalog.catalogue()['investigations'] if x['id']=='ra.arthritis')
    ref=radiology_catalog.detail(curriculum,item)['radiology_reference']
    models=ref['spatial_model_options']
    assert [m['family'] for m in models]==['hand','foot','knee','hip','cervical']
    assert models[1]['source_view']=='whole-foot'
    assert models[-1]['source_atlas']=='cervical-bones'
    assert 'do not constitute a bilateral arthritis survey' in ref['regional_reference_note']
    assert 'atlantoaxial' in ref['regional_reference_note']


@pytest.mark.parametrize('identifier',['ra.mri-muscle-injury','ra.mri-muscle-disease'])
def test_muscle_modules_use_uncropped_source_muscle_groups(curriculum,identifier):
    item=next(x for x in radiology_catalog.catalogue()['investigations'] if x['id']==identifier)
    ref=radiology_catalog.detail(curriculum,item)['radiology_reference']
    models=ref['spatial_model_options']
    assert len(models)==6
    assert all(m['initial_layer']=='muscle' and m['initial_cropped'] is False for m in models)
    assert all(m['family']!='longbone' for m in models)
    assert all('not a complete inventory' in m['population_note'] for m in models)
    assert 'Enumerate every actually covered muscle' in ref['regional_reference_note']


@pytest.mark.parametrize('mutation', ['empty','not_list','missing_note','nontext_note','unknown_mode','conflicting_frame'])
def test_regional_source_configuration_rejects_ambiguous_anatomy(curriculum,monkeypatch,mutation):
    import copy
    original=radiology_catalog._read
    def changed(name,default=None):
        data=copy.deepcopy(original(name,default))
        if name=='investigation-model-bindings.json':
            target=data['ra.mri-muscle-injury']
            if mutation=='empty':target['regional_references']=[]
            elif mutation=='not_list':target['regional_references']='shoulder'
            else:
                entry=target['regional_references'][0]
                if mutation=='missing_note':entry.pop('population_note')
                if mutation=='nontext_note':entry['population_note']=['unverified']
                if mutation=='unknown_mode':entry['display_mode']='full-anatomy'
                if mutation=='conflicting_frame':entry['source_view']='whole-foot'
        return data
    monkeypatch.setattr(radiology_catalog,'_read',changed)
    item=next(x for x in radiology_catalog.catalogue()['investigations'] if x['id']=='ra.mri-muscle-injury')
    with pytest.raises(ValueError,match='Regional'):
        radiology_catalog.detail(curriculum,item)
