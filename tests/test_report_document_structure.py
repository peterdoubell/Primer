"""Study headings, protocol confirmation and browser/server parity."""
import gzip
import json
import subprocess
from pathlib import Path

import pytest

from primer.descriptor_reporting import render_descriptors

ROOT = Path(__file__).resolve().parents[1]
with gzip.open(ROOT / 'data/radiology/descriptor-reporting.json.gz', 'rt') as source:
    CATALOG = json.load(source)
EXAMS = {exam['id']: (form, exam) for form in CATALOG['forms'].values()
         for exam in form['investigations']}


@pytest.mark.parametrize('identifier,header', [
    ('ra.mri-knee', 'Protocol'), ('ct.liver-mass', 'Technique'),
    ('xr.hand', None), ('us.venous-duplex-lower-limb', None),
])
def test_report_document_order_and_browser_parity(identifier, header):
    form, exam = EXAMS[identifier]
    fields = {'clinical_history': 'Clinical question', 'comparison': 'No prior available.',
              'impression': 'Reviewed impression.', 'recommendation': 'Discuss with the referring team.'}
    if header:
        fields['protocol_options'] = [exam['report_protocol']['options'][0]]
    state = {'investigation_id': identifier, 'report_fields': fields}
    text = render_descriptors(form, state)['text']
    titles = ['Clinical history:', 'Comparison:', exam['title']]
    if header:
        titles += [header + ':', 'Findings:']
        assert exam['title'] + '\n' + header + ':\n' + fields['protocol_options'][0] in text
    else:
        assert '\nTechnique:' not in text and '\nProtocol:' not in text
    titles += ['Impression:', 'Recommendation:']
    assert sorted(titles, key=text.index) == titles
    script = """global.window={}; require('./web/radiology-structured.js');
    const [form,state]=JSON.parse(require('fs').readFileSync(0,'utf8'));
    process.stdout.write(window.PrimerStructuredReporting.compose(form,state).text);"""
    actual = subprocess.check_output(['node', '-e', script], cwd=ROOT, input=json.dumps([form, state]).encode()).decode()
    assert actual == text


def test_protocol_omission_and_unlisted_choices_are_explicit():
    form, exam = EXAMS['ra.mri-knee']
    state = {'investigation_id': exam['id'], 'report_fields': {'clinical_history': 'Pain'}}
    assert 'Protocol:\n' + exam['report_protocol']['standard_text'] in render_descriptors(form, state)['text']
    state['report_fields']['protocol'] = ''
    assert 'Protocol:\n[]' in render_descriptors(form, state)['text']
    state['report_fields']['protocol_options'] = ['Unknown sequence']
    assert not render_descriptors(form, state)['valid']
    form, exam = EXAMS['xr.hand']
    assert not render_descriptors(form, {'investigation_id': exam['id'], 'report_fields': {'protocol': 'Invalid section'}})['valid']


def test_standard_acquisition_exists_for_each_mri_and_ct():
    for form, exam in EXAMS.values():
        if exam['modality'] in ('MRI', 'CT'):
            protocol = exam['report_protocol']['standard_text']
            assert protocol, exam['id']
            state = {'investigation_id': exam['id'], 'report_fields': {'clinical_history': 'Clinical question'}}
            report = render_descriptors(form, state)['text']
            heading = 'Protocol' if exam['modality'] == 'MRI' else 'Technique'
            assert exam['title'] + '\n' + heading + ':\n' + protocol + '\n\nFindings:' in report, exam['id']
        else:
            assert not exam.get('report_protocol'), exam['id']


@pytest.mark.parametrize('identifier', [
    'ra.biliary-duct-pathology',
    'ra.pancreatic-cysts',
])
def test_multimodality_protocol_only_appears_after_confirmation(identifier):
    from copy import deepcopy
    from primer.report_templates import align_builder_protocols, library
    from primer.reporting_bridge import descriptor_forms

    stored_form, stored_exam = EXAMS[identifier]
    served_form = descriptor_forms()['forms'][stored_form['guide_id']]
    served = next(exam for exam in served_form['investigations'] if exam['id'] == identifier)
    option = library()[identifier]['technique']['normal']
    assert served['modality'] == 'Multimodality'
    assert served['sections'] == stored_exam['sections']
    assert served['report_protocol']['options'] == [option]
    assert served['report_protocol']['standard_text'] == ''
    assert served['report_protocol']['heading'] == 'Protocol'
    catalogue = {'forms': {stored_form['guide_id']: deepcopy(served_form)}}
    assert align_builder_protocols(catalogue)['forms'][stored_form['guide_id']] == served_form
    for exam in served_form['investigations']:
        if exam['modality'] == 'Ultrasound':
            assert 'report_protocol' not in exam

    section = next(row for row in served['sections'] if row['normal'])
    observations = {section['id']: {'normal': True}}
    generic = {'investigation_id': identifier, 'selections': observations}
    baseline = render_descriptors(stored_form, generic)
    explicit = dict(generic, report_fields={'protocol_options': [option]})
    blank = dict(generic, report_fields={'protocol_options': [], 'protocol': '  '})
    typed = dict(generic, report_fields={'protocol': 'Reader-confirmed MRCP details.'})
    empty = {'investigation_id': identifier, 'report_fields': {'protocol': ''}}
    forged = dict(generic, report_fields={'protocol_options': ['Unauthored MRCP option']})

    def text(state):
        result = render_descriptors(served_form, state)
        assert result['valid'], result
        return result['text']

    assert text(generic) == text(blank) == baseline['text']
    assert text(empty) == ''
    confirmed = text(explicit)
    assert served['title'] + f'\nProtocol:\n{option}\n\nFindings:\n' in confirmed
    assert confirmed.count(option) == 1
    assert '\nProtocol:\nReader-confirmed MRCP details.\n\nFindings:\n' in text(typed)
    assert option not in text(typed)
    assert not render_descriptors(served_form, forged)['valid']

    script = """global.window={}; require('./web/radiology-structured.js');
    const [form,states]=JSON.parse(require('fs').readFileSync(0,'utf8'));
    process.stdout.write(JSON.stringify(states.map(state => window.PrimerStructuredReporting.compose(form,state).text)));"""
    states = [generic, explicit, blank, typed, empty]
    output = subprocess.check_output(['node', '-e', script], cwd=ROOT,
                                     input=json.dumps([served_form, states]).encode())
    assert json.loads(output) == [text(state) for state in states]


def test_performed_acquisition_composes_with_both_exact_layout_inverses():
    from hashlib import sha256
    from tools.report_layout_compatibility import (
        NORMAL_LINE, before_click_builder_spacing_bytes, before_performed_acquisition_bytes,
        before_rich_report_format_bytes,
    )

    folder = ROOT / 'docs' / 'report-format-parity'
    sources = json.loads((folder / 'performed-acquisition-inverse.json').read_text())
    spacing = json.loads((folder / 'acquisition-spacing-inverse.json').read_text())
    for path, proof in sources.items():
        raw = (ROOT / path).read_bytes()
        assert sha256(raw).hexdigest() == proof['after']
        assert sha256(before_performed_acquisition_bytes(path, raw)).hexdigest() == proof['before'] == spacing[path]['after']
        assert sha256(before_click_builder_spacing_bytes(path, raw)).hexdigest() == spacing[path]['before']
        assert sha256(before_rich_report_format_bytes(path, raw)).hexdigest() == NORMAL_LINE[path][1]
        assert before_performed_acquisition_bytes(path, raw + b'\n') == raw + b'\n'
