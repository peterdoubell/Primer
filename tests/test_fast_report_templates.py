"""Fast report templates: one per examination, in the paste-ready RIS layout."""
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

from primer import report_templates as rt
from tools.fast_report_templates_compatibility import CHANGES, before_fast_templates_bytes

ROOT = Path(__file__).resolve().parents[1]

CXR_TEMPLATE = """Clinical history:
[]

Comparison:
[]

Chest radiographs, PA and lateral / Chest radiograph, AP
Airways and cardiomediastinum:
• Trachea central.
• Normal heart size, mediastinal contours and hila.
• [Cardiomegaly / Widened mediastinum / Hilar enlargement / Tracheal deviation] []

Lungs:
• Clear.
• [Consolidation / Collapse / Nodule / Mass / Interstitial opacity] in the []
• [Pulmonary oedema / Hyperinflation / Cavitation] []

Pleura and diaphragm:
• No pleural effusion or pneumothorax.
• Normal diaphragm.
• [Small / Moderate / Large] [right / left / bilateral] pleural effusion.
• [Right / Left] pneumothorax, [] cm at the level of the hilum.
• [Right / Left / Bilateral] free subdiaphragmatic gas.

Devices and bones:
• No lines or devices.
• No acute bony abnormality.
• [Endotracheal tube / Central venous catheter / Nasogastric tube / Pacemaker lead] tip []
• [Rib fracture / Vertebral fracture / Lytic lesion / Sclerotic lesion] []

Impression:
1. []
2. []
3. []

Recommendation:
1. []
2. []
3. []"""

CXR_NORMAL = """Clinical history:
[]

Comparison:
[]

Chest radiographs, PA and lateral / Chest radiograph, AP
Airways and cardiomediastinum:
• Trachea central.
• Normal heart size, mediastinal contours and hila.

Lungs:
• Clear.

Pleura and diaphragm:
• No pleural effusion or pneumothorax.
• Normal diaphragm.

Devices and bones:
• No lines or devices.
• No acute bony abnormality.

Impression:
1. Normal chest radiograph.

Recommendation:
1. None."""


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
    header = rt.acquisition_heading(identifier, item)
    first = header or item['sections'][0]['heading']
    for lines in (template, normal):
        # The study name runs straight into its first heading.
        assert lines[:8] == ['Clinical history:', '[]', '', 'Comparison:', '[]', '', item['title'], first + ':']
        headings = [line[:-1] for line in lines if line.endswith(':')]
        assert headings == ['Clinical history', 'Comparison', *report['headings'], 'Impression', 'Recommendation']
        assert '\n\n\n' not in '\n'.join(lines) and lines[-1].strip()
        assert '[ ]' not in '\n'.join(lines)
    # MRI opens with its Protocol and CT with its Technique, then Findings; nothing else has either.
    if header:
        assert report['headings'][:2] == [header, 'Findings']
        start = template.index(header + ':')
        assert template[start + 1] == item['technique']['normal']
        assert 'Limited by []' in template and 'Limited by []' not in normal
        # Findings runs straight into the first anatomical subheading.
        assert template[template.index('Findings:') + 1] == item['sections'][0]['heading'] + ':'
    else:
        assert not {'Technique', 'Protocol'} & set(report['headings'])
    numbered = 'Impression:\n1. []\n2. []\n3. []\n\nRecommendation:\n1. []\n2. []\n3. []'
    assert report['template'].endswith(numbered)
    assert '[' not in '\n'.join(normal[5:])
    impression = item['impression'] if isinstance(item['impression'], list) else [item['impression']]
    assert report['normal'].endswith('Impression:\n' + '\n'.join(f'{n}. {line}' for n, line in enumerate(impression, 1))
                                     + '\n\nRecommendation:\n1. ' + item.get('recommendation', 'None.'))
    # Under each subheading every finding is a bullet: the normal sentences first, then the selectable findings.
    for section in item['sections']:
        start = template.index(section['heading'] + ':')
        sentences = re.split(r'(?<=\.)\s+(?=[A-Z])', section['normal'])
        options = [option.replace('[ ].', '[]').replace('[ ]', '[]') for option in section.get('options', [])]
        expected = ['\u2022 ' + line for line in [*sentences, *options]]
        assert template[start + 1:start + 1 + len(expected)] == expected
        assert template[start + 1 + len(expected):start + 2 + len(expected)] in ([''], [])


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
    from tools.source_studies_compatibility import before_combined_source_release_bytes

    current = (ROOT / path).read_bytes()
    raw = before_combined_source_release_bytes(path, current)
    assert before_combined_source_release_bytes(path, current + b'\n') == current + b'\n'
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


def test_formatted_copy_is_arial_12_with_underlined_headings_and_an_exact_inverse():
    from tools.report_layout_compatibility import AFTER, BEFORE, PATH, before_report_layout_bytes
    from tools.report_compartment_compatibility import before_rich_report_bytes
    raw = (ROOT / PATH).read_bytes()
    source = raw.decode()
    assert 'font-family:Arial,sans-serif;font-size:12pt' in source
    assert "case 'main': return '<u>' + content + '</u>';" in source and "case 'subheading': return '<em>'" in source
    assert '(Clinical history|Comparison|Protocol|Technique|Findings|Impression|Recommendation)' in source
    from tools.report_layout_compatibility import NORMAL_LINE, before_normal_line_bytes
    assert hashlib.sha256(raw).hexdigest() == NORMAL_LINE[PATH][1]
    raw = before_normal_line_bytes(PATH, raw)
    assert hashlib.sha256(raw).hexdigest() == AFTER
    restored = before_report_layout_bytes(PATH, raw)
    assert hashlib.sha256(restored).hexdigest() == BEFORE
    assert before_report_layout_bytes(PATH, restored) == restored
    assert before_report_layout_bytes(PATH, raw + b'\n') == raw + b'\n'
    assert before_report_layout_bytes('web/app.js', raw) == raw
    assert hashlib.sha256(before_rich_report_bytes(PATH, raw)).hexdigest() not in (AFTER, BEFORE)


def test_a_checklist_normal_reads_as_label_colon_normal_with_an_exact_inverse():
    from primer.descriptor_reporting import normal_line
    from tools.report_layout_compatibility import NORMAL_LINE, before_normal_line_bytes
    assert normal_line('Supraspinatus tendon', 'The supraspinatus tendon is intact.') == 'Supraspinatus tendon: normal.'
    assert normal_line('Right pleura', 'No right pleural effusion, pneumothorax or pleural nodularity.') == 'Right pleura: normal.'
    # A heading that names a finding cannot be "normal".
    assert normal_line('Fracture', 'No fracture.') == 'Fracture: none.'
    assert normal_line('Hernia at the site of concern', 'No hernia at the site of concern is seen.') == 'Hernia at the site of concern: none.'
    assert normal_line('Haematoma', 'No collection.') == 'Haematoma: none.'
    assert normal_line('Gallbladder', 'No gallbladder calculi.') == 'Gallbladder: normal.'
    assert normal_line('Thyroid nodule', 'No thyroid nodules are identified.') == 'Thyroid nodule: none.'
    assert normal_line('Anterior Horn', 'No tear.', 'Medial meniscus') == 'Medial meniscus, anterior horn: normal.'
    assert normal_line('Supraspinatus', 'Intact.', 'Rotator cuff · tendons') == 'Supraspinatus tendon: normal.'
    assert normal_line('Supraspinatus', 'Normal bulk.', 'Rotator cuff · muscles') == 'Supraspinatus muscle: normal.'
    for path, (before, after, _) in NORMAL_LINE.items():
        raw = (ROOT / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == after
        assert hashlib.sha256(before_normal_line_bytes(path, raw)).hexdigest() == before
        assert before_normal_line_bytes(path, raw + b'\n') == raw + b'\n'


def test_the_on_screen_report_draft_matches_the_copied_text_with_an_exact_inverse():
    from tools.report_layout_compatibility import PREVIEW, PREVIEW_PATH, before_preview_match_bytes
    from tools.report_layout_compatibility import before_template_editor_bytes
    raw = before_template_editor_bytes(PREVIEW_PATH, (ROOT / PREVIEW_PATH).read_bytes())
    assert b'.rad-report-main-heading { font-weight: 400; }' in raw
    assert b'.rad-report-text { font: 12pt/1.4 Arial, sans-serif !important; }' in raw
    assert hashlib.sha256(raw).hexdigest() == PREVIEW[1]
    assert hashlib.sha256(before_preview_match_bytes(PREVIEW_PATH, raw)).hexdigest() == PREVIEW[0]
    assert before_preview_match_bytes(PREVIEW_PATH, raw + b'\n') == raw + b'\n'


def test_the_report_template_tab_is_a_rich_text_editor_with_an_exact_inverse():
    from tools.report_layout_compatibility import TEMPLATE_EDITOR, before_template_editor_bytes
    from tools.source_studies_compatibility import before_reporting_step_evidence_bytes
    source = (ROOT / 'web/app.js').read_text()
    assert "contenteditable: 'true', role: 'textbox'" in source and "el('textarea', { id: uid, class: 'rad-report-editor'" not in source
    # Formatting is limited to bold, italic and underline; pasted and dropped content is plain text.
    assert "format('bold', 'B', 'Bold'), format('italic', 'I', 'Italic'), format('underline', 'U', 'Underline')" in source
    assert "document.execCommand('insertText', false, (event.clipboardData || window.clipboardData).getData('text/plain'))" in source
    assert "editor.addEventListener('drop', event => event.preventDefault());" in source
    # The copy carries the formatting shown and a plain-text alternative.
    assert "'text/html': new Blob([html], { type: 'text/html' })" in source and "'text/plain': new Blob([text], { type: 'text/plain' })" in source
    assert set(TEMPLATE_EDITOR) == {'web/app.js', 'web/radiology-structured.css'}
    for path, (before, after, _) in TEMPLATE_EDITOR.items():
        raw = before_reporting_step_evidence_bytes(path, (ROOT / path).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == after
        assert hashlib.sha256(before_template_editor_bytes(path, raw)).hexdigest() == before
        assert before_template_editor_bytes(path, raw + b'\n') == raw + b'\n'
    from tools.source_studies_compatibility import before_combined_source_release_bytes
    reader = (ROOT / 'web/app.js').read_bytes()
    assert hashlib.sha256(before_combined_source_release_bytes('web/app.js', reader)).hexdigest() not in (
        TEMPLATE_EDITOR['web/app.js'][0], TEMPLATE_EDITOR['web/app.js'][1])


def test_the_click_builder_default_acquisition_is_the_template_protocol_with_an_exact_inverse():
    import gzip
    from primer.descriptor_reporting import render_descriptors
    from primer.reporting_bridge import descriptor_forms
    from tools.report_compartment_compatibility import before_compartments_bytes
    from tools.report_layout_compatibility import PROTOCOL_ALIGNMENT, PROTOCOL_ALIGNMENT_PATH, before_protocol_alignment_bytes
    packed = ROOT / 'data/radiology/descriptor-reporting.json.gz'
    stored = json.loads(gzip.decompress(packed.read_bytes()) if packed.exists()
                        else (ROOT / 'data/radiology/descriptor-reporting.json').read_text())
    original = {inv['id']: inv for form in stored['forms'].values() for inv in form['investigations']}
    library, aligned = rt.library(), 0
    for form in descriptor_forms()['forms'].values():
        for investigation in form['investigations']:
            acquisition = investigation.get('report_protocol')
            if not acquisition:
                continue
            before = original[investigation['id']]['report_protocol']
            # Only the default text changes; the selectable choices stay as authored.
            assert {k: v for k, v in acquisition.items() if k != 'standard_text'} == {
                k: v for k, v in before.items() if k != 'standard_text'}, investigation['id']
            item = library.get(investigation['id'])
            if item and rt.acquisition_heading(investigation['id'], item):
                assert acquisition['standard_text'] == item['technique']['normal'], investigation['id']
                aligned += 1
            else:
                assert acquisition['standard_text'] == before['standard_text'], investigation['id']
    assert aligned >= 140
    form = next(f for f in descriptor_forms()['forms'].values() if any(i['id'] == 'ra.mri-knee' for i in f['investigations']))
    knee = next(i for i in form['investigations'] if i['id'] == 'ra.mri-knee')
    section = next(s for s in knee['sections'] if s.get('normal'))
    report = render_descriptors(form, {'investigation_id': 'ra.mri-knee', 'selections': {section['id']: {'normal': True}}})
    assert report['valid'] and library['ra.mri-knee']['technique']['normal'] in report['text']
    raw = (ROOT / PROTOCOL_ALIGNMENT_PATH).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PROTOCOL_ALIGNMENT[1]
    assert hashlib.sha256(before_protocol_alignment_bytes(PROTOCOL_ALIGNMENT_PATH, raw)).hexdigest() == PROTOCOL_ALIGNMENT[0]
    assert before_protocol_alignment_bytes(PROTOCOL_ALIGNMENT_PATH, raw + b'\n') == raw + b'\n'
    assert hashlib.sha256(before_compartments_bytes(PROTOCOL_ALIGNMENT_PATH, raw, allow_older=True)).hexdigest() == PROTOCOL_ALIGNMENT[0]
