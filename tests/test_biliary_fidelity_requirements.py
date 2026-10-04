"""Fine duct targets, actual modalities and clinical infection boundaries stay explicit."""
import json
from pathlib import Path

from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    item = next(i for i in data['investigations'] if i['investigation_id'] == 'ra.biliary-duct-pathology')
    return {**data, 'investigations': [item], 'scope': {'catalog_investigation_ids': ['ra.biliary-duct-pathology']}}, item


def test_full_biliary_reporting_contract_and_branches_require_separate_coverage():
    data, item = inventory()
    ref = detail(Curriculum(), resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data, {item['investigation_id']: ref['reporting']})
    assert item['source_contract_sha256'] == digest({k: ref.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')})
    leaves = {r['id']: r for r in requirements_for(item)}
    assert len(leaves) == 306
    for name in ('segment_caudate_I.complete_branch_tree', 'segment_right_posterior_VII.each_subsegmental_branch',
                 'duct_intramural_common_bile.complete_lumen', 'variants.right_posterior_to_left_duct',
                 'right_vascular.arterial_sectoral_branches', 'postoperative.excluded_undrained_segment'):
        assert 'biliary.' + name in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']} == set(range(5))
    result = audit(data, {'assets': [{'id': 'parent', 'kind': 'model', 'investigation_ids': [item['investigation_id']],
                                     'structure_ids': ['biliary.duct_common_hepatic', 'biliary.ampullary']}]},
                   expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements'] == 918
    assert result['counts'] == {'verified': 0, 'unverified': 0, 'missing': 918}


def test_static_parent_anatomy_cannot_supply_pathology_mri_or_ultrasound_features():
    _, item = inventory()
    leaves = {r['id']: r for r in requirements_for(item)}
    asset = {'kind': 'clinical_image', 'modality': 'CT', 'source_context': {'depicted_state': 'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(asset, leaves['biliary.material.each_stone'])
    assert 'source_context_purpose_mismatch' in inspect_binding(asset, leaves['biliary.adjacent.peritoneal_deposit_if_present'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset, leaves['biliary.mri.source_dwi_if_acquired'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset, leaves['biliary.ultrasound.acoustic_shadow_if_present'])


def test_reader_does_not_exclude_clinical_cholangitis_or_invent_surgical_history():
    ref = detail(Curriculum(), resolve('ra.biliary-duct-pathology'))['radiology_reference']
    step = ref['walkthrough']['steps'][4]
    assert 'imaging alone cannot exclude it' in str(step['normal'])
    assert 'No stent or prior biliary surgery' not in str(step['normal'])
    assert 'standalone resectability decision' in ref['walkthrough']['steps'][2]['tip']
    assert len(ref['reporting']['sources']) == 3
    n = Curriculum().nodes['rad.5.biliary']
    assert 'no universal length-only diagnostic cutoff' in n['reference']['measure'][1]['cutoff']
    assert 'does not prove TG18 Grade III' in n['quiz'][13]['explain']
    assert 'dopamine ≥5' in n['quiz'][13]['explain']
    assert n['quiz'][13]['answer'] == 'Urgent biliary decompression by ERCP, alongside resuscitation and intravenous antibiotics'
