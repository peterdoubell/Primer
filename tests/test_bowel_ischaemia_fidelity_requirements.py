"""Phase-dependent vascular and wall observations cannot be created by normal presets."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]


def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item=next(i for i in data['investigations'] if i['investigation_id']=='ra.ct-bowel-ischaemia')
    return {**data,'investigations':[item],'scope':{'catalog_investigation_ids':[item['investigation_id']]}},item


def test_actual_vascular_bowel_and_reperfusion_scope_matches_reader_contract():
    data,item=inventory();ref=detail(Curriculum(),resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data,{item['investigation_id']:ref['reporting']})
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    leaves={r['id']:r for r in requirements_for(item)};assert len(leaves)==304
    for name in ['arterial_microtree.vasa_recta','vein_ileal_tributaries.bowel_drainage_interface',
                 'segment_terminal_ileum.outer_wall_if_resolved','wall_injury.unenhanced_hyperattenuating_wall',
                 'mechanical.second_transition','reperfusion_context.baseline_affected_wall']:
        assert 'bowel_ischaemia.'+name in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    result=audit(data,{'assets':[{'id':'parent','kind':'model','investigation_ids':[item['investigation_id']],
                                 'structure_ids':['bowel_ischaemia.wall_injury','bowel_ischaemia.arterial_microtree']}]},expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements']==912 and result['counts']=={'verified':0,'unverified':0,'missing':912}


def test_normal_anatomical_models_do_not_supply_injury_or_reperfusion_examples():
    _,item=inventory();leaves={r['id']:r for r in requirements_for(item)}
    image={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(image,leaves['bowel_ischaemia.wall_injury.nonenhancing_wall_if_assessable'])
    assert 'source_context_purpose_mismatch' in inspect_binding(image,leaves['bowel_ischaemia.reperfusion_context.current_affected_wall'])


def test_normal_preset_retains_arterial_venous_and_wall_phase_limitations():
    ref=detail(Curriculum(),resolve('ra.ct-bowel-ischaemia'))['radiology_reference'];steps=ref['walkthrough']['steps']
    assert 'not assessable' in str(steps[0]['normal']) and 'not assessable' in str(steps[1]['normal'])
    assert 'Normal enhancement' not in str(steps[2]['normal']) and 'unassessed' in str(steps[2]['normal'])
    assert 'baseline attenuation' in steps[2]['look']
    assert 'source colours' in steps[2]['tip']
    assert len(ref['reporting']['sources'])==3
    assert any('Immediately communicate' in x for x in ref['reporting']['escalation'])
