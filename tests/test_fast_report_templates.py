"""Fast report templates: one per examination, in the paste-ready RIS layout."""
import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from primer import report_templates as rt
from tools.fast_report_templates_compatibility import CHANGES, before_fast_templates_bytes

ROOT = Path(__file__).resolve().parents[1]

CXR_TEMPLATE = """Clinical history:
[ ].

Chest radiographs, PA and lateral / Chest radiograph, AP
Airways and cardiomediastinum:
Trachea central. Normal heart size, mediastinal contours and hila.
[Cardiomegaly / Widened mediastinum / Hilar enlargement / Tracheal deviation] [ ].

Lungs:
Clear lungs.
[Consolidation / Collapse / Nodule / Mass / Interstitial opacity] in the [ ].
[Pulmonary oedema / Hyperinflation / Cavitation] [ ].

Pleura and diaphragm:
No pleural effusion or pneumothorax. Normal diaphragm.
[Small / Moderate / Large] [right / left / bilateral] pleural effusion.
[Right / Left] pneumothorax, [ ] cm at the level of the hilum.
[Right / Left / Bilateral] free subdiaphragmatic gas.

Devices and bones:
No lines or devices. No acute bony abnormality.
[Endotracheal tube / Central venous catheter / Nasogastric tube / Pacemaker lead] tip [ ].
[Rib fracture / Vertebral fracture / Lytic lesion / Sclerotic lesion] [ ].

Impression:
1. []
2. []
3. []

Recommendation:
[ ]."""

CXR_NORMAL = """Clinical history:
[ ].

Chest radiographs, PA and lateral / Chest radiograph, AP
Airways and cardiomediastinum:
Trachea central. Normal heart size, mediastinal contours and hila.

Lungs:
Clear lungs.

Pleura and diaphragm:
No pleural effusion or pneumothorax. Normal diaphragm.

Devices and bones:
No lines or devices. No acute bony abnormality.

Impression:
1. Normal chest radiograph.

Recommendation:
None."""


@pytest.fixture(scope='module')
def curriculum():
    from primer.curriculum import Curriculum
    return Curriculum()


@pytest.fixture(scope='module')
def served_ids(curriculum):
    from primer.radiology_catalog import index
    from primer.reporting_bridge import with_descriptor_investigations
    return [module['id'] for module in with_descriptor_investigations(index(curriculum))['modules']]


def test_every_served_examination_has_exactly_one_template(served_ids):
    assert len(served_ids) == len(set(served_ids)) == 333
    assert set(served_ids) == set(rt.library())


def test_chest_radiograph_matches_the_paste_layout_exactly():
    report = rt.quick_report('ra.chest-radiography')
    assert report['template'] == CXR_TEMPLATE
    assert report['normal'] == CXR_NORMAL
    assert report['radiograph'] is True
    assert report['headings'] == ['Airways and cardiomediastinum', 'Lungs', 'Pleura and diaphragm', 'Devices and bones']


@pytest.mark.parametrize('identifier', sorted(rt.library()))
def test_layout_rules_hold_for_every_template(identifier):
    item = rt.library()[identifier]
    report = rt.quick_report(identifier)
    template, normal = report['template'].split('\n'), report['normal'].split('\n')
    for lines in (template, normal):
        assert lines[:4] == ['Clinical history:', '[ ].', '', item['title']]
        assert '' not in (lines[4], lines[5]) and lines[4].endswith(':')
        headings = [line[:-1] for line in lines if line.endswith(':')]
        assert headings == ['Clinical history', *report['headings'], 'Impression', 'Recommendation']
        assert all(lines[index + 1] for index, line in enumerate(lines) if line.endswith(':'))
        assert '\n\n\n' not in '\n'.join(lines) and lines[-1].strip()
    # Radiographs have no technique or comparison; every other examination opens with both.
    if item['radiograph']:
        assert 'Technique' not in report['headings'] and 'Comparison' not in report['headings']
    else:
        assert report['headings'][:2] == ['Technique', 'Comparison']
        assert template[template.index('Technique:') + 1] == item['technique']['normal']
        assert 'Limited by [ ].' in template and 'Limited by [ ].' not in normal
    assert report['template'].endswith('Impression:\n1. []\n2. []\n3. []\n\nRecommendation:\n[ ].')
    # The normal report is ready to sign once the history is written: no picks or blanks.
    assert '[' not in '\n'.join(normal[2:]) and ']' not in '\n'.join(normal[2:])
    impression = item['impression'] if isinstance(item['impression'], list) else [item['impression']]
    assert report['normal'].endswith('Impression:\n' + '\n'.join(f'{n}. {line}' for n, line in enumerate(impression, 1))
                                     + '\n\nRecommendation:\n' + item.get('recommendation', 'None.'))
    # Each heading's normal line comes first, then its selectable findings.
    for section in item['sections']:
        start = template.index(section['heading'] + ':')
        assert template[start + 1:start + 2 + len(section.get('options', []))] == [section['normal'], *section.get('options', [])]


def test_radiograph_titles_and_flags_agree():
    for identifier, item in rt.library().items():
        titles = item['title'].split(' / ')
        radiographic = [any(word in title.lower() for word in ('radiograph', 'mammograph', 'skeletal survey')) for title in titles]
        if item['radiograph']:
            assert all(radiographic), identifier
        else:
            # Male breast imaging pairs mammography with ultrasound, so it keeps a technique.
            assert not all(radiographic) or identifier == 'ra.male-breast', identifier
        if identifier.startswith('xr.'):
            assert item['radiograph'], identifier


def test_malformed_templates_are_refused():
    good = copy.deepcopy(rt.library()['ra.chest-radiography'])
    rt.validate('good', good)
    cases = [
        ('sections', 0, 'normal', 'Clear [lungs / lung].', 'normal line'),
        ('sections', 0, 'options', ['[Nested [ ] pick / other].'], 'nested'),
        ('sections', 0, 'options', ['[Only one choice] here.'], 'pick'),
        ('sections', 0, 'options', ['[Unclosed / pick.'], 'paired'),
        ('sections', 0, 'options', ['No full stop'], 'full stop'),
        ('sections', 0, 'heading', 'LUNGS AND PLEURA', 'sentence case'),
        ('sections', 0, 'heading', 'Lungs:', 'sentence case'),
        ('sections', 0, 'heading', 'Impression', 'reserved'),
        ('sections', 1, 'heading', 'Airways and cardiomediastinum', 'reserved or repeated'),
    ]
    for key, index, field, value, message in cases:
        bad = copy.deepcopy(good)
        bad[key][index][field] = value
        with pytest.raises(ValueError, match=message):
            rt.validate('bad', bad)
    for change, message in [
        ({'technique': {'normal': 'CT chest.'}}, 'radiographs have no technique'),
        ({'radiograph': False}, 'every other examination has one'),
        ({'title': 'Chest radiograph:'}, 'study title'),
        ({'title': 'Chest [PA / AP]'}, 'study title'),
        ({'impression': 'Normal [chest / lungs].'}, 'normal line'),
        ({'impression': []}, 'impression'),
        ({'sections': good['sections'][:1]}, 'two to twelve'),
        ({'extra': True}, 'unknown'),
    ]:
        with pytest.raises(ValueError, match=message):
            rt.validate('bad', {**copy.deepcopy(good), **change})


def test_library_files_are_schema_tagged_and_ids_unique(tmp_path, monkeypatch):
    seen = {}
    for path in sorted(rt.LIBRARY.glob('*.json')):
        data = json.loads(path.read_text())
        assert data['schema'] == rt.SCHEMA
        for identifier in data['templates']:
            assert identifier not in seen, (identifier, seen.get(identifier), path.name)
            seen[identifier] = path.name
    first = sorted(rt.LIBRARY.glob('*.json'))[0]
    data = json.loads(first.read_text())
    (tmp_path / 'a.json').write_text(json.dumps(data))
    (tmp_path / 'b.json').write_text(json.dumps(data))
    monkeypatch.setattr(rt, 'LIBRARY', tmp_path)
    rt.library.cache_clear()
    try:
        with pytest.raises(ValueError, match='defined twice'):
            rt.library()
    finally:
        monkeypatch.undo()
        rt.library.cache_clear()


def test_module_responses_carry_the_template_and_normal_report(curriculum, tmp_path, monkeypatch):
    monkeypatch.setenv('PRIMER_DB', str(tmp_path / 'reporting.db'))
    from fastapi.testclient import TestClient
    import primer.server as server
    monkeypatch.setattr(server, 'curr', curriculum)
    client = TestClient(server.app)
    try:
        for identifier, expected in [('ra.chest-radiography', 'ra.chest-radiography'), ('rad.5.prostate-mri', 'ra.mri-prostate'),
                                     ('xr.knee', 'xr.knee'), ('template:pet-ct-report', 'template:pet-ct-report')]:
            body = client.get('/api/radiology/modules/' + identifier).json()
            report = body['radiology_reference']['quick_report']
            assert report == rt.quick_report(expected)
            assert body['radiology_reference'].get('structured_form') is not None
        assert client.get('/api/radiology/modules/rad.missing').status_code == 404
        assert 'quick_report' not in client.get('/api/radiology/modules').text
    finally:
        client.close()


def test_responses_without_a_template_are_unchanged():
    detail = {'id': 'not-a-template', 'radiology_reference': {'reporting': {}}}
    assert rt.with_quick_report(detail) is detail
    assert rt.with_quick_report({'id': 'ra.chest-radiography'}) == {'id': 'ra.chest-radiography'}
    original = {'id': 'ra.chest-radiography', 'radiology_reference': {'reporting': {}}}
    attached = rt.with_quick_report(original)
    assert 'quick_report' not in original['radiology_reference'] and attached['radiology_reference']['quick_report']


@pytest.mark.parametrize('path', sorted(CHANGES))
def test_shared_file_inverse_restores_the_previous_bytes_exactly(path):
    raw = (ROOT / path).read_bytes()
    restored = before_fast_templates_bytes(path, raw)
    assert hashlib.sha256(raw).hexdigest() == CHANGES[path]['after']
    assert hashlib.sha256(restored).hexdigest() == CHANGES[path]['before']
    assert before_fast_templates_bytes(path, restored) == restored
    assert before_fast_templates_bytes(path, raw + b'\n') == raw + b'\n'
    assert before_fast_templates_bytes('web/styles.css', raw) == raw
    from tools.source_studies_compatibility import before_source_studies_bytes
    assert hashlib.sha256(before_source_studies_bytes(path, raw)).hexdigest() != CHANGES[path]['after']


def test_reader_renders_both_texts_above_the_click_builder():
    source = (ROOT / 'web/app.js').read_text()
    assert source.count('renderQuickReport(ref.quick_report, n.id)') == 2
    assert "...(ref.quick_report || ref.structured_form?.descriptor_form" in source
    check = subprocess.run(['node', '--check', str(ROOT / 'web/app.js')], capture_output=True, text=True)
    assert check.returncode == 0, check.stderr
