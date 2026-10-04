"""MRI-specific observations and temporal comparisons cannot be borrowed from CT or static model colours."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]

def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(r for r in data['investigations'] if r['investigation_id']=='ra.mri-crohn')
    return {**data,'investigations':[item],'scope':{'catalog_investigation_ids':[item['investigation_id']]}},item


def test_complete_mri_wall_stricture_tract_and_comparison_scope_matches_effective_reader():
    data,item=inventory();ref=detail(Curriculum(),resolve(item['investigation_id']))['radiology_reference'];validate_reporting_snapshots(data,{item['investigation_id']:ref['reporting']})
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    leaves={r['id']:r for r in requirements_for(item)};assert len(leaves)==344
    for suffix in ['segment_terminal_ileum.antimesenteric_border','mural_observations.adc_corresponding_region',
                   'narrowing.actual_persistence_source','tracts.each_actual_branch','tracts.unresolved_endpoint_limit',
                   'collections.outer_wall_interface','postoperative.neoterminal_ileum','comparison.matched_sequence_site',
                   'acquisition.recorded_diffusion_b_values','pelvic_if_covered.unresolved_perianal_extent']:
        assert 'crohn_mri.'+suffix in leaves
    assert {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    result=audit(data,{'assets':[{'id':'parent','kind':'model','investigation_ids':[item['investigation_id']],
                                'structure_ids':['crohn_mri.tracts','crohn_mri.mural_observations']}]},expected_catalog_ids={item['investigation_id']})
    assert result['representation_requirements']==1032 and result['counts']=={'verified':0,'unverified':0,'missing':1032}


def test_ct_and_normal_reference_cannot_supply_mri_disease_features():
    _,item=inventory();leaves={r['id']:r for r in requirements_for(item)}
    ct={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'crohn_wall_observation'}}
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(ct,leaves['crohn_mri.mural_observations.t2_high_signal_region'])
    normal={**ct,'modality':'MRI','source_context':{'depicted_state':'normal_anatomy'}}
    assert 'source_context_purpose_mismatch' in inspect_binding(normal,leaves['crohn_mri.tracts.complete_source_visible_course'])
    assert 'source_context_depicted_state_mismatch' in inspect_binding(normal,leaves['crohn_mri.phenotype_examples.poor_distension_mimic_example'])


def test_presets_retain_unacquired_enhancement_fixedness_endpoint_and_comparison_limits():
    ref=detail(Curriculum(),resolve('ra.mri-crohn'))['radiology_reference'];steps=ref['walkthrough']['steps']
    for index in [0,2,3,4]:assert 'unassessed' in str(steps[index]['normal'])
    assert 'No small-bowel wall thickening or abnormal enhancement' not in str(steps[0]['normal'])
    assert 'No mesenteric inflammation; no interval change' not in str(steps[4]['normal'])
    assert 'unavailable' in str(steps[4]['normal'])
    assert 'missing temporal evidence' in steps[2]['look']
    assert 'dedicated perianal assessment' in steps[3]['tip']
    assert 'Histological fibrosis is not quantified' in steps[1]['findings'][1]
    assert 'quantify fibrosis' in steps[1]['tip'] and 'ADC/source context' in steps[1]['look']
    assert len(ref['reporting']['sources'])==3
    assert any('Communicate abscess' in s for s in ref['reporting']['escalation'])
