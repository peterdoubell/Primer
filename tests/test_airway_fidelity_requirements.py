import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for,validate_reporting_snapshots,inspect_binding,audit
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1]


def inventory():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    inv=next(x for x in data['investigations'] if x['investigation_id']=='ra.ct-airways')
    return {**data,'investigations':[inv],'scope':{'catalog_investigation_ids':['ra.ct-airways']}},inv


def test_all_effective_airway_reporting_fields_and_common_segments_are_retained():
    data,inv=inventory();ref=detail(Curriculum(),resolve('ra.ct-airways'))['radiology_reference']
    validate_reporting_snapshots(data,{'ra.ct-airways':ref['reporting']})
    assert inv['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    leaves={x['id']:x for x in requirements_for(inv)}
    assert len(leaves)==229
    for key in ('airways.right_rb10.segmental_lumen_and_wall','airways.left_lb1_2.parenchymal_distribution',
                'airways.left_lb4.accompanying_arterial_branch','airways.trachea.posterior_membranous_wall',
                'airways.post_intervention.bronchial_stump','airways.congenital_variants.atretic_bronchial_segment'):
        assert key in leaves
    assert sum(s['id'].startswith('airways.right_rb') for s in inv['structures'])==10
    assert sum(s['id'].startswith('airways.left_lb') for s in inv['structures'])==8
    assert not any(s['id']=='airways.left_lb7' for s in inv['structures'])
    assert any(s['id']=='airways.left_segment_variants' for s in inv['structures'])
    assert len(inv['functional_evidence_requirements'])==5 and len(inv['source_scope_issues'])==4


def test_normal_prefill_does_not_assert_unacquired_expiration_is_negative():
    ref=detail(Curriculum(),resolve('ra.ct-airways'))['radiology_reference']
    normal=ref['walkthrough']['steps'][3]['normal']['EXPIRATORY FINDINGS']
    assert '[adequate / limited / not acquired]' in normal
    assert '[not assessed / none / distribution]' in normal
    assert 'no excessive central airway collapse' not in normal
    assert any('Expiratory imaging not acquired' in x for x in ref['walkthrough']['steps'][3]['findings'])


def test_static_parent_lung_cannot_cover_segments_or_positive_airway_disease():
    data,inv=inventory()
    result=audit(data,{'assets':[{'id':'whole-lung','kind':'model','investigation_ids':['ra.ct-airways'],'structure_ids':['airways.lobes_fissures']}]},expected_catalog_ids={'ra.ct-airways'})
    assert result['representation_requirements']==687
    assert result['counts']=={'verified':0,'unverified':0,'missing':687}
    leaves={x['id']:x for x in requirements_for(inv)}
    issues=inspect_binding({'kind':'clinical_image','modality':'MRI','source_context':{'depicted_state':'normal_anatomy','laterality':'right'}},leaves['airways.bronchiectasis.dilated_lumen'])
    assert 'source_context_purpose_mismatch' in issues
    assert 'clinical_image_modality_not_in_requirement_scope' in issues
    assert not result['clinical_commercial_ready']
