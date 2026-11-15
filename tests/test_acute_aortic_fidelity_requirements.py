"""Complete reporting fields and conditional physiology cannot be filled by parent names or generic anatomy."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for,audit,inspect_binding,validate_reporting_snapshots

ROOT=Path(__file__).resolve().parents[1]
IDENT='ra.ct-acute-aortic-syndrome'

def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item=next(r for r in data['investigations'] if r['investigation_id']==IDENT)
    return {**data,'scope':{**data['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]},item

def test_complete_effective_report_and_every_branch_wall_or_compartment_requirement_remain_bound():
    data,item=inventory();ref=detail(Curriculum(),resolve(IDENT))['radiology_reference']
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    validate_reporting_snapshots(data,{IDENT:ref['reporting']})
    leaves=requirements_for(item);assert len(item['structures'])==85 and len(leaves)==750
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    ids={r['id'] for r in leaves}
    for suffix in ['extent.arch_pattern','root.outer_wall_contour','sinotubular_junction.orthogonal_measurement_level',
        'true_lumen.each_compressed_or_collapsed_segment','false_lumen.each_lumen_communication','flap.each_intussusception_if_present',
        'tears.each_separate_communication','intramural_haematoma.each_intramural_blood_pool','ulcerative_lesions.depth_width_and_plane',
        'right_sinus.cusp_or_leaflet_if_resolved','left_main_coronary.source_resolved_true_false_or_shared_supply',
        'right_accessory_renal.each_actual_branch_or_variant','left_common_femoral.covered_distal_course',
        'intercostal_spinal_supply.uncovered_supply_and_resolvability_limit','left_cerebral_territory.clinical_confirmation',
        'malperfusion_mechanisms.actual_dynamic_or_temporal_evidence','pericardium.each_communication_to_other_spaces',
        'right_pleural_space.complete_covered_boundary','open_repair.each_branch_reimplantation_or_stent',
        'endovascular_repair.each_anastomosis_or_seal','acquisition.ecg_gating_and_motion']:
        assert 'aas.'+suffix in ids
    result=audit(data,{'assets':[{'id':'generic-aorta','kind':'model','investigation_ids':[IDENT],
        'structure_ids':['aas.true_lumen','aas.false_lumen','aas.wall']}]},expected_catalog_ids={IDENT})
    assert result['representation_requirements']==2250 and result['counts']=={'verified':0,'unverified':0,'missing':2250}

def test_context_side_and_modality_constraints_cannot_be_borrowed():
    _,item=inventory();leaves={r['id']:r for r in requirements_for(item)}
    normal={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(normal,leaves['aas.intramural_haematoma.greatest_thickness_and_plane'])
    left={**normal,'source_context':{'depicted_state':'normal_anatomy','laterality':'left'}}
    assert 'source_context_laterality_mismatch' in inspect_binding(left,leaves['aas.right_coronary.ostium'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding({**normal,'modality':'MRI'},leaves['aas.ulcerative_lesions.complete_boundary'])

def test_classification_mechanisms_and_normal_defaults_preserve_actual_evidence_and_urgency():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];steps=ref['walkthrough']['steps']
    assert 'ascending aorta is not involved' in steps[0]['findings'][1]
    assert 'non-A/non-B' in steps[0]['findings'][1] and 'classification' in steps[0]['tip']
    assert 'dynamic' in steps[2]['tip'] and 'does not prove' in steps[2]['tip']
    assert 'not diagnosed from volume alone' in steps[3]['findings'][0]
    for index in (0,2,3):
        text=next(iter(steps[index]['normal'].values()))
        assert '[adequate actual' in text and 'unassessed' in text
    assert 'Immediately communicate suspected acute aortic syndrome, rupture or branch malperfusion.' in ref['reporting']['escalation']
    _,item=inventory();assert item['clinical_validation_status'].startswith('draft_')
    assert all(s['requires_site_instantiation'] for s in item['structures'])
