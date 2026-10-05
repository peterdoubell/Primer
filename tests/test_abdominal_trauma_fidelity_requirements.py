"""Trauma geometry and interpretation require actual phases, interfaces and organ scales."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    item = next(r for r in data['investigations'] if r['investigation_id'] == 'ra.ct-abdominal-trauma')
    return {**data, 'investigations': [item], 'scope': {'catalog_investigation_ids': [item['investigation_id']]}}, item


def test_full_source_scope_matches_reader_and_leaves_all_new_bindings_missing():
    data, item = inventory()
    ref = detail(Curriculum(), resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data, {item['investigation_id']: ref['reporting']})
    assert item['source_contract_sha256'] == digest({k: ref.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')})
    leaves = {r['id']: r for r in requirements_for(item)}
    assert len(leaves) == 690
    for suffix in ['liver_segment_IVb.biliary_interface_if_resolved', 'right_kidney.calyces_if_opacified', 'left_kidney.renal_arterial_branches', 'pancreas_neck.duct_if_resolved', 'vascular_injury.venous_phase_same_site_if_acquired', 'space_lesser_sac.source_boundaries', 'bowel_duodenum_fourth.antimesenteric_border', 'collecting_injury.unresolved_duct_or_leak_endpoint', 'bladder.actual_retrograde_fill_source', 'left_diaphragm.crus', 'bone_right_innominate.adjacent_vascular_or_organ_interface', 'trajectory.unresolved_track_or_object_extent', 'grading.actual_revision_year', 'acquisition.resuscitation_or_intervention_context']:
        assert 'trauma_ct.' + suffix in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']} == set(range(5))
    result = audit(data, {'assets': [{'id': 'parent', 'kind': 'model', 'investigation_ids': [item['investigation_id']], 'structure_ids': ['trauma_ct.injury', 'trauma_ct.bladder']}]}, expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements'] == 2070
    assert result['counts'] == {'verified': 0, 'unverified': 0, 'missing': 2070}


def test_ultrasound_and_normal_reference_cannot_supply_ct_injury_regions():
    _, item = inventory()
    target = next(r for r in requirements_for(item) if r['id'] == 'trauma_ct.injury.capsule_breach_if_present')
    source = {'kind': 'clinical_image', 'modality': 'Ultrasound', 'source_context': {'depicted_state': 'actual_traumatic_injury'}}
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(source, target)
    normal = {**source, 'modality': 'CT', 'source_context': {'depicted_state': 'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(normal, target)
    right = next(r for r in requirements_for(item) if r['id'] == 'trauma_ct.vessel_right_renal_arterial_tree.lumen_if_resolved')
    left = {**normal, 'source_context': {'depicted_state': 'normal_anatomy', 'laterality': 'left'}}
    assert 'source_context_laterality_mismatch' in inspect_binding(left, right)


def test_presets_retain_phase_duct_cystography_trajectory_and_grading_limits():
    ref = detail(Curriculum(), resolve('ra.ct-abdominal-trauma'))['radiology_reference']
    steps = ref['walkthrough']['steps']
    assert all('unassessed' in str(s['normal']) for s in steps)
    assert 'Liver, spleen, kidneys, adrenals and pancreas intact' not in str(steps[0]['normal'])
    assert 'No bowel or mesenteric injury' not in str(steps[3]['normal'])
    assert 'not performed' in str(steps[3]['normal'])
    assert 'limited / unassigned' in str(steps[4]['normal'])
    assert 'missing phases' in steps[1]['look']
    assert 'absent apparent growth' in steps[1]['tip']
    assert 'early injury' in steps[3]['look']
    assert 'actual organ-specific scale/revision year' in steps[4]['findings'][1]
    assert 'do not apply one year across organs' in ref['reporting']['classification']['version']
    assert any('renal 2025 and pancreatic 2024' in s for s in ref['reporting']['pitfalls'])
    assert any('Routine excretory contrast' in s for s in ref['reporting']['pitfalls'])
    assert len(ref['reporting']['sources']) == 5
    assert any('Immediately communicate' in s for s in ref['reporting']['escalation'])
