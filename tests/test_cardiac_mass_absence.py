"""A dedicated cardiac mass report can explicitly record absence without a lesion.

The real authored report is compiled in memory for these focused regressions;
this does not write a catalogue or create an archive of unshipped content.
"""
import copy
import json
from pathlib import Path

import pytest

from primer.descriptor_reporting import render_descriptors
from tools.build_descriptor_reporting import compile_statement, digest, slug
from tools.msk_descriptor_catalog import apply_anatomic_reports

ROOT = Path(__file__).resolve().parents[1]
EXAM = 'ra.cardiac-masses'
ABSENCE = 'No intracardiac or pericardial mass is identified on the acquired images.'
MASS_STRUCTURES = ('left-ventricle', 'right-ventricle', 'left-atrium', 'right-atrium',
                   'valve-aortic', 'valve-mitral', 'valve-tricuspid', 'valve-pulmonary')


@pytest.fixture
def report(tmp_path):
    source = json.loads((ROOT / 'data/radiology/anatomic-cardiorespiratory.json').read_text())
    definition = source['investigations'][EXAM]
    source['investigations'] = {EXAM: definition}
    source['coverage'] = [row for row in source['coverage'] if row['investigation_id'] == EXAM]
    directory = tmp_path / 'data/radiology'
    directory.mkdir(parents=True)
    (directory / 'anatomic-cardiorespiratory.json').write_text(json.dumps(source))
    forms = {definition['guide_id']: {'sources': [], 'provenance': {}, 'investigations': [{'id': EXAM}]}}
    apply_anatomic_reports(forms, tmp_path, compile_statement, digest, slug)
    form = forms[definition['guide_id']]
    return form, {row['anatomy_id']: row for row in form['investigations'][0]['sections']}


def render(form, selections):
    return render_descriptors(form, {'investigation_id': EXAM, 'selections': selections})


def values(finding):
    return {slot['id']: slot['options'][0]['value'] if slot['kind'] == 'choice' else 1
            for slot in finding['slots']}


def test_explicit_absence_is_available_without_inventing_a_lesion_or_other_normal_findings(report):
    form, rows = report
    assert render(form, {})['text'] == ''
    parent = rows['cardiac-lesion']
    assert parent['repeatable'] and parent['normal']['text'] == ABSENCE
    result = render(form, {parent['id']: {'normal': True}})
    assert result['valid'] and result['selected_finding_count'] == 0
    assert result['text'] == 'LESION CHARACTERISATION\n' + ABSENCE
    assert 'Lesion 1' not in result['text']
    assert 'enhancement' not in result['text']
    assert 'function' not in result['text']


def test_parent_absence_cannot_coexist_with_a_positive_repeated_cardiac_lesion(report):
    form, rows = report
    parent = rows['cardiac-lesion']
    lesion = next(item for item in parent['findings'] if item['id'].endswith(':present'))
    selection = {'instances': [{'findings': {lesion['id']: values(lesion)}}]}
    positive = render(form, {parent['id']: selection})
    assert positive['valid'] and ABSENCE not in positive['text']
    conflicting = copy.deepcopy(selection)
    conflicting['normal'] = True
    result = render(form, {parent['id']: conflicting})
    assert not result['valid'] and result['text'] == ''
    assert 'invalid_repeat_instances' in {issue['code'] for issue in result['issues']}


@pytest.mark.parametrize('structure', MASS_STRUCTURES)
def test_each_chamber_or_valve_mass_invalidates_the_overall_negative(report, structure):
    form, rows = report
    parent = rows['cardiac-lesion']
    section = rows[structure]
    mass = next(item for item in section['findings'] if item['id'].endswith(':mass'))
    assert parent['id'] in mass['invalidates_normal']
    positive = {section['id']: {'findings': {mass['id']: values(mass)}}}
    assert render(form, positive)['valid']
    result = render(form, {**positive, parent['id']: {'normal': True}})
    assert not result['valid'] and result['text'] == ''
    assert 'conflicting_anatomic_normal' in {issue['code'] for issue in result['issues']}
