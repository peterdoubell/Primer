import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for,inspect_binding,validate_reporting_snapshots,audit
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]


def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    inv=next(x for x in data['investigations'] if x['investigation_id']=='ra.ct-coronary')
    return {**data,'investigations':[inv],'scope':{'catalog_investigation_ids':['ra.ct-coronary']}},inv


def test_complete_coronary_contract_and_conditional_targets_are_retained():
    data,inv=inventory();ref=detail(Curriculum(),resolve('ra.ct-coronary'))['radiology_reference']
    validate_reporting_snapshots(data,{'ra.ct-coronary':ref['reporting']})
    assert inv['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    leaves={x['id']:x for x in requirements_for(inv)}
    assert len(leaves)==181
    for key in ('coronary_ct.left_main.ostium_lumen','coronary_ct.lad.middle_wall_boundary',
                'coronary_ct.graft.distal_anastomosis','coronary_ct.stent.stented_lumen',
                'coronary_ct.anomalous_origin_course.intramural_segment','coronary_ct.plaque.napkin_ring_rim',
                'coronary_ct.cardiac_context.pericardial_space','coronary_ct.extracardiac.upper_abdominal_organs'):
        assert key in leaves
    assert {r['checklist_index'] for s in inv['structures'] for r in s['report_refs']}==set(range(5))
    assert len(inv['source_scope_issues'])==4 and len(inv['functional_evidence_requirements'])==5
    assert any(s['requires_site_instantiation'] for s in inv['structures'])


def test_normal_non_ct_reference_cannot_replace_lesion_specific_ct():
    _,inv=inventory();leaves={x['id']:x for x in requirements_for(inv)}
    asset={'kind':'clinical_image','modality':'MRI','source_context':{'depicted_state':'normal_anatomy'}}
    issues=inspect_binding(asset,leaves['coronary_ct.plaque.napkin_ring_rim'])
    assert 'clinical_image_modality_not_in_requirement_scope' in issues
    assert 'source_context_purpose_mismatch' in issues
    assert 'source_context_depicted_state_mismatch' in issues


def test_generic_trunk_model_receives_no_segment_or_lumen_credit():
    data,_=inventory()
    model={'id':'gross-coronary-tree','kind':'model','investigation_ids':['ra.ct-coronary'],
           'structure_ids':['coronary_ct.left_main','coronary_ct.lad']}
    result=audit(data,{'assets':[model]},expected_catalog_ids={'ra.ct-coronary'})
    assert result['representation_requirements']==543
    assert result['counts']=={'verified':0,'unverified':0,'missing':543}
    assert not result['clinical_commercial_ready']


def test_normal_prefill_keeps_dominance_case_specific_and_model_limits_visible():
    ref=detail(Curriculum(),resolve('ra.ct-coronary'))['radiology_reference']
    steps=ref['walkthrough']['steps']
    normal=steps[1]['normal']['CORONARY DOMINANCE']
    assert '[right / left / co-dominant]' in normal and 'PDA origin: [ ]' in normal
    assert 'Right-dominant' not in normal
    assert len(steps)==7 and all(s['anatomy_note'] for s in steps)
    assert 'Agatston' in steps[0]['anatomy_note']
    assert 'lumen' in steps[2]['anatomy_note']
    assert 'physiological' in steps[4]['anatomy_note']


def test_coronary_source_figures_are_assigned_to_their_actual_depicted_subject():
    ref=detail(Curriculum(),resolve('ra.ct-coronary'))['radiology_reference']
    steps=ref['walkthrough']['steps']
    assert steps[1]['images']==['ccta-img-1','ccta-img-4']
    assert 'ccta-img-5' not in steps[1]['images']
    assert 'ccta-img-7' not in steps[2]['images']
    assert steps[3]['images']==['ccta-img-7']
    assert steps[4]['images']==['ccta-img-5','ccta-img-8']
    by_id={x['id']:x for x in ref['key_images']}
    assert by_id['ccta-img-5']['label']=='IMG 5 · Coronary stent example'
    assert by_id['ccta-img-7']['label']=='IMG 7 · Plaque morphology'
    assert 'orthogonal lumen views' in next(s['body'] for s in ref['report_templates'][0]['sections'] if s['heading']=='KEY IMAGES')
