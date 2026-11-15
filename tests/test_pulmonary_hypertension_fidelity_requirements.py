"""Actual pulmonary vascular anatomy cannot supply unperformed haemodynamics or central-only clot rules."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for,validate_reporting_snapshots,audit
ROOT=Path(__file__).resolve().parents[1];IDENT='ra.pulmonary-hypertension'
def test_complete_branch_variant_region_and_report_scope_remain_required():
    d=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(i for i in d['investigations'] if i['investigation_id']==IDENT);r=detail(Curriculum(),resolve(IDENT))['radiology_reference'];single={**d,'scope':{**d['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]}
    assert item['source_contract_sha256']==digest({k:r.get(k) for k in ('reporting','report_templates','walkthrough','reading')});validate_reporting_snapshots(single,{IDENT:r['reporting']})
    assert len(item['structures'])==102 and len(requirements_for(item))==896 and {ref['checklist_index'] for s in item['structures'] for ref in s['report_refs']}==set(range(5))
    ids={r['id'] for r in requirements_for(item)}
    for side in ['right','left']:
        for key in ['upper_apical','upper_posterior','upper_anterior','lower_superior','lower_medial_basal','lower_anterior_basal','lower_lateral_basal','lower_posterior_basal']:assert f'pulm_htn.{side}_{key}_segmental_PA.actual_combined_or_accessory_origin_relationship' in ids
        for key in ['combined_accessory_PA','subsegmental_tree','microvascular_region','web_band_slit','recanalisation','bronchial_collaterals','nonbronchial_collaterals','common_accessory_or_dual_pulmonary_vein']:assert any(i.startswith(f'pulm_htn.{side}_{key}.') for i in ids)
    assert 'pulm_htn.haemodynamics.if_supplied_mPAP_PAWP_PVR_CO_values_units_method' in ids
    assert 'pulm_htn.perfusion_sources.VQ_ventilation_and_perfusion_source_if_separately_obtained' in ids
    result=audit(single,{'assets':[{'id':'normal-thorax','kind':'model','investigation_ids':[IDENT],'structure_ids':['pulm_htn.left_subsegmental_tree','pulm_htn.left_microvascular_region']}]},expected_catalog_ids={IDENT});assert result['counts']=={'verified':0,'unverified':0,'missing':2688}
def test_normal_presets_and_CT_patterns_cannot_supply_negative_or_hemodynamic_diagnosis():
    r=detail(Curriculum(),resolve(IDENT))['radiology_reference'];s=r['walkthrough']['steps'];assert all(step['normal']=={} for step in s)
    assert 'cannot be negative' in s[0]['detail'] and 'Acute emboli may be eccentric' in s[1]['tip']
    assert 'CTEPD may occur without PH' in s[2]['tip'] and 'does not alone exclude distal chronic disease' in s[2]['tip']
    assert 'mPAP >20 mmHg' in s[3]['tip'] and 'PAWP ≤15 mmHg' in s[3]['tip'] and 'PVR >2 WU' in s[3]['tip']
    assert 'No such values are inferred from CT' in s[3]['tip'] and 'not automatic WHO-group' in s[4]['tip']
    assert 'does not supply patient-specific' in r['walkthrough']['spatial_model']['reporting_aim']
    assert r['reporting']['classification'] is None

def test_source_licence_and_definition_limits_do_not_approve_coverage():
    p=json.loads((ROOT/'docs/pulmonary-hypertension-source-review.json').read_text());source={r['pmcid']:r for r in p['sources']};assert source['PMC11657945']['original_license']=='CC BY-NC-ND 4.0' and source['PMC10971453']['original_license']=='CC BY 4.0'
    assert all(not r['images_or_models_reused'] and not r['anatomical_approval'] for r in source.values())
    assert p['RA_source_ge20_vs_named_ESC_strict_gt20_discrepancy_preserved'] and not p['clinical_approval'] and not p['structure_coverage_granted']
