"""Descriptor-only anatomy is audited without turning findings or partial sources into meshes."""
from copy import deepcopy
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from tools import audit_structure_coverage as coverage
from tools.check_msk_fidelity import audit, KINDS
from tools.anatomy_sources import build_soft_tissue_neck_inventory as neck

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def inventory():
    return neck.validate(neck.read(neck.OUTPUT))


@pytest.fixture(scope='module')
def live():
    return coverage.live_coverage()


def test_every_actual_report_section_field_and_dependency_has_its_exact_trace(inventory):
    authored, compiled = neck.report_sources()
    assert inventory == neck.build()
    assert [row['id'] for row in inventory['sections']] == neck.EXPECTED_SECTIONS
    assert len(inventory['sections']) == 9
    assert inventory['source_report']['compiled_investigation_sha256'] == neck.digest(compiled)
    assert inventory['source_report']['author_investigation_sha256'] == neck.digest(authored)
    records = inventory['evidence_requirements']
    for section, actual in zip(authored['sections'], compiled['sections']):
        expected = {field['id'] for field in section['findings']} | ({'normal'} if section.get('normal') else set())
        traced = [record for record in records if record['source_section_id'] == section['id'] and 'source_field_id' in record]
        assert {row['source_field_id'] for row in traced} == expected
        for row in traced:
            field = actual['normal'] if row['source_field_id'] == 'normal' else next(f for f in actual['findings'] if f['id'] == row['report_provenance']['compiled_field_id'])
            assert row['report_provenance']['compiled_field_sha256'] == neck.digest(field)
            assert row['requires_any'] == field.get('requires_any', [])
            assert row['guidance'][0]['source_id'] == neck.GUIDANCE
            assert row['required_representations'] == []
    assert inventory['sources'][1]['doi'] == '10.1002/jum.16251'
    assert {row['section_ids'][0] for row in inventory['report_guidance_gaps']} >= {'parotid-glands', 'thyroid-gland', 'right-neck-nodes', 'vessels'}


def test_ordinary_landmarks_have_explicit_sides_and_one_isthmus(inventory):
    targets = inventory['anatomical_requirements']
    assert len(targets) == 15 and len({row['id'] for row in targets}) == 15
    assert Counter(row['laterality'] for row in targets) == {'right': 7, 'left': 7, 'not_applicable': 1}
    assert next(row for row in targets if row['laterality'] == 'not_applicable')['name'] == 'thyroid isthmus'
    assert all(row['required_representations'] == list(KINDS) for row in targets)
    assert not any('sublingual' in row['name'] or 'parathyroid' in row['name'] or 'sternocleidomastoid' in row['name'] for row in targets)
    assert all('acquisition_condition' in row for row in targets if row['tissue_class'] == 'salivary_duct')
    scopes = [row for row in inventory['evidence_requirements'] if row['requirement_type'] == 'assessment_scope']
    assert len(scopes) == 2 and all(row['source_level_choices'] == ['I', 'II', 'III', 'IV', 'V', 'VI'] for row in scopes)
    assert not any('level' in row['id'] for row in targets)


def test_measurements_flow_classification_and_current_findings_are_separate(inventory):
    assert inventory['counts'] == {'anatomical_requirements': 15, 'representation_obligations': 45,
        'typed_evidence_records': 39, 'evidence_records_by_type': {'assessment_scope': 2, 'classification': 1,
        'current_exam_assessment': 7, 'current_finding': 16, 'examination_scope': 1,
        'flow_assessment': 5, 'interpretation': 1, 'measurement': 6}}
    records = inventory['evidence_requirements']
    area = next(row for row in records if row['id'] == 'neck_us.area-of-concern.size')
    assert area['measurement'] == {'unit': 'mm', 'number_of_values': 3, 'axis_definition': 'three_dimensions'}
    assert area['requires_any'] == ['us.soft-tissue-neck:area-of-concern:lesion']
    nodes = [row for row in records if row['requirement_type'] == 'measurement' and 'neck-nodes' in row['id']]
    assert len(nodes) == 2 and all(row['measurement']['axis_definition'] == 'short_axis' for row in nodes)
    conditional = [row for row in records if row['requirement_type'] == 'flow_assessment' and 'applies_when' in row]
    assert len(conditional) == 3
    assert {row['applies_when']['selected_value'] for row in conditional} == {'hypervascular', 'peripheral vascularity'}
    assert all('actual_patient_flow_sensitive_acquisition' in row['required_evidence'] for row in records if row['requirement_type'] == 'flow_assessment')
    assert all(row['clinical_approval'] is row['representation_completion_claim'] is False for row in records)


def test_source_contexts_are_unbound_and_the_photos_never_gain_sides(inventory):
    contexts = inventory['source_contexts']
    assert {row['source_id'] for row in contexts} == {'segthy-001', 'salivary-us-2025'}
    assert all(row['requirement_ids'] == [] and row['coverage_granted'] is False for row in contexts)
    photos = next(row for row in contexts if row['source_id'] == 'salivary-us-2025')
    assert photos['side'] == photos['plane'] == 'not_reported' and photos['panels'] == ['A', 'B']
    assert inventory['clinical_approval'] is inventory['structure_coverage_granted'] is inventory['representation_completion_claim'] is False


@pytest.mark.parametrize('change', ['section', 'isthmus', 'invented_side', 'measurement_mesh', 'source_binding', 'flow_gate', 'approval'])
def test_unreviewed_semantics_do_not_pass_the_current_inventory_validator(inventory, change):
    bad = deepcopy(inventory)
    if change == 'section': bad['sections'].pop()
    elif change == 'isthmus': next(row for row in bad['anatomical_requirements'] if row['id'] == 'neck_us.thyroid_isthmus.not_applicable')['laterality'] = 'left'
    elif change == 'invented_side': bad['source_contexts'][1]['side'] = 'left'
    elif change == 'measurement_mesh': next(row for row in bad['evidence_requirements'] if row['requirement_type'] == 'measurement')['required_representations'] = ['model']
    elif change == 'source_binding': bad['source_contexts'][1]['requirement_ids'] = [bad['anatomical_requirements'][0]['id']]
    elif change == 'flow_gate': next(row for row in bad['evidence_requirements'] if 'applies_when' in row)['applies_when']['selected_value'] = 'all findings'
    else: bad['clinical_approval'] = True
    with pytest.raises(ValueError, match='exact report'):
        neck.validate(bad)


def test_live_denominator_is_the_real_app_index_and_neck_has_three_distinct_denominators(live):
    from primer.server import app
    with TestClient(app) as client:
        index = client.get('/api/radiology/modules').json()
        response = client.get('/api/radiology/modules/' + neck.CASE).json()
    assert index['count'] == live['investigations'] == 335
    assert {row['id'] for row in index['modules']} == {row['investigation_id'] for row in live['rows']}
    assert live['report_sections'] == 7070
    assert (live['with_dedicated_inventory'], live['without_dedicated_inventory']) == (137, 198)
    assert (live['legacy_inventory_investigations'], live['typed_descriptor_investigations']) == (136, 1)
    row = next(row for row in live['rows'] if row['investigation_id'] == neck.CASE)
    assert row['report_sections'] == 9 and row['inventory']['typed_evidence_records'] == 39
    for kind in KINDS:
        assert row['representations'][kind] == {'required': 15, 'verified': 0, 'unverified': 0, 'missing': 15,
            'explicitly_bound': 0, 'with_partial_candidates': 0, 'complete_set': False}
    actual, = [item for item in response['radiology_reference']['structured_form']['descriptor_form']['investigations'] if item['id'] == neck.CASE]
    assert [section['anatomy_id'] for section in actual['sections']] == neck.EXPECTED_SECTIONS
    sections = {section['anatomy_id']: section for section in actual['sections']}
    for record in neck.read(neck.OUTPUT)['evidence_requirements']:
        if 'source_field_id' not in record:
            continue
        section = sections[record['source_section_id']]
        field = section['normal'] if record['source_field_id'] == 'normal' else next(field for field in section['findings'] if field['id'] == record['report_provenance']['compiled_field_id'])
        assert neck.digest(field) == record['report_provenance']['compiled_field_sha256']
    assert response['radiology_reference']['quick_report']['normal'].count('• Normal.') == 3
    assert {'segthy-001', 'salivary-us-2025'} <= {row['id'] for row in response['radiology_reference']['source_native_inspectors']}


def test_live_known_representation_counts_conserve_leaves_and_unknown_studies_stay_unknown(live):
    assert live['known_representation_obligations'] == 152631
    assert live['total_representation_obligations'] is None
    for kind in KINDS:
        total = live['representations'][kind]
        assert total['required'] == 50877
        assert total['required'] == total['verified'] + total['unverified'] + total['missing']
        assert total['explicitly_bound'] == total['verified'] + total['unverified']
        assert total['with_partial_candidates'] <= total['explicitly_bound']
        assert sum(row['representations'][kind]['required'] or 0 for row in live['rows']) == total['required']
    unknown = [row for row in live['rows'] if row['inventory_status'] == 'no_dedicated_inventory']
    assert len(unknown) == 198
    assert all(row['representations'][kind]['required'] is None and not row['representations'][kind]['complete_set'] for row in unknown for kind in KINDS)
    assert all(not row['clinical_completion_claim'] for row in live['rows'])


def test_two_partial_sources_cannot_be_summed_into_complete_sets(inventory):
    adapted = coverage.descriptor_anatomical_inventory(inventory)
    assets = []
    for target in inventory['anatomical_requirements']:
        for suffix in ['a', 'b']:
            assets.append({'id': target['id'] + suffix, 'kind': 'model', 'investigation_ids': [neck.CASE],
                'structure_ids': [target['id']], 'requirement_coverage': {target['id']: {'extent': 'partial', 'basis': 'Only local source tissue is depicted.'}}})
    result = audit(adapted, {'assets': assets})
    counts = coverage.representation_counts(result['requirements'], 'model')
    assert counts['required'] == counts['explicitly_bound'] == counts['with_partial_candidates'] == 15
    assert counts['verified'] == 0 and counts['unverified'] == 15 and counts['missing'] == 0
    assert counts['complete_set'] is False and result['clinical_commercial_ready'] is False


def test_original_literal_counter_is_an_exact_projection_of_the_live_audit(live):
    original = coverage.coverage()
    assert len(original) == 136
    actual = {row['investigation_id']: row['legacy_literal_binding_counts'] for row in live['rows'] if row['legacy_literal_binding_counts'] is not None}
    assert [actual[row['investigation_id']] for row in original] == original
    run = subprocess.run([sys.executable, str(ROOT / 'tools/audit_structure_coverage.py'), '--legacy-json'], capture_output=True, text=True, check=True)
    assert json.loads(run.stdout) == {'investigations': 136, 'required': sum(row['required'] for row in original),
        'bound': sum(row['bound'] for row in original), 'rows': original}


def test_default_cli_uses_the_live_index_instead_of_the_preserved_legacy_counter(live):
    run = subprocess.run([sys.executable, str(ROOT / 'tools/audit_structure_coverage.py'), '--json'], capture_output=True, text=True, check=True)
    assert json.loads(run.stdout) == live
