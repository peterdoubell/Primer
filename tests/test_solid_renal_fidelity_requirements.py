import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]
IDENTIFIER='ra.solid-renal-masses'


def inventory():
    d=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    i=next(row for row in d['investigations'] if row['investigation_id']==IDENTIFIER)
    return {**d,'investigations':[i],'scope':{'catalog_investigation_ids':[IDENTIFIER]}},i


def test_renal_reporting_and_bilateral_compartment_scope():
    d,i=inventory();ref=detail(Curriculum(),resolve(IDENTIFIER))['radiology_reference']
    validate_reporting_snapshots(d,{IDENTIFIER:ref['reporting']})
    assert i['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    leaves={r['id']:r for r in requirements_for(i)}
    assert len(leaves)==214
    for target in ('right_kidney.cortex','left_kidney.medulla','right_collecting_system.minor_calyces',
                   'left_collecting_system.urothelial_boundary','right_renal_arterial_supply.segmental_branches',
                   'left_renal_venous_drainage.variant_course','perinephric_compartment.posterior_renal_fascia',
                   'venous_tissue.ivc_retrohepatic','venous_tissue.diaphragmatic_interface','observation_extent.complete_margin'):
        assert 'renal_mass.'+target in leaves
    assert {r['checklist_index'] for s in i['structures'] for r in s['report_refs']}==set(range(5))


def test_parent_kidney_does_not_cover_fine_parts_or_lesions():
    d,_=inventory()
    result=audit(d,{'assets':[{'id':'gross-kidney','kind':'model','investigation_ids':[IDENTIFIER],
                  'structure_ids':['renal_mass.right_kidney','renal_mass.left_kidney','renal_mass.observation_extent']}]},expected_catalog_ids={IDENTIFIER})
    assert result['representation_requirements']==642
    assert result['counts']=={'verified':0,'unverified':0,'missing':642}
    assert not result['clinical_commercial_ready']


def test_ct_cannot_supply_mri_only_renal_features():
    _,i=inventory();leaves={r['id']:r for r in requirements_for(i)}
    asset={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'renal_mass_mri_feature'}}
    for target in ('t2_signal.target','chemical_shift.opposed_phase','subtraction.true_enhancement','diffusion.adc'):
        row=leaves['renal_mass.'+target]
        assert row['modality_scope']==['MRI']
        assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset,row)


def test_normal_renal_atlas_cannot_cover_positive_mass_or_thrombus():
    _,i=inventory();leaves={r['id']:r for r in requirements_for(i)}
    asset={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    for target in ('observation_extent.complete_margin','local_extension.sinus_fat','venous_tissue.enhancing_tissue','nodes.individual_margin'):
        assert 'source_context_purpose_mismatch' in inspect_binding(asset,leaves['renal_mass.'+target])


def test_fat_prompt_preserves_exceptions_and_microscopic_fat_distinction():
    ref=detail(Curriculum(),resolve(IDENTIFIER))['radiology_reference']
    step=ref['walkthrough']['steps'][1]
    assert 'favouring classic angiomyolipoma' in step['findings'][0]
    assert 'diagnostic of angiomyolipoma' not in step['findings'][0]
    assert 'rare RCC exceptions' in step['tip']
    assert 'Opposed-phase signal loss alone' in step['tip']
    assert any(s['url']=='https://pmc.ncbi.nlm.nih.gov/articles/PMC6980339/' for s in ref['reporting']['sources'])
