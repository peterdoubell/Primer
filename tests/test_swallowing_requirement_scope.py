"""Actual timed source findings cannot be supplied by static normal presets."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for
ROOT=Path(__file__).resolve().parents[1];INV='ra.swallowing'
def item():return next(x for x in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if x['investigation_id']==INV)
def test_each_oral_airway_sphincter_and_trial_interface_remains_required():
    i=item();assert i['module_id']=='rad.5.esophagus-swallowing' and len(i['structures'])==81 and len(requirements_for(i))==486
    ids={x['id'] for x in i['structures']}
    for side in ['left','right']:
        for key in ['oral_tongue_intrinsic_and_extrinsic_components','pyriform_recess_and_apical_interface','arytenoid_false_fold_and_true_vocal_fold','each_actual_or_supplied_V_VII_IX_X_XII_route_and_target','each_actual_postoperative_or_reconstructed_tissue','each_actual_lateral_bolus_route_or_residue']:assert 'swallowing.'+side+'_'+key in ids
    for key in ['pharyngoesophageal_segment_and_cricopharyngeal_interfaces','covered_thoracic_esophagus_and_junctional_extent','each_observed_subglottic_aspiration_event','each_observed_cough_or_absent_recorded_response','each_tested_posture_or_compensatory_manoeuvre']:assert 'swallowing.not_applicable_'+key in ids
    assert all(x['requires_site_instantiation'] for x in i['structures']);assert sum(x['requires_actual_temporal_evidence'] for x in i['structures'])==22
    assert all(0<=r['checklist_index']<5 for x in i['structures'] for r in x['report_refs'])
def test_normality_risk_or_function_is_not_supplied_by_still_or_generic_model():
    r=detail(Curriculum(),resolve(INV))['radiology_reference'];w=r['walkthrough'];assert all(x['normal']=={} for x in w['steps']);assert 'Partial swallowing orientation' in w['spatial_model']['reporting_aim']
    assert 'does not uniquely diagnose' in w['steps'][1]['tip'];assert 'without a universal risk ranking' in w['steps'][2]['tip'];assert 'does not guarantee general safety' in w['steps'][4]['look']
    protocol=' '.join(r['reporting']['protocol']);assert 'recorded frame rate' in protocol and 'pulse rate' in protocol and 'bolus volume/consistency' in protocol
    functional=' '.join(item()['functional_evidence_requirements']);assert 'cannot be inferred from a still' in functional and 'Pressure/manometry' in functional
