"""Incomplete channel tracing or static generic anatomy cannot pass congenital reporting scope."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import audit,requirements_for,validate_reporting_snapshots
ROOT=Path(__file__).resolve().parents[1]
IDENT='ra.vascular-anomalies'
def test_actual_branches_connections_and_every_report_field_are_required():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(i for i in data['investigations'] if i['investigation_id']==IDENT)
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];single={**data,'scope':{**data['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]}
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    validate_reporting_snapshots(single,{IDENT:ref['reporting']})
    assert len(item['structures'])==73 and len(requirements_for(item))==734
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    ids={p['id'] for p in requirements_for(item)}
    for suffix in ['left_brachiocephalic.actual_origin','left_arch_component.atretic_extent_and_inference_basis',
        'right_ductal_component.source_visualisation_or_inference_basis','ring_map.exact_uncertainty_and_unresolved_component',
        'airway_variant.bridging_bronchus_course','left_pulmonary_artery.interruption_vs_hypoplasia_vs_non_opacification',
        'right_middle_pulmonary_veins.every_dual_connection','left_lingular_pulmonary_veins.each_atrial_or_systemic_endpoint',
        'left_pericardiophrenic.lateral_cardiac_and_diaphragm_relation','right_levoatriocardinal.bidirectional_or_unresolved_function','left_atrial_appendage.relevant_isomerism_context','venous_collaterals.acquired_vs_congenital_context','left_svc.actual_coronary_sinus_or_atrial_endpoint','coronary_sinus.roof_and_left_atrial_relation',
        'hepatic_ivc.continuity_or_interruption','hemiazygos.continuation_and_systemic_endpoint',
        'repair.each_actual_graft_patch_stent_or_reimplantation','functional_context.shunt_direction_and_quantification_source']:
        assert 'vascular_anomaly.'+suffix in ids
    result=audit(single,{'assets':[{'id':'generic-arch','kind':'model','investigation_ids':[IDENT],
        'structure_ids':['vascular_anomaly.arch','vascular_anomaly.left_svc']}]},expected_catalog_ids={IDENT})
    assert result['counts']=={'verified':0,'unverified':0,'missing':2202}
    assert item['clinical_validation_status'].startswith('draft_')
def test_reporting_does_not_invent_normality_drainage_or_function():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];s=ref['walkthrough']['steps'];r=ref['reporting']
    assert all(step['normal']=={} for step in s)
    assert 'inferred atretic' in s[0]['tip']
    assert 'Static narrowing alone' in s[1]['tip']
    assert 'proximal pulmonary artery interruption' in s[2]['tip']
    assert 'Do not assume four' in s[3]['tip']
    assert 'left-atrial drainage occurs' in s[4]['tip']
    assert 'generic aorta model does not contain the actual anomaly' in ref['walkthrough']['spatial_model']['reporting_aim']
    assert any('extra' in t or 'automatically' in t for t in r['pitfalls'])
    assert 'actual drainage endpoint' in r['checklist'][4]['detail'].lower() or 'actual drainage' in r['checklist'][4]['detail'].lower()
