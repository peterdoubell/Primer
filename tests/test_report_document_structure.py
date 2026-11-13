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
        assert fields['protocol_options'][0] in text
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
    assert 'Protocol:\n—' in render_descriptors(form, state)['text']
    state['report_fields']['protocol_options'] = ['Unknown sequence']
    assert not render_descriptors(form, state)['valid']
    form, exam = EXAMS['xr.hand']
    assert not render_descriptors(form, {'investigation_id': exam['id'], 'report_fields': {'protocol': 'Invalid section'}})['valid']
