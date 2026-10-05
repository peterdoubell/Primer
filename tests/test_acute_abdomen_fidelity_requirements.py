"""Acute-abdomen reporting cannot borrow modality, dynamic or cause evidence."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]


def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item=next(r for r in data['investigations'] if r['investigation_id']=='ra.acute-abdomen')
    return {**data,'investigations':[item],'scope':{'catalog_investigation_ids':[item['investigation_id']]}},item


def test_all_actual_fields_and_modality_scopes_have_explicit_source_targets():
    data,item=inventory();ref=detail(Curriculum(),resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data,{item['investigation_id']:ref['reporting']})
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    leaves={r['id']:r for r in requirements_for(item)}
    assert len(leaves)==724
    for suffix in ['appendix.nonvisualised_extent_limit','liver_segment_IVb.biliary_interface_if_resolved','right_adrenal_if_relevant.vascular_interface_if_resolved','hernia_wall_if_relevant.each_bowel_crossing','bowel_sigmoid_colon.adjacent_host_interface','organ_pancreatic_neck.lumen_or_duct_if_resolved','right_kidney.calyces_if_resolved','left_adnexa_if_relevant.vascular_pedicle_if_resolved','collections.source_orthogonal_dimensions','vessel_sma_and_actual_branches.each_actual_branch_or_confluence','ultrasound_features.actual_tenderness_or_murphy_site','mri_if_acquired.adc_correspondence_if_acquired','radiography_if_provided.unassessed_soft_tissue_or_fluid_filled_bowel_limit','source_context.pregnancy_or_postoperative_context_if_relevant']:
        assert 'acute_abdomen.'+suffix in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    result=audit(data,{'assets':[{'id':'parent','kind':'model','investigation_ids':[item['investigation_id']],'structure_ids':['acute_abdomen.appendix','acute_abdomen.ultrasound_features']}]},expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements']==2172 and result['counts']=={'verified':0,'unverified':0,'missing':2172}


def test_source_features_cannot_cross_modality_or_positive_context_boundaries():
    _,item=inventory();leaves={r['id']:r for r in requirements_for(item)}
    normal={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(normal,leaves['acute_abdomen.ultrasound_features.actual_tenderness_or_murphy_site'])
    radiograph={**normal,'modality':'Radiography'}
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(radiograph,leaves['acute_abdomen.appendix.outer_wall'])
    assert 'source_context_purpose_mismatch' in inspect_binding(normal,leaves['acute_abdomen.ct_observations.each_actual_fat_stranding_region'])
    assert 'source_context_purpose_mismatch' not in inspect_binding(normal,leaves['acute_abdomen.ct_features.source_baseline_or_reference_site'])
    us={**normal,'modality':'Ultrasound'}
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(us,leaves['acute_abdomen.mri_if_acquired.adc_correspondence_if_acquired'])


def test_presets_retain_nonvisualisation_actual_dynamic_source_and_unassessed_extent():
    ref=detail(Curriculum(),resolve('ra.acute-abdomen'))['radiology_reference'];steps=ref['walkthrough']['steps']
    assert all('unassessed' in str(s['normal']) for s in steps)
    assert 'not seen' in str(steps[1]['normal'])
    assert 'Normal appendix; no bowel wall thickening' not in str(steps[1]['normal'])
    assert 'No free gas, ascites or collection' not in str(steps[4]['normal'])
    assert 'ultrasound compression only if actually assessed' in steps[1]['findings'][0]
    assert 'does not establish infection or pathogen' in steps[1]['findings'][3]
    assert 'Sonographic Murphy/tenderness/compression only if actually assessed' in steps[2]['findings'][0]
    assert 'absent sources remain unassessed' in steps[2]['look']
    assert 'source colour' in steps[4]['tip']
    assert any('adult nonpregnant' in s for s in ref['reporting']['pitfalls'])
    assert len(ref['reporting']['sources'])==2
    assert any('Communicate suspected perforation' in s for s in ref['reporting']['escalation'])
