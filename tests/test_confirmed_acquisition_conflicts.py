"""Explicit acquisition claims must agree with declared performed method/phase."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from primer.descriptor_reporting import render_descriptors
from primer.report_templates import CONFIRMED_ACQUISITION_CONFLICTS, library
from primer.reporting_bridge import descriptor_forms

ROOT = Path(__file__).resolve().parents[1]


def profile(identifier):
    form = next(row for row in descriptor_forms()['forms'].values()
                if any(exam['id'] == identifier for exam in row['investigations']))
    exam = next(exam for exam in form['investigations'] if exam['id'] == identifier)
    return form, exam


CASES = [(identifier, value) for identifier, scope in CONFIRMED_ACQUISITION_CONFLICTS.items()
         for value in scope['values']]


@pytest.mark.parametrize('identifier,value', CASES)
@pytest.mark.parametrize('confirmation', ['option', 'verbatim'])
def test_conflicts_and_recovery_preserve_saved_observations(identifier, value, confirmation):
    form, exam = profile(identifier)
    scope = exam['report_protocol']['incompatible_scopes'][0]
    sentence = library()[identifier]['technique']['normal']
    selected = {scope['section_id']: {'findings': {
        scope['finding_id']: {scope['slot_id']: value}}}}
    normal = next(row for row in exam['sections'] if row['normal'] and row['id'] != scope['section_id'])
    selected[normal['id']] = {'normal': True}
    fields = {'clinical_history': 'Fixture history.'}
    fields.update({'protocol_options': [sentence]} if confirmation == 'option' else {'protocol': sentence})

    # Both interaction orders serialize to the same saved state.
    state = {'investigation_id': identifier, 'selections': selected, 'report_fields': fields}
    saved = json.loads(json.dumps(state))
    result = render_descriptors(form, saved)
    assert saved == state
    assert result['valid'] is False and result['text'] == ''
    issue, = [row for row in result['issues'] if row['code'] == 'conflicting_report_protocol']
    assert issue['section_id'] == scope['section_id']
    assert issue['finding_id'] == scope['finding_id']
    assert issue['slot_id'] == scope['slot_id']
    assert value in issue['label'] and 'unconfirm' in issue['label']
    assert any(row['section_id'] == (normal.get('report_section_id') or normal['id']) for row in result['sections'])

    unconfirmed = deepcopy(saved)
    unconfirmed['report_fields'] = {'clinical_history': 'Fixture history.'}
    report = render_descriptors(form, unconfirmed)
    assert report['valid'] and sentence not in report['text']
    assert value in report['text'] and 'Fixture history.' in report['text']

    cleared_method = deepcopy(saved)
    del cleared_method['selections'][scope['section_id']]
    report = render_descriptors(form, cleared_method)
    assert report['valid'] and sentence in report['text']
    assert 'Fixture history.' in report['text']
    assert normal['label'] + ': normal.' in report['text'] or normal['label'] + ': none.' in report['text']

    section = next(row for row in exam['sections'] if row['id'] == scope['section_id'])
    finding = next(row for row in section['findings'] if row['id'] == scope['finding_id'])
    slot = next(row for row in finding['slots'] if row['id'] == scope['slot_id'])
    compatible = next(row['value'] for row in slot['options'] if row['value'] not in scope['values'])
    changed_method = deepcopy(saved)
    changed_method['selections'][scope['section_id']]['findings'][scope['finding_id']][scope['slot_id']] = compatible
    assert render_descriptors(form, changed_method)['valid']

    states = [saved, unconfirmed, cleared_method, changed_method]
    script = """global.window={}; require('./web/radiology-structured.js');
const [form,states]=JSON.parse(require('fs').readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(states.map(state=>window.PrimerStructuredReporting.compose(form,state))));"""
    browser = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT,
                                                input=json.dumps([form, states]).encode()))
    assert browser[0]['complete'] is False and browser[0]['text'] == ''
    browser_issue, = [row for row in browser[0]['missing'] if row.get('code') == 'conflicting_report_protocol']
    assert browser_issue['label'] == issue['label']
    for state, composed in zip(states[1:], browser[1:]):
        assert composed['complete']
        assert composed['text'] == render_descriptors(form, state)['text']


def test_an_unassessed_method_and_unconfirmed_free_text_do_not_claim_a_conflicting_acquisition():
    for identifier, scope in CONFIRMED_ACQUISITION_CONFLICTS.items():
        form, exam = profile(identifier)
        option = exam['report_protocol']['options'][0]
        state = {'investigation_id': identifier, 'selections': {
            scope['section_id']: {'not_assessed': True}},
            'report_fields': {'protocol_options': [option]}}
        assert render_descriptors(form, state)['valid']
        state['selections'][scope['section_id']] = {'findings': {
            scope['finding_id']: {scope['slot_id']: scope['values'][0]}}}
        state['report_fields'] = {'protocol': 'Reader-supplied acquisition details.'}
        assert render_descriptors(form, state)['valid']


def test_conflict_inverse_restores_the_reviewed_acquisition_layer():
    from hashlib import sha256
    from tools.report_layout_compatibility import (
        CONFIRMED_GROUP_AFTER, PATH, before_acquisition_conflicts_bytes,
        before_confirmed_acquisition_group_bytes, before_performed_acquisition_bytes, before_stacked_headings_bytes,
    )
    from tools.acute_abdomen_panels_compatibility import before_acute_panel_bytes
    folder = ROOT / 'docs/report-format-parity'
    proof = json.loads((folder / 'acquisition-conflicts-inverse.json').read_text())
    performed = json.loads((folder / 'performed-acquisition-inverse.json').read_text())
    for path, row in proof.items():
        # Compare the acquisition-layer bytes after undoing both later, independently pinned changes.
        current = before_acute_panel_bytes(path, (ROOT / path).read_bytes())
        raw = before_stacked_headings_bytes(path, current)
        assert sha256(raw).hexdigest() == row['after']
        assert sha256(before_acquisition_conflicts_bytes(path, raw)).hexdigest() == row['before']
        assert before_acquisition_conflicts_bytes(path, raw + b'\n') == raw + b'\n'
    raw = (ROOT / PATH).read_bytes()
    assert sha256(before_acquisition_conflicts_bytes(PATH, raw)).hexdigest() == CONFIRMED_GROUP_AFTER
    assert sha256(before_confirmed_acquisition_group_bytes(PATH, raw)).hexdigest() == performed[PATH]['after']
    assert sha256(before_performed_acquisition_bytes(PATH, raw)).hexdigest() == performed[PATH]['before']
