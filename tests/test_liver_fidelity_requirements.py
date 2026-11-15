import json
from pathlib import Path
import pytest
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import audit, inspect_binding, requirements_for, validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]


def inventory(identifier):
    d = json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    i = next(x for x in d['investigations'] if x['investigation_id'] == identifier)
    return {**d, 'investigations': [i], 'scope': {'catalog_investigation_ids': [identifier]}}, i


@pytest.mark.parametrize('identifier,count,prefix', [('ra.liver-masses',246,'liver_mass'),('ra.liver-lirads',210,'lirads')])
def test_full_liver_reporting_contract_and_conditional_anatomy_are_retained(identifier,count,prefix):
    d,i = inventory(identifier); ref = detail(Curriculum(),resolve(identifier))['radiology_reference']
    validate_reporting_snapshots(d,{identifier:ref['reporting']})
    assert i['source_contract_sha256'] == digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    assert {r['checklist_index'] for s in i['structures'] for r in s['report_refs']} == set(range(5))
    leaves = {r['id']:r for r in requirements_for(i)}
    assert len(leaves) == count
    for target in ('segment_i.biliary_drainage','segment_iva.parenchymal_territory','segment_ivb.portal_supply',
                   'segment_viii.venous_boundaries','portal_anatomy.segmental_branches','hepatic_venous_anatomy.caudate_outflow',
                   'arterial_anatomy.accessory_replaced_branches','biliary_anatomy.variant_drainage',
                   'observation_extent.perfusion_vs_mass_interface','vascular_abnormality.enhancing_venous_tissue'):
        assert prefix+'.'+target in leaves
    assert len(i['functional_evidence_requirements']) == 8
    assert len(i['source_scope_issues']) == 5


@pytest.mark.parametrize('identifier,count,prefix', [('ra.liver-masses',246,'liver_mass'),('ra.liver-lirads',210,'lirads')])
def test_whole_liver_or_portal_parent_cannot_cover_all_segments_branches_and_lesions(identifier,count,prefix):
    d,_ = inventory(identifier)
    report = audit(d,{'assets':[{'id':'gross-liver','kind':'model','investigation_ids':[identifier],
        'structure_ids':[prefix+'.whole_liver',prefix+'.portal_anatomy',prefix+'.observation_extent']}]},expected_catalog_ids={identifier})
    assert report['representation_requirements'] == count*3
    assert report['counts'] == {'verified':0,'unverified':0,'missing':count*3}
    assert not report['clinical_commercial_ready']


def test_mri_only_liver_features_cannot_borrow_a_ct_source():
    _,i = inventory('ra.liver-lirads');leaves={r['id']:r for r in requirements_for(i)}
    asset={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'lirads_other_imaging_feature'}}
    for target in ('lirads.lrm_and_ancillary.targetoid_diffusion','lirads.lrm_and_ancillary.targetoid_transitional_hbp',
                   'lirads.lrm_and_ancillary.diffusion_restriction','lirads.mri_observation_features.adc_regions'):
        assert leaves[target]['modality_scope'] == ['MRI']
        assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset,leaves[target])


def test_normal_anatomy_cannot_supply_positive_observation_or_tumour_in_vein():
    asset={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    for identifier,prefix in [('ra.liver-masses','liver_mass'),('ra.liver-lirads','lirads')]:
        _,i=inventory(identifier);leaves={r['id']:r for r in requirements_for(i)}
        for target in ('observation_extent.whole_margin','vascular_abnormality.enhancing_venous_tissue',
                       'background_disease.steatotic_regions'):
            assert 'source_context_purpose_mismatch' in inspect_binding(asset,leaves[prefix+'.'+target])
    _,i=inventory('ra.liver-masses')
    assert any(s['id']=='liver_mass.case_fnh' for s in i['structures'])
    assert not any(s['id']=='liver_mass.major_feature_regions' for s in i['structures'])
    _,i=inventory('ra.liver-lirads')
    assert any(s['id']=='lirads.major_feature_regions' for s in i['structures'])
    assert any(s['id']=='lirads.treated_context' for s in i['structures'])
