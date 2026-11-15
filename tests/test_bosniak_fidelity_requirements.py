import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1];ID='ra.renal-cysts-bosniak'


def inventory():
    d=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());i=next(r for r in d['investigations'] if r['investigation_id']==ID)
    return {**d,'investigations':[i],'scope':{'catalog_investigation_ids':[ID]}},i


def test_bosniak_scope_keeps_whole_wall_individual_septa_and_nodule_interfaces():
    d,i=inventory();ref=detail(Curriculum(),resolve(ID))['radiology_reference'];validate_reporting_snapshots(d,{ID:ref['reporting']})
    assert i['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    leaves={r['id']:r for r in requirements_for(i)};assert len(leaves)==163
    for target in ('wall.inner_surface','wall.outer_surface','wall.maximal_thickness','septa.first_wall_attachment',
                   'septa.second_wall_attachment','septa.count_identity','protrusions.attachment_base','protrusions.acute_interface',
                   'protrusions.obtuse_interface','protrusions.perpendicular_size','observation.enhancing_tissue_fraction'):
        assert 'bosniak.'+target in leaves
    assert {r['checklist_index'] for s in i['structures'] for r in s['report_refs']}==set(range(5))


def test_generic_cyst_shell_cannot_cover_septa_nodules_or_whole_reporting_scope():
    d,_=inventory();result=audit(d,{'assets':[{'id':'generic-shell','kind':'model','investigation_ids':[ID],
                      'structure_ids':['bosniak.wall','bosniak.observation','bosniak.septa','bosniak.protrusions']}]},expected_catalog_ids={ID})
    assert result['representation_requirements']==489
    assert result['counts']=={'verified':0,'unverified':0,'missing':489}
    assert not result['clinical_commercial_ready']


def test_mri_subtraction_and_t1_exception_cannot_borrow_ct():
    _,i=inventory();leaves={r['id']:r for r in requirements_for(i)}
    asset={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'cystic_renal_mri_feature'}}
    for target in ('mri_subtraction.subtraction','mri_t1.fat_saturated','mri_t2.fluid_signal','mri_iif_exception.heterogeneous_regions'):
        row=leaves['bosniak.'+target];assert row['modality_scope']==['MRI']
        assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset,row)


def test_normal_kidney_cannot_supply_positive_wall_septa_or_nodules():
    _,i=inventory();leaves={r['id']:r for r in requirements_for(i)}
    asset={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    for target in ('wall.enhancing_regions','septa.enhancing_regions','protrusions.enhancing_tissue','case_iv.category_driving_feature'):
        assert 'source_context_purpose_mismatch' in inspect_binding(asset,leaves['bosniak.'+target])


def test_walkthrough_enhancement_and_iif_shortcuts_are_qualified():
    ref=detail(Curriculum(),resolve(ID))['radiology_reference'];steps=ref['walkthrough']['steps']
    assert 'unequivocally visible' in steps[1]['look']
    assert 'same technique' in steps[1]['look']
    assert 'unenhanced CT' in steps[1]['findings'][1]
    assert 'smooth enhancing septa' in steps[2]['findings'][2]
    assert 'septum' in steps[2]['findings'][2]
    assert 'if no enhancing nodule' in steps[2]['findings'][3]
    assert 'hereditary RCC' in ref['reporting']['classification']['applicability']
    assert any('fat-suppressed T1 MRI' in s for s in steps[1]['findings'])
