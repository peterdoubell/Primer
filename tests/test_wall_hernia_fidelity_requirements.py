"""Hernia source geometry and planning metrics do not prove dynamics, viability or operative outcomes."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]


def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(r for r in data['investigations'] if r['investigation_id']=='ra.abdominal-wall-hernias')
    return {**data,'investigations':[item],'scope':{'catalog_investigation_ids':[item['investigation_id']]}},item


def test_actual_wall_defect_content_repair_and_volume_fields_are_separately_required():
    data,item=inventory();ref=detail(Curriculum(),resolve(item['investigation_id']))['radiology_reference'];validate_reporting_snapshots(data,{item['investigation_id']:ref['reporting']})
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    leaves={r['id']:r for r in requirements_for(item)};assert len(leaves)==337
    for suffix in ['left_rectus_sheath.posterior_sheath_where_present','semilunar_and_groin_landmarks_if_relevant.right_inferior_epigastric_interface_if_resolved','region_right_spigelian.musculoaponeurotic_layer','defects.interdefect_bridge_if_present','sac.neck_if_resolved','contents.entry_limb','contents.unresolved_adhesion_or_connection_limit','volumetry.complete_source_residual_ACV_boundary','volumetry.explicitly_named_denominator','repair.nonvisualised_mesh_limit','complications.each_resolved_tract_endpoint','acquisition.actual_strain_or_Valsalva_source_if_performed']:
        assert 'wall_hernia.'+suffix in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    result=audit(data,{'assets':[{'id':'parent','kind':'model','investigation_ids':[item['investigation_id']],'structure_ids':['wall_hernia.defects','wall_hernia.sac']}]},expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements']==1011 and result['counts']=={'verified':0,'unverified':0,'missing':1011}


def test_normal_and_other_modality_images_cannot_supply_positive_ct_defect_geometry():
    _,item=inventory();leaves={r['id']:r for r in requirements_for(item)};target=leaves['wall_hernia.defects.complete_source_aperture']
    source={'kind':'clinical_image','modality':'MRI','source_context':{'depicted_state':'source_hernia'}}
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(source,target)
    normal={**source,'modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(normal,target)
    left={**normal,'source_context':{'depicted_state':'normal_anatomy','laterality':'left'}}
    assert 'source_context_laterality_mismatch' in inspect_binding(left,leaves['wall_hernia.right_rectus.covered_muscle_extent'])


def test_presets_keep_unassessed_dynamics_mesh_volume_method_and_complication_extent():
    ref=detail(Curriculum(),resolve('ra.abdominal-wall-hernias'))['radiology_reference'];steps=ref['walkthrough']['steps']
    assert all('unassessed' in str(s['normal']) for s in steps)
    assert 'No incarceration, obstruction or strangulation' not in str(steps[4]['normal'])
    assert 'not clearly seen' in str(steps[3]['normal'])
    assert 'HSV/ACV / HSV/(HSV+ACV)' in steps[2]['findings'][1]
    assert 'not a guaranteed closure' in steps[2]['findings'][1]
    assert 'Source compartment volumes' in steps[2]['measurements']
    assert 'can coexist' in steps[0]['tip']
    assert 'Do not infer absent mesh' in steps[3]['look']
    assert 'microbiological context' in steps[3]['findings'][2]
    assert 'clinical/dynamic' in steps[2]['normal']['CONTENTS']
    assert len(ref['reporting']['sources'])==3
    assert any('Communicate suspected strangulation' in s for s in ref['reporting']['escalation'])
