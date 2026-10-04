"""Actual duct visibility and modality evidence cannot be inferred from a normal preset."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]


def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item=next(i for i in data['investigations'] if i['investigation_id']=='ra.ultrasound-bile-duct-stones')
    return {**data,'investigations':[item],'scope':{'catalog_investigation_ids':[item['investigation_id']]}},item


def test_cbd_stone_scope_preserves_segments_material_and_outlet_interfaces():
    data,item=inventory();ref=detail(Curriculum(),resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data,{item['investigation_id']:ref['reporting']})
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    leaves={r['id']:r for r in requirements_for(item)}
    assert len(leaves)==187
    for name in ['intramural_common_bile.complete_lumen','outlet.major_papilla_if_seen','material.each_stone',
                 'vessels.doppler_reference_region','gallbladder.compression_of_common_hepatic_duct','postoperative.undrained_segment_limit']:
        assert 'cbd_stones.'+name in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    result=audit(data,{'assets':[{'id':'parent','kind':'model','investigation_ids':[item['investigation_id']],
                                 'structure_ids':['cbd_stones.outlet','cbd_stones.material']}]},expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements']==561
    assert result['counts']=={'verified':0,'unverified':0,'missing':561}


def test_normal_ct_and_parent_anatomy_cannot_supply_ultrasound_stone_evidence():
    _,item=inventory();leaves={r['id']:r for r in requirements_for(item)}
    asset={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(asset,leaves['cbd_stones.material.each_stone'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset,leaves['cbd_stones.ultrasound.acoustic_shadow_source'])
    assert {'visibility','mobility','vessel_discrimination'} <= {r['observation'] for r in item['functional_evidence_requirements']}


def test_normal_prefill_does_not_fabricate_whole_course_visibility_or_clearance():
    ref=detail(Curriculum(),resolve('ra.ultrasound-bile-duct-stones'))['radiology_reference'];steps=ref['walkthrough']['steps']
    assert 'visualised along its whole course' not in str(steps[0]['normal'])
    assert 'Unassessed regions and limitations' in str(steps[0]['normal'])
    assert 'does not establish whole-duct clearance' in str(steps[2]['normal'])
    assert 'Clinical/laboratory assessment' in str(steps[4]['normal'])
    assert len(ref['reporting']['sources'])==3
