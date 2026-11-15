"""Peripheral arterial scope requires actual source trees/variants rather than parent aorta or normal runoff."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import audit,requirements_for,validate_reporting_snapshots
ROOT=Path(__file__).resolve().parents[1];IDENT='ra.mra-peripheral-vessels'
def test_named_bilateral_branches_variants_and_all_fields_remain_required():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(i for i in data['investigations'] if i['investigation_id']==IDENT);ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];single={**data,'scope':{**data['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]}
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')});validate_reporting_snapshots(single,{IDENT:ref['reporting']})
    assert len(item['structures'])==90 and len(requirements_for(item))==945 and {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    ids={r['id'] for r in requirements_for(item)}
    for side in ['right','left']:
        for artery in ['common_iliac','internal_iliac','profunda_femoris','popliteal','anterior_tibial','tibioperoneal_trunk','peroneal','posterior_tibial','dorsalis_pedis','medial_plantar','lateral_plantar','plantar_arch','metatarsal_branches','digital_branches']:
            assert f'peripheral_mra.{side}_{artery}.actual_origin' in ids and f'peripheral_mra.{side}_{artery}.uncovered_or_unresolved_extent' in ids
        assert f'peripheral_mra.{side}_runoff_tree.high_origin_or_other_branching_variant' in ids and f'peripheral_mra.{side}_intervention.distal_anastomosis_or_attachment' in ids
        assert f'peripheral_mra.{side}_perforator_tissue_relations.actual_septal_or_muscle_interface' in ids
        assert f'peripheral_mra.{side}_collateral_routes.flow_direction_source_if_obtained' in ids
    assert 'peripheral_mra.additional_territories.separate_scope_expansion_required' in ids
    result=audit(single,{'assets':[{'id':'generic-aorta','kind':'model','investigation_ids':[IDENT],'structure_ids':['peripheral_mra.left_anterior_tibial','peripheral_mra.left_plantar_arch']}]},expected_catalog_ids={IDENT})
    assert result['counts']=={'verified':0,'unverified':0,'missing':2835} and not result['clinical_commercial_ready']
def test_presets_cannot_assert_normal_patency_runoff_or_clinical_function():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];steps=ref['walkthrough']['steps'];assert all(s['normal']=={} for s in steps)
    assert 'three patent channels' in steps[3]['detail'] and 'tissue viability' in steps[3]['tip']
    assert 'not automatically absent or occluded' in steps[0]['tip']
    assert 'reference convention' in steps[2]['tip']
    assert 'do not delay care' in steps[4]['tip'] and 'Historical scanner/coil' in steps[4]['tip']
    assert 'does not supply patient-specific' in ref['walkthrough']['spatial_model']['reporting_aim']
    fields={r['heading']:r['body'] for r in ref['reporting']['template_sections']}
    assert 'pedal/plantar arch connections' in fields['RUNOFF AND COLLATERALS'] and 'flow/metal/subtraction mimics' in fields['LESION MORPHOLOGY']
    assert 'extravascular' in fields['TECHNICAL LIMITATIONS']
def test_source_review_does_not_grant_image_rights_or_complete_clinical_approval():
    p=json.loads((ROOT/'docs/peripheral-mra-source-review.json').read_text())
    assert not p['image_rights_or_original_pixels_approved'] and not p['clinical_approval'] and not p['structure_coverage_granted']
    assert p['source_review_scope']=='listed_effective_guide_and_primary_source_extracts_only'
    assert p['historical_RA_treatment_scanner_and_resolution_claims_not_adopted_as_universal']
