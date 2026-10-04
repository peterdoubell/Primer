"""Complete bowel loops and available enhancement cannot be inferred from presets or envelopes."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]


def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item=next(i for i in data['investigations'] if i['investigation_id']=='ra.ct-bowel-obstruction')
    return {**data,'investigations':[item],'scope':{'catalog_investigation_ids':[item['investigation_id']]}},item


def test_bowel_scope_preserves_complete_segments_transitions_and_mesenteric_branches():
    data,item=inventory();ref=detail(Curriculum(),resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data,{item['investigation_id']:ref['reporting']})
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    leaves={r['id']:r for r in requirements_for(item)};assert len(leaves)==268
    for target in ['duodenum_D4.complete_segment','terminal_ileum.distal_connection','closed_loop.second_inflow_or_outflow_point',
                   'arterial.vasa_recta','venous.mesenteric_venous_gas_if_present','hernias.entrapped_mesenteric_pedicle']:
        assert 'bowel_obstruction.'+target in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    result=audit(data,{'assets':[{'id':'bowel','kind':'model','investigation_ids':[item['investigation_id']],
                                'structure_ids':['bowel_obstruction.closed_loop','bowel_obstruction.wall']}]},expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements']==804
    assert result['counts']=={'verified':0,'unverified':0,'missing':804}


def test_normal_anatomy_cannot_supply_pathological_loop_or_ischemic_wall_examples():
    _,item=inventory();leaves={r['id']:r for r in requirements_for(item)}
    image={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(image,leaves['bowel_obstruction.closed_loop.complete_isolated_loop'])
    assert 'source_context_purpose_mismatch' in inspect_binding(image,leaves['bowel_obstruction.wall.hypoenhancing_region'])
    assert {'continuity','enhancement','vascular_relationship','viability_and_urgency'} <= {r['observation'] for r in item['functional_evidence_requirements']}


def test_normal_preset_does_not_fabricate_unavailable_contrast_enhancement():
    ref=detail(Curriculum(),resolve('ra.ct-bowel-obstruction'))['radiology_reference'];step=ref['walkthrough']['steps'][3]
    assert 'Normal wall enhancement' not in str(step['normal'])
    assert 'not assessable on this study' in str(step['normal'])
    assert 'Without suitable contrast, state enhancement is unassessed' in step['look']
    assert 'unavailable enhancement is not normal' in step['tip']
    assert len(ref['reporting']['sources'])==3
    assert any('suspected closed-loop obstruction' in s for s in ref['reporting']['escalation'])
