"""Routine CT must not turn source anatomy/patterns into unperformed quantitative or functional diagnoses."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for,validate_reporting_snapshots,audit
ROOT=Path(__file__).resolve().parents[1];IDENT='ra.ct-cardiovascular-pearls'
def test_complete_named_source_scope_and_all_report_fields_remain_required():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(i for i in data['investigations'] if i['investigation_id']==IDENT);ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];single={**data,'scope':{**data['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]}
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')});validate_reporting_snapshots(single,{IDENT:ref['reporting']})
    assert len(item['structures'])==111 and len(requirements_for(item))==1082 and {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    ids={r['id'] for r in requirements_for(item)}
    for key in ['LAA','RAA','atrial_membrane','aortic_valve','tricuspid_valve','levoatrial_cardinal_vein','left_superior_intercostal_vein','scimitar_return','systemic_lung_supply','ductus_ligament_region','coronary_variant','coronary_fistula']:
        assert any(i.startswith('chest_cv.'+key+'.') for i in ids)
    for sinus in ['right_coronary','left_coronary','noncoronary']:assert 'chest_cv.'+sinus+'_sinus.actual_source_resolved_sinus_boundary' in ids
    assert 'chest_cv.myocardial_aneurysm.actual_outpouching_subtype_and_differential' in ids
    for n in range(1,18):assert f'chest_cv.LV_region_{n}.unassigned_or_unresolved_extent' in ids
    for key in ['CAC_visual.whole_patient_visual_burden_method','valve_calcium.leaflet_vs_root_wall_annular_or_coronary_location','functional_evidence.actual_flow_pressure_shunt_or_perfusion_source','pericardial_compartments.each_fluid_fat_calcium_or_thickened_region']:
        assert 'chest_cv.'+key in ids
    result=audit(single,{'assets':[{'id':'generic-heart','kind':'model','investigation_ids':[IDENT],'structure_ids':['chest_cv.LAA','chest_cv.pericardial_compartments']}]},expected_catalog_ids={IDENT});assert result['counts']=={'verified':0,'unverified':0,'missing':3246} and not result['clinical_commercial_ready']
def test_presets_or_still_morphology_cannot_assert_normal_or_functional_results():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];steps=ref['walkthrough']['steps'];assert all(s['normal']=={} for s in steps)
    assert 'not a measurement of flow' in steps[0]['tip'] and 'one filling defect' in steps[0]['tip']
    assert 'overestimate wall thickness' in steps[1]['tip'] and 'not automatic infarct timing' in steps[1]['tip']
    assert 'whole-patient visual CAC burden' in steps[2]['tip'] and 'not CAD-RADS stenosis grading' in steps[2]['tip']
    assert 'No universal vessel size' in steps[3]['tip'] and 'left SVC drainage' in steps[3]['tip']
    assert 'does not independently establish tamponade' in steps[4]['tip']
    assert 'does not supply the patient-specific' in ref['walkthrough']['spatial_model']['reporting_aim']
    fields={x['heading']:x['body'] for x in ref['reporting']['template_sections']};assert 'clinical/functional confirmation' in fields['PERICARDIUM'] and 'unavailable pressure/shunt/perfusion evidence' in fields['GREAT VESSELS']
def test_original_source_grants_do_not_approve_source_pixels_or_complete_anatomy():
    p=json.loads((ROOT/'docs/chest-cardiovascular-source-review.json').read_text());assert {r['pmcid'] for r in p['sources']}=={'PMC6365314','PMC7774698'} and all(r['original_license']=='CC BY 4.0' and not r['images_or_models_reused'] and not r['anatomical_approval'] for r in p['sources'])
    assert not p['clinical_approval'] and not p['structure_coverage_granted'] and not p['image_rights_or_complete_original_pixels_approved']
