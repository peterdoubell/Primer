"""Fast report templates: one per examination, in the paste-ready RIS layout."""
import copy
import hashlib
import html
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
Lungs:
• Clear.
• [Consolidation / Collapse / Nodule / Mass / Interstitial opacity] in the []
• [Pulmonary oedema / Hyperinflation / Cavitation] []
Pleura:
• No pleural effusion or pneumothorax.
• [Small / Moderate / Large] [right / left / bilateral] pleural effusion.
• [Right / Left] pneumothorax, [] cm at the level of the hilum.
Heart and mediastinum:
• Normal heart size and mediastinal contours.
• Central trachea.
• [Cardiomegaly / Widened mediastinum / Tracheal deviation / Pneumomediastinum] []
Hila:
• Normal.
• [Hilar enlargement / Hilar lymphadenopathy / Hilar mass] on the [right / left / both sides] []
Diaphragm:
• Normal.
• No free subdiaphragmatic gas.
• [Right / Left / Bilateral] free subdiaphragmatic gas.
• [Raised hemidiaphragm / Eventration / Hiatus hernia] []
Bones and soft tissues:
• No acute bone abnormality.
• Normal soft tissues.
• [Rib fracture / Vertebral fracture / Lytic lesion / Sclerotic lesion] []
• [Subcutaneous emphysema / Soft tissue mass / Breast prosthesis] []
Lines and devices:
• None.
• [Endotracheal tube / Central venous catheter / Nasogastric tube / Pacemaker lead] tip []

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
Lungs:
• Clear.
Pleura:
• No pleural effusion or pneumothorax.
Heart and mediastinum:
• Normal heart size and mediastinal contours.
• Central trachea.
Hila:
• Normal.
Diaphragm:
• Normal.
• No free subdiaphragmatic gas.
Bones and soft tissues:
• No acute bone abnormality.
• Normal soft tissues.
Lines and devices:
• None.

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
    assert len(served_ids) == len(set(served_ids)) == 334
    assert set(served_ids) == set(rt.library())


def test_chest_radiograph_matches_the_paste_layout_exactly():
    report = rt.quick_report('ra.chest-radiography')
    assert report['template'] == CXR_TEMPLATE
    assert report['normal'] == CXR_NORMAL
    assert report['radiograph'] is True
    assert report['headings'] == ['Lungs', 'Pleura', 'Heart and mediastinum', 'Hila', 'Diaphragm', 'Bones and soft tissues',
                                  'Lines and devices']


@pytest.mark.parametrize('identifier', sorted(rt.library()))
def test_layout_rules_hold_for_every_template(identifier):
    item = rt.library()[identifier]
    report = rt.quick_report(identifier)
    template, normal = report['template'].split('\n'), report['normal'].split('\n')
    header = rt.acquisition_heading(identifier, item)
    # A heading that opens a group is preceded by the group's subheading.
    opening = item['sections'][0].get('group') or item['sections'][0]['heading']
    first = header or opening
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
        assert template[template.index('Findings:') + 1] == opening + ':'
    else:
        assert not {'Technique', 'Protocol'} & set(report['headings'])
    numbered = 'Impression:\n1. []\n2. []\n3. []\n\nRecommendation:\n1. []\n2. []\n3. []'
    assert report['template'].endswith(numbered)
    assert '[' not in '\n'.join(normal[5:])
    impression = item['impression'] if isinstance(item['impression'], list) else [item['impression']]
    assert report['normal'].endswith('Impression:\n' + '\n'.join(f'{n}. {line}' for n, line in enumerate(impression, 1))
                                     + '\n\nRecommendation:\n1. ' + item.get('recommendation', 'None.'))
    # Under each subheading every finding is a bullet: the normal sentences first, then the selectable findings.
    sections = item['sections']
    for index, section in enumerate(sections):
        start = template.index(section['heading'] + ':')
        sentences = re.split(r'(?<=\.)\s+(?=[A-Z])', section['normal'])
        options = [option.replace('[ ].', '[]').replace('[ ]', '[]') for option in section.get('options', [])]
        expected = ['\u2022 ' + line for line in [*sentences, *options]]
        assert template[start + 1:start + 1 + len(expected)] == expected
        after = template[start + 1 + len(expected)]
        # Headings follow one another without a blank line; a subheading and its headings stand apart.
        following = sections[index + 1] if index + 1 < len(sections) else None
        stacked = following is not None and following.get('group') == section.get('group')
        assert after == (following['heading'] + ':' if stacked else ''), (identifier, section['heading'], after)
    for group, members in rt._blocks(item['sections']):
        if group:
            start = template.index(group + ':')
            assert template[start + 1] == members[0]['heading'] + ':' and (start == 0 or template[start - 1] in ('', 'Findings:', item['title']))


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
        ('sections', 1, 'heading', 'Lungs', 'reserved or repeated'),
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
        ({'sections': good['sections'][:1]}, 'two to 30'),
        ({'sections': good['sections'] * 8}, 'two to 30'),
        ({'extra': True}, 'unknown'),
    ]:
        with pytest.raises(ValueError, match=message):
            rt.validate('bad', {**copy.deepcopy(good), **change})


def test_a_subheading_groups_two_or_more_adjacent_headings():
    good = copy.deepcopy(rt.library()['ra.chest-radiography'])
    def grouped(*groups):
        item = copy.deepcopy(good)
        for section, group in zip(item['sections'], groups):
            if group:
                section['group'] = group
        return item
    rt.validate('good', grouped('Chest', 'Chest', None, None))
    for groups, message in [(('Chest', None, None, None), 'two or more'), (('Chest', 'Chest', None, 'Chest'), 'split'),
                            (('Lungs', 'Lungs', None, None), 'repeated'), (('Findings', 'Findings', None, None), 'reserved'),
                            (('chest:', 'chest:', None, None), 'sentence case')]:
        with pytest.raises(ValueError, match=message):
            rt.validate('bad', grouped(*groups))
    item = grouped('Chest', 'Chest', None, None)
    text = rt.render(item)
    assert '\nChest:\nLungs:\n• Clear.' in text
    assert '\nPleura:\n• No pleural effusion or pneumothorax.' in text and '\n\nPleura:' not in text
    # The headings after the subheading's paragraph stack one under another.
    assert '\n\nHeart and mediastinum:\n' in text and '\n\nHila:' not in text and '\nCentral trachea.' not in text
    draft = rt.render_dictation(item, None)['text']
    assert '\nChest:\nLungs: []\nPleura: []\n\nHeart and mediastinum: []\nHila: []\nDiaphragm: []\n' in draft


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
    from tools.report_layout_compatibility import AFTER, BEFORE, PATH, before_report_layout_bytes, before_rich_report_format_bytes
    from tools.report_compartment_compatibility import before_rich_report_bytes
    raw = (ROOT / PATH).read_bytes()
    source = raw.decode()
    assert 'font-family:Arial,sans-serif;font-size:12pt' in source
    assert "return ['u', line, ''];" in source and "return ['em', line, ''];" in source
    raw = before_rich_report_format_bytes(PATH, raw)
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
    from tools.report_layout_compatibility import NORMAL_LINE, before_normal_line_bytes, before_rich_report_format_bytes
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
        raw = before_rich_report_format_bytes(path, (ROOT / path).read_bytes())
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
        from tools.lesson_activities_compatibility import before_activity_registry_bytes
        raw = before_reporting_step_evidence_bytes(path, before_activity_registry_bytes(path, (ROOT / path).read_bytes()))
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
            before = original[investigation['id']].get('report_protocol')
            if before is None:
                assert investigation['id'] in rt.CONFIRMED_ACQUISITIONS and acquisition['confirmed_only']
                continue
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


def test_all_dictation_templates_use_study_specific_sections_and_simple_placeholders():
    for identifier, item in rt.library().items():
        draft = rt.quick_report(identifier)['dictation']
        text = draft['text']
        assert text.startswith('Clinical history:\n[]\n\nComparison:\n[]\n\n' + draft['title'])
        assert text.endswith('\n\nImpression:\n[]\n\nRecommendation:\n[]')
        assert '[ ]' not in text and '• ' not in text
        heading = rt.acquisition_heading(identifier, item)
        if heading and 'dictation' not in item:
            assert f'\n{heading}:\n' + item['technique']['normal'] + '\n\nFindings:\n' in text
        if not heading:
            assert '\nTechnique:' not in text and '\nProtocol:' not in text
        if 'dictation' not in item:
            assert all(f"\n{section['heading']}: []" in text for section in item['sections'])
            # Headings stack one to a line; only a subheading's paragraph has a blank line around it.
            for first, second in zip(item['sections'], item['sections'][1:]):
                pair = f"{first['heading']}: []\n{second['heading']}: []"
                assert (pair in text) == (first.get('group') == second.get('group')), (identifier, pair)
            # The study name runs into its technique or its first heading.
            assert '\n' + draft['title'] + '\n' in text


def test_every_dictation_template_uses_inline_italics_without_changing_its_text():
    drafts = [rt.quick_report(identifier)['dictation'] for identifier in rt.library()]
    script = """
        const fs = require('node:fs');
        global.window = {};
        require('./web/radiology-structured.js');
        const drafts = JSON.parse(fs.readFileSync(0, 'utf8'));
        process.stdout.write(JSON.stringify(drafts.map(
          ({text, title}) => window.PrimerStructuredReporting.reportHTML(text, title)
        )));
    """
    result = subprocess.run(['node', '-e', script], cwd=ROOT, input=json.dumps(drafts),
                            text=True, capture_output=True, check=True, timeout=30)
    for draft, formatted in zip(drafts, json.loads(result.stdout), strict=True):
        assert formatted.startswith('<div style="font-family:Arial,sans-serif;font-size:12pt;')
        assert '<strong>' not in formatted
        assert f'<u>{html.escape(draft["title"], quote=False)}</u>' in formatted
        restored = re.sub(r'<[^>]+>', '', formatted.replace('<br>', '\n'))
        assert html.unescape(restored) == draft['text']
        for line in draft['text'].splitlines():
            match = re.fullmatch(r'([A-Z][^:]*:)( \[\](?: .*)?)', line)
            if match:
                heading, value = (html.escape(part, quote=False) for part in match.groups())
                assert f'<em>{heading}</em>{value}' in formatted
                assert f'<em>{heading}{value}</em>' not in formatted


def test_prostate_dictation_encodes_the_departmental_template():
    draft = rt.quick_report('ra.mri-prostate')['dictation']
    assert draft['title'] == 'mpMRI prostate'
    assert '\nTechnique:\nDepartmental 1.5 T' in draft['text']
    assert 'PSA density [] ng/mL²' in draft['text']
    assert 'Location (PI-RADS sector, series and image): []' in draft['text']
    assert 'T2: []\nDWI: []\nDCE: []' in draft['text']
    assert 'Lesion PI-RADS category: []' in draft['text']
    assert 'Extraprostatic extension: []' in draft['text']


def test_the_stacked_heading_layout_has_an_exact_inverse():
    from hashlib import sha256
    from tools.report_layout_compatibility import before_acquisition_conflicts_bytes, before_stacked_headings_bytes
    path = 'primer/report_templates.py'
    row = json.loads((ROOT / 'docs/report-format-parity/stacked-headings-inverse.json').read_text())[path]
    raw = (ROOT / path).read_bytes()
    assert sha256(raw).hexdigest() == row['after']
    restored = before_stacked_headings_bytes(path, raw)
    assert sha256(restored).hexdigest() == row['before']
    assert before_stacked_headings_bytes(path, restored) == restored
    assert before_stacked_headings_bytes(path, raw + b'\n') == raw + b'\n'
    assert before_stacked_headings_bytes('web/app.js', raw) == raw
    # The chain head undoes it before the acquisition-conflict link.
    assert before_acquisition_conflicts_bytes(path, raw) == before_acquisition_conflicts_bytes(path, restored)
