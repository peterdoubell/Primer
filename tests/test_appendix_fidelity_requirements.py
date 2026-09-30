import json
from pathlib import Path

from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for,inspect_binding,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest,build_report,build_scope

ROOT=Path(__file__).resolve().parents[1]

def inventory():
    return json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())


def test_appendix_scope_matches_the_complete_effective_reporting_contract():
    data=inventory();inv=data['investigations'][0]
    ref=detail(Curriculum(),resolve('ra.appendicitis'))['radiology_reference']
    validate_reporting_snapshots(data,{'ra.appendicitis':ref['reporting']})
    contract={k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')}
    assert inv['source_contract_sha256']==digest(contract)
    leaves={r['id']:r for r in requirements_for(inv)}
    assert len(leaves)==56
    for key in ['abdomen.appendix.tip','abdomen.appendix.submucosa','abdomen.mesenteric_nodes.individual_nodes',
                'abdomen.right_ureter_appendix_workup.distal','pelvis.left_adnexa_appendix_workup.ovary',
                'abdomen.appendectomy_stump.remnant','abdomen.appendiceal_collection.adjacent_structures']:
        assert key in leaves
    assert inv['source_scope_issues'] and inv['expansion_rules']
    assert len(inv['functional_evidence_requirements'])==4


def test_ct_and_normal_anatomy_cannot_replace_us_layers_or_perforation_evidence():
    leaves={r['id']:r for r in requirements_for(inventory()['investigations'][0])}
    ct={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy','laterality':'left'}}
    assert any('modality' in issue for issue in inspect_binding(ct,leaves['abdomen.appendix.submucosa']))
    assert 'source_context_purpose_mismatch' in inspect_binding(ct,leaves['abdomen.appendiceal_perforation.wall_defect'])
    assert 'source_context_laterality_mismatch' in inspect_binding(ct,leaves['pelvis.right_adnexa_appendix_workup.ovary'])


def test_inventory_does_not_award_existing_generic_models_any_anatomical_credit():
    report=build_report(build_scope())
    extra=report['additional_structure_audit']
    assert extra['representation_requirements']==168
    assert extra['counts']=={'verified':0,'unverified':3,'missing':165}
    assert not extra['clinical_commercial_ready']
    assert report['total_representation_requirements'] is None
