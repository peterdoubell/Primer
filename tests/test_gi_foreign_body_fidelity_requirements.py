"""Radiographic projection and negative gas findings cannot substitute for complete object/CT injury evidence."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]

def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    item=next(r for r in data['investigations'] if r['investigation_id']=='ra.gi-foreign-bodies')
    return {**data,'investigations':[item],'scope':{'catalog_investigation_ids':[item['investigation_id']]}},item


def test_all_object_endpoint_host_and_injury_requirements_match_effective_reader():
    data,item=inventory();ref=detail(Curriculum(),resolve(item['investigation_id']))['radiology_reference']
    validate_reporting_snapshots(data,{item['investigation_id']:ref['reporting']})
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    leaves={r['id']:r for r in requirements_for(item)};assert len(leaves)==355
    for suffix in ['each_object.each_sharp_tip','each_object.unseen_endpoint_limit','segment_duodenum_fourth.outer_wall_if_resolved',
                   'localisation.source_cross_axis_plane','host_psoas_if_relevant.unassessed_penetration_boundary',
                   'vessel_aorta_if_relevant.nearest_object_tip_interface','migration.unassessed_source_correspondence',
                   'radiographic_source.magnification_or_calibration_limit','positive_examples.contained_perforation_without_free_gas_example']:
        assert 'gi_foreign_body.'+suffix in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    result=audit(data,{'assets':[{'id':'parent','kind':'model','investigation_ids':[item['investigation_id']],
                                'structure_ids':['gi_foreign_body.each_object','gi_foreign_body.perforation']}]},expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements']==1065 and result['counts']=={'verified':0,'unverified':0,'missing':1065}


def test_projection_cannot_cover_ct_depth_and_ct_cannot_replace_radiographic_projection():
    _,item=inventory();leaves={r['id']:r for r in requirements_for(item)}
    radiograph={'kind':'clinical_image','modality':'Radiography','source_context':{'depicted_state':'foreign_body_injury'}}
    ct={**radiograph,'modality':'CT'}
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(radiograph,leaves['gi_foreign_body.localisation.traversed_wall_region'])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(ct,leaves['gi_foreign_body.radiographic_source.object_projection'])
    normal={**ct,'source_context':{'depicted_state':'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(normal,leaves['gi_foreign_body.each_object.complete_body'])


def test_negative_presets_do_not_exclude_ingestion_perforation_or_adjacent_injury():
    ref=detail(Curriculum(),resolve('ra.gi-foreign-bodies'))['radiology_reference'];steps=ref['walkthrough']['steps']
    for index in [0,2,3,4]:assert 'unassessed' in str(steps[index]['normal'])
    assert 'No foreign body identified' not in str(steps[0]['normal'])
    assert 'No perforation or collection' not in str(steps[3]['normal'])
    assert 'Absence of free gas alone does not exclude perforation' in str(steps[3]['normal'])
    assert 'Projected proximity is not proof' in steps[4]['tip']
    assert 'reliable prior correspondence' in steps[4]['tip']
    assert steps[0]['measurements']==['Object dimensions'] and len(ref['reporting']['measurements'])==1
    assert len(ref['reporting']['sources'])==3
    assert any('Communicate a perforating sharp object' in r for r in ref['reporting']['escalation'])
    assert any('not universal paediatric' in r for r in ref['reporting']['pitfalls'])
