import json
from pathlib import Path

from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import requirements_for, inspect_binding, validate_reporting_snapshots, audit
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def brain_inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    inv = next(i for i in data['investigations'] if i['investigation_id'] == 'ra.brain-anatomy')
    return {**data, 'investigations': [inv], 'scope': {'catalog_investigation_ids': ['ra.brain-anatomy']}}, inv


def test_brain_reporting_contract_and_each_named_step_are_retained():
    data, inv = brain_inventory()
    ref = detail(Curriculum(), resolve('ra.brain-anatomy'))['radiology_reference']
    validate_reporting_snapshots(data, {'ra.brain-anatomy': ref['reporting']})
    assert inv['source_contract_sha256'] == digest({k: ref.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')})
    assert {r['checklist_index'] for s in inv['structures'] for r in s['report_refs']} == set(range(5))
    leaves = {r['id']: r for r in requirements_for(inv)}
    assert len(leaves) == 210
    for key in ('brain.left_internal_capsule.posterior_limb', 'brain.corpus_callosum.splenium',
                'brain.right_cerebellum.middle_peduncle', 'brain.right_cisterns.ambient_cistern',
                'brain.left_territories.internal_border_zone', 'brain.right_venous_drainage.internal_cerebral_vein',
                'brain.left_source_regions.hippocampal_tail', 'brain.pituitary.stalk'):
        assert key in leaves
    assert inv['expansion_rules'] and len(inv['source_scope_issues']) == 4


def test_wrong_side_and_modality_cannot_satisfy_a_brain_image_requirement():
    _, inv = brain_inventory()
    leaves = {r['id']: r for r in requirements_for(inv)}
    requirement = leaves['brain.left_internal_capsule.posterior_limb']
    assert 'source_context_laterality_mismatch' in inspect_binding(
        {'kind': 'clinical_image', 'modality': 'MRI', 'source_context': {'laterality': 'right'}}, requirement)
    assert any('modality' in x for x in inspect_binding(
        {'kind': 'clinical_image', 'modality': 'Ultrasound', 'source_context': {'laterality': 'left'}}, requirement))


def test_gross_parent_labels_and_offline_candidates_receive_no_child_credit():
    data, _ = brain_inventory()
    gross = {'id': 'gross-capsule', 'kind': 'model', 'investigation_ids': ['ra.brain-anatomy'],
             'structure_ids': ['brain.left_internal_capsule'], 'source_context': {'laterality': 'left'}}
    report = audit(data, {'assets': [gross]}, expected_catalog_ids={'ra.brain-anatomy'})
    assert report['representation_requirements'] == 630
    assert report['counts'] == {'verified': 0, 'unverified': 0, 'missing': 630}
    assert not report['clinical_commercial_ready']
