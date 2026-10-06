"""Regional cardiac anatomy/function needs actual source contours, phases and tissue methods."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import audit,requirements_for,validate_reporting_snapshots
ROOT=Path(__file__).resolve().parents[1];IDENT='ra.mri-cardiomyopathy'
def test_every_region_layer_and_report_field_are_required():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(i for i in data['investigations'] if i['investigation_id']==IDENT);ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];single={**data,'scope':{**data['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]}
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')});validate_reporting_snapshots(single,{IDENT:ref['reporting']})
    assert len(item['structures'])==67 and len(requirements_for(item))==636 and {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    ids={r['id'] for r in requirements_for(item)}
    for n in range(1,18):
        for part in ['source_endocardial_surface','source_midwall_region','epicardial_surface','actual_temporal_thickening_source','unresolved_layer_or_uncovered_extent']:assert f'cardiomyopathy.lv_segment_{n}.{part}' in ids
    for suffix in ['right_ventricular_pool.papillary_trabecular_inclusion_convention','rv_outflow.actual_temporal_motion_source','mapping.motion_registration_and_partial_volume','ecv.haematocrit_source_value_and_date_if_used','ecv.named_synthetic_or_other_alternative_if_used','lge.mvo_or_other_mixed_component','volume_function.actual_reference_population_and_method']:
        assert 'cardiomyopathy.'+suffix in ids
    result=audit(single,{'assets':[{'id':'normal-heart','kind':'model','investigation_ids':[IDENT],'structure_ids':['cardiomyopathy.left_ventricular_wall','cardiomyopathy.lv_segment_1']}]},expected_catalog_ids={IDENT})
    assert result['counts']=={'verified':0,'unverified':0,'missing':1908} and item['modality_scope']==['MRI']
def test_no_preset_or_exclusive_pattern_supplies_normal_function_or_diagnosis():
    r=detail(Curriculum(),resolve(IDENT))['radiology_reference'];s=r['walkthrough']['steps'];assert all(x['normal']=={} for x in s)
    assert 'papillary/trabecular conventions' in s[0]['tip'] and 'still/model' in s[0]['tip']
    assert 'actual named segment/region' in s[1]['look'] and 'colour pictures are not calibrated measurements' in s[2]['tip']
    assert 'global subendocardial' in s[3]['tip'] and 'do not uniquely establish cause' in s[3]['tip'] and 'does not exclude all cardiomyopathy' in s[3]['tip']
    assert 'No single filling defect' in s[4]['tip']
    assert 'does not supply patient-specific' in r['walkthrough']['spatial_model']['reporting_aim']
    assert any('contour method' in v['body'] for v in r['reporting']['template_sections'])
def test_reviewed_sources_do_not_grant_complete_clinical_or_pixel_approval():
    p=json.loads((ROOT/'docs/cardiomyopathy-source-review.json').read_text());assert {r['pmcid'] for r in p['sources']}=={'PMC7066763','PMC11084160'}
    assert all(r['actual_license']=='CC BY 4.0' and not r['images_reused'] and not r['anatomical_approval'] for r in p['sources'])
    assert not p['clinical_approval'] and not p['structure_coverage_granted']
