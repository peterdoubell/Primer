"""Every source site, paired course and compartment remains required across all three representations."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import resolve,detail
from tools.check_msk_fidelity import audit,requirements_for,inspect_binding,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]
IDENT='ra.aortic-aneurysm-rupture'


def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item=next(r for r in data['investigations'] if r['investigation_id']==IDENT)
    return {**data,'scope':{**data['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]},item


def test_effective_contract_and_every_report_field_are_bound_to_complete_draft():
    data,item=inventory();ref=detail(Curriculum(),resolve(IDENT))['radiology_reference']
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    validate_reporting_snapshots(data,{IDENT:ref['reporting']})
    leaves=requirements_for(item);assert len(item['structures'])==66 and len(leaves)==629
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    ids={p['id'] for p in leaves}
    for suffix in ['proximal_neck.lowest_renal_origin_reference','wall.each_calcification_gap','mural_thrombus.each_fissuration_course',
                   'posterior_containment.intervening_fat_plane','right_anterior_pararenal_space.source_resolved_boundary',
                   'left_posterior_pararenal_space.communication_to_other_compartments','perihepatic_space.each_haemorrhage_focus',
                   'left_paracolic_gutter.uncovered_extent','inferior_mesenteric_artery.ostium_and_origin',
                   'right_accessory_renal_arteries.each_branch_or_variant','left_common_femoral.minimum_access_lumen_and_plane',
                   'right_distal_access_runoff.popliteal_covered_course','left_distal_seal_zone.device_and_planning_limit',
                   'aortoenteric_fistula.unresolved_endpoints_and_alternative_cause','ivc.flow_and_complete_tract_limit',
                   'endograft.each_sac_contrast_focus','left_repair_limb.distal_anastomosis_or_seal',
                   'acquisition.bitmap_hu_and_rendering_limit']:
        assert 'aaa_rupture.'+suffix in ids
    result=audit(data,{'assets':[{'id':'generic-arch','kind':'model','investigation_ids':[IDENT],
                                'structure_ids':['aaa_rupture.aortic_course','aaa_rupture.wall']}]},expected_catalog_ids={IDENT})
    assert result['representation_requirements']==1887 and result['counts']=={'verified':0,'unverified':0,'missing':1887}


def test_wrong_side_normal_anatomy_or_modality_cannot_fill_missing_pathology_or_vessels():
    _,item=inventory();leaves={p['id']:p for p in requirements_for(item)}
    normal={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(normal,leaves['aaa_rupture.rupture_sites.wall_site'])
    left={**normal,'source_context':{'depicted_state':'normal_anatomy','laterality':'left'}}
    assert 'source_context_laterality_mismatch' in inspect_binding(left,leaves['aaa_rupture.right_renal_artery.ostium_and_origin'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding({**normal,'modality':'MRI'},leaves['aaa_rupture.aortic_course.bifurcation'])


def test_assessment_prompts_and_crescent_qualification_keep_suspected_rupture_urgent():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];steps=ref['walkthrough']['steps']
    assert steps[2]['label']=='Wall and thrombus' and 'not necessarily' in steps[2]['tip']
    assert 'immediately communicate' in steps[2]['tip'].lower()
    assert 'Immediately communicate suspected aortic rupture or contained leak.' in ref['reporting']['escalation']
    for step in steps[1:]:
        assert '[adequate actual' in next(iter(step['normal'].values()))
        assert 'unassessed' in next(iter(step['normal'].values()))
    assert all('a sign of impending rupture' not in text for text in steps[2]['findings'])
    _,item=inventory();assert item['clinical_validation_status'].startswith('draft_')
    assert all(s['requires_site_instantiation'] for s in item['structures'])
    assert any('not a full guideline review' in s for s in item['source_scope_issues'])
