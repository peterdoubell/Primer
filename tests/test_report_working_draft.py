"""The whole live cohort keeps supplied facts, blank defaults and compiler parity."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from primer import report_templates
from primer.descriptor_reporting import render_descriptors
from primer.reporting_bridge import descriptor_forms
from tools.report_working_draft_compatibility import before_working_draft_bytes, PROOF

ROOT = Path(__file__).resolve().parents[1]


def test_all_335_reports_preserve_supplied_precision_and_have_no_initial_patient_facts():
    forms = descriptor_forms()['forms']
    cases = []
    for guide, form in forms.items():
        for exam in form['investigations']:
            fields = {'clinical_history': 'Synthetic history.\n\nMeasurement 6.00 × 4.50 mm < 8 mm; a & b.',
                      'comparison': '2025-03-04 (synthetic prior).',
                      'impression': '1. Retain the clinician’s “indeterminate” wording.',
                      'recommendation': '1. Retain the clinician’s supplied next step.'}
            cases.append({'guide': guide, 'id': exam['id'], 'states': [
                {'investigation_id': exam['id'], 'selections': {}},
                {'investigation_id': exam['id'], 'selections': {}, 'report_fields': fields}]})
    assert len(cases) == 335
    script = """global.window={};require('./web/radiology-structured.js');
const {forms,cases}=JSON.parse(require('fs').readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(cases.map(c=>c.states.map(state=>{
 const r=window.PrimerStructuredReporting.compose(forms[c.guide],state);
 return {text:r.text,complete:r.complete};
}))));"""
    browser = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT,
                                                input=json.dumps({'forms': forms, 'cases': cases}).encode()))
    for case, projected in zip(cases, browser):
        for index, state in enumerate(case['states']):
            saved = deepcopy(state)
            compiled = render_descriptors(forms[case['guide']], state)
            assert compiled['valid'] and state == saved, case['id']
            assert projected[index]['text'] == compiled['text'], case['id']
            if not index:
                assert compiled['text'] == '' and not projected[index]['complete'], case['id']
                continue
            for field in state['report_fields'].values():
                assert field in compiled['text'], case['id']
            headings = ['Clinical history:', 'Comparison:', 'Impression:', 'Recommendation:']
            positions = [compiled['text'].index(h) for h in headings]
            assert positions == sorted(positions), case['id']


def test_every_quick_report_variant_uses_the_approved_rich_heading_and_font_format():
    reports = []
    for identifier in report_templates.library():
        report = report_templates.quick_report(identifier)
        reports += [[report['dictation']['text'], report['dictation']['title']],
                    [report['template'], report['title']], [report['normal'], report['title']]]
    assert len(reports) == 1005
    script = """global.window={};require('./web/radiology-structured.js');
const rows=JSON.parse(require('fs').readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(rows.map(([text,title])=>{
 const h=window.PrimerStructuredReporting.reportHTML(text,title);
 return h.includes('font-family:Arial,sans-serif;font-size:12pt') && !h.includes('<strong>') &&
 ['Clinical history','Comparison','Impression','Recommendation'].every(t=>h.includes('<u>'+t+':</u>'));
})));"""
    result = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT,
                                               input=json.dumps(reports).encode()))
    assert all(result)


def test_exact_editor_inverse_preserves_the_reviewed_base_and_foreign_edits():
    for path, record in json.loads(PROOF.read_text()).items():
        raw = (ROOT / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == record['after']
        before = before_working_draft_bytes(path, raw)
        assert hashlib.sha256(before).hexdigest() == record['before']
        assert before_working_draft_bytes(path, before) == before
        assert before_working_draft_bytes(path, raw + b'\n') == raw + b'\n'
        assert before_working_draft_bytes('other', raw) == raw
