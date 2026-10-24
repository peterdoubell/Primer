"""Bindings preserve observation provenance and isolate repeated lesions."""
import copy
import json
from pathlib import Path

import pytest

from primer.descriptor_calculations import descriptor_calculation_jobs
from primer.descriptor_reporting import render_descriptors
from tools.build_descriptor_reporting import compile_statement
from tools.descriptor_calculation_binding_compiler import attach_calculation_bindings

ROOT = Path(__file__).resolve().parents[1]


def authored_form(identifier):
    path = ROOT / 'data/radiology' / ('anatomic-neuro.json' if identifier == 'ra.ultrasound-thyroid' else 'anatomic-body.json')
    authored = json.loads(path.read_text())['investigations'][identifier]
    rows = []
    for raw in authored['sections']:
        section = {key: copy.deepcopy(value) for key, value in raw.items() if key != 'findings'}
        section.update(id='anatomy-' + raw['id'], anatomy_id=raw['id'])
        section['normal'] = compile_statement(raw['normal'], kind='normal', label='Normal', source={}) if raw['normal'] else None
        findings = []
        for item in raw['findings']:
            finding = compile_statement(item['text'], kind='finding', label=item['label'], source={})
            finding['id'] = identifier + ':' + raw['id'] + ':' + item['id']
            if item.get('requires_any'):
                finding['requires_any'] = [identifier + ':' + raw['id'] + ':' + parent for parent in item['requires_any']]
            if item.get('exclusive_group'):
                finding['exclusive_group'] = item['exclusive_group']
            if item.get('report') is False:
                finding['report'] = False
            findings.append(finding)
        section['findings'] = findings
        rows.append(section)
    form = {'guide_id': authored['guide_id'], 'calculator_ids': ['acr_tirads_2017', 'pirads_v2_1', 'prostate_volume_psad'],
            'investigations': [{'id': identifier, 'sections': rows}]}
    bindings = json.loads((ROOT / 'data/radiology/descriptor-calculation-bindings.json').read_text())
    attach_calculation_bindings({form['guide_id']: form}, {'investigations': {identifier: bindings['investigations'][identifier]}})
    return form


def selected(identifier, section, values):
    return {'findings': {identifier + ':' + section + ':' + key: value for key, value in values.items()}}


def prostate_lesion(t2='3', dwi='3', dce='negative', zone='peripheral zone'):
    return selected('ra.mri-prostate', 'prostate-lesion', {
        'lesion': {'slot-1': 'right', 'slot-2': 'mid gland', 'slot-3': 'anterior'},
        'zone': {'slot-1': zone}, 'treatment': {'slot-1': 'treatment-naive prostate'},
        't2-adequate': {}, 'dwi-adequate': {}, 't2-score': {'slot-1': t2},
        'dwi-score': {'slot-1': dwi}, 'dce': {'slot-1': dce},
    })


def thyroid_nodule(composition='solid or almost completely solid', foci='punctate echogenic foci only'):
    return selected('ra.ultrasound-thyroid', 'thyroid-nodule', {
        'nodule': {'slot-1': 'right upper pole'},
        'composition': {'slot-1': composition}, 'echogenicity': {'slot-1': 'hypoechoic'},
        'shape': {'slot-1': 'wider-than-tall'}, 'margin': {'slot-1': 'smooth'},
        'echogenic-foci': {'slot-1': foci},
        'dimensions': {'slot-1': 11, 'slot-2': 17, 'slot-3': 13},
    })


def test_repeat_inputs_never_leak_between_prostate_lesions():
    form = authored_form('ra.mri-prostate')
    state = {'investigation_id': 'ra.mri-prostate', 'selections': {
        'anatomy-prostate-lesion': {'instances': [prostate_lesion(dce='positive'), prostate_lesion(dwi='2')]}}}
    original = copy.deepcopy(state)
    assert render_descriptors(form, state)['valid']
    jobs = descriptor_calculation_jobs(form, state)
    assert state == original
    assert [j['inputs']['dwi_score'] for j in jobs] == [3, 2]
    assert [j['context_label'] for j in jobs] == ['Lesion 1', 'Lesion 2']
    assert [j['instance_index'] for j in jobs] == [0, 1]
    assert len({j['binding_id'] for j in jobs}) == 2
    # Deleting a finding removes that input rather than borrowing another lesion's value.
    del state['selections']['anatomy-prostate-lesion']['instances'][1]['findings']['ra.mri-prostate:prostate-lesion:dwi-score']
    assert 'dwi_score' not in descriptor_calculation_jobs(form, state)[1]['inputs']


def test_global_applicability_and_additive_foci_are_explicit():
    form = authored_form('ra.ultrasound-thyroid')
    state = {'investigation_id': 'ra.ultrasound-thyroid', 'selections': {
        'anatomy-thyroid-nodule': {'instances': [thyroid_nodule(foci='macrocalcification and peripheral rim calcification and punctate echogenic foci')]}}}
    job = descriptor_calculation_jobs(form, state)[0]
    assert 'adult_applicability_confirmed' not in job['inputs']
    assert job['inputs']['echogenic_foci'] == ['macrocalcifications', 'peripheral_rim', 'punctate']
    assert job['inputs']['size_mm'] == 17
    state['selections']['anatomy-patient-group'] = selected('ra.ultrasound-thyroid', 'patient-group', {'child': {}})
    job = descriptor_calculation_jobs(form, state)[0]
    assert job['not_applicable'] and job['inputs']['adult_applicability_confirmed'] is False
    state['selections']['anatomy-patient-group'] = selected('ra.ultrasound-thyroid', 'patient-group', {'adult': {}})
    assert descriptor_calculation_jobs(form, state)[0]['inputs']['adult_applicability_confirmed'] is True


def test_partial_dimensions_are_not_used_as_the_largest_dimension():
    form = authored_form('ra.ultrasound-thyroid')
    record = thyroid_nodule()
    record['findings']['ra.ultrasound-thyroid:thyroid-nodule:dimensions'].pop('slot-2')
    state = {'investigation_id': 'ra.ultrasound-thyroid', 'selections': {'anatomy-thyroid-nodule': {'instances': [record]}}}
    assert not render_descriptors(form, state)['valid']
    assert 'size_mm' not in descriptor_calculation_jobs(form, state)[0]['inputs']


def test_conflicting_explicit_sources_are_not_guessed():
    form = authored_form('ra.mri-prostate')
    record = prostate_lesion()
    record['findings']['ra.mri-prostate:prostate-lesion:t2-inadequate'] = {}
    state = {'investigation_id': 'ra.mri-prostate', 'selections': {'anatomy-prostate-lesion': {'instances': [record]}}}
    assert not render_descriptors(form, state)['valid']
    job = descriptor_calculation_jobs(form, state)[0]
    assert 't2_adequate' not in job['inputs']
    assert {'code': 'conflicting_calculation_inputs', 'input': 't2_adequate'} in job['input_issues']


def test_zone_outside_pz_tz_is_not_automatically_classified():
    form = authored_form('ra.mri-prostate')
    state = {'investigation_id': 'ra.mri-prostate', 'selections': {'anatomy-prostate-lesion': {'instances': [prostate_lesion(zone='central zone')]}}}
    job = descriptor_calculation_jobs(form, state)[0]
    assert job['not_applicable'] and job['inputs']['zone'] == 'CZ'


def test_volume_units_and_optional_psa_do_not_infer_missing_lab_values():
    form = authored_form('ra.mri-prostate')
    state = {'investigation_id': 'ra.mri-prostate', 'selections': {'anatomy-prostate-dimensions': selected(
        'ra.mri-prostate', 'prostate-dimensions', {'dimensions': {'slot-1': 40, 'slot-2': 30, 'slot-3': 50}})}}
    job = descriptor_calculation_jobs(form, state)[0]
    assert job['inputs'] == {'transverse_cm': 4.0, 'ap_cm': 3.0, 'longitudinal_cm': 5.0}
    assert job['instance_index'] is None
    state['selections']['anatomy-prostate-dimensions']['findings']['ra.mri-prostate:prostate-dimensions:psa'] = {'slot-1': 0}
    assert descriptor_calculation_jobs(form, state)[0]['inputs']['psa_ng_ml'] == 0


def test_unbound_archived_forms_and_unanswered_rows_have_no_jobs():
    form = {'investigations': [{'id': 'old', 'sections': [{'id': 's', 'label': 'Old source', 'findings': []}]}]}
    assert descriptor_calculation_jobs(form, {'investigation_id': 'old'}) == []
    assert descriptor_calculation_jobs(authored_form('ra.mri-prostate'), {'investigation_id': 'ra.mri-prostate'}) == []


@pytest.mark.parametrize('record', [{'not_assessed': True}, {'normal': True}])
def test_normal_or_unassessed_records_cannot_activate_a_job(record):
    assert descriptor_calculation_jobs(authored_form('ra.mri-prostate'), {
        'investigation_id': 'ra.mri-prostate', 'selections': {'anatomy-prostate-lesion': record}}) == []
