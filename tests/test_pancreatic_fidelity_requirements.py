import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1];ID='ra.ct-pancreatic-cancer'


def inventory():
    d=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());i=next(r for r in d['investigations'] if r['investigation_id']==ID)
    return {**d,'investigations':[i],'scope':{'catalog_investigation_ids':[ID]}},i


def test_pancreatic_scope_retains_ducts_vessel_branches_and_full_reporting_contract():
    d,i=inventory();ref=detail(Curriculum(),resolve(ID))['radiology_reference'];validate_reporting_snapshots(d,{ID:ref['reporting']})
    assert i['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    leaves={r['id']:r for r in requirements_for(i)};assert len(leaves)==253
    for target in ('whole_pancreas.uncinate','main_pancreatic_duct.cutoff_interface','biliary_outflow.intrapancreatic_cbd',
                   'sma.wall','common_hepatic_artery.branch_junctions','arterial_variants.replaced_right_hepatic',
                   'arterial_contact.orthogonal_plane','venous_contact.proximal_patency','venous_contact.distal_patency',
                   'venous_tributaries.first_jejunal_vein','local_tissue_planes.transverse_mesocolon','local_tissue_planes.mesenteric_root',
                   'regional_nodes.regional_status_source_map','treated_context.fibrosis_uncertain_region'):
        assert 'pancreatic_ca.'+target in leaves
    assert {r['checklist_index'] for s in i['structures'] for r in s['report_refs']}==set(range(5))


def test_parent_pancreas_or_generic_vessels_cannot_cover_fine_scope():
    d,_=inventory();r=audit(d,{'assets':[{'id':'gross-pancreas','kind':'model','investigation_ids':[ID],
        'structure_ids':['pancreatic_ca.whole_pancreas','pancreatic_ca.sma','pancreatic_ca.portal_vein']}]},expected_catalog_ids={ID})
    assert r['representation_requirements']==759 and r['counts']=={'verified':0,'unverified':0,'missing':759}
    assert not r['clinical_commercial_ready']


def test_normal_atlas_cannot_supply_positive_contact_or_metastatic_disease():
    _,i=inventory();leaves={r['id']:r for r in requirements_for(i)}
    asset={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}}
    for target in ('primary_observation.whole_margin','arterial_contact.circumferential_sector','venous_contact.occluded_lumen',
                   'suspected_neural_spread.source_tissue_extent','hepatic_spread.whole_margin','treated_context.residual_primary_region'):
        assert 'source_context_purpose_mismatch' in inspect_binding(asset,leaves['pancreatic_ca.'+target])


def test_mri_adjunct_does_not_borrow_ct_or_static_signal():
    _,i=inventory();leaves={r['id']:r for r in requirements_for(i)}
    asset={'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'pancreatic_mri_adjunct'}}
    for target in ('mri_adjunct.dwi_regions','mri_adjunct.adc_regions','mri_adjunct.duct_regions','mri_adjunct.liver_regions'):
        row=leaves['pancreatic_ca.'+target];assert row['modality_scope']==['MRI']
        assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset,row)


def test_walkthrough_keeps_source_descriptors_separate_from_operative_and_microscopic_claims():
    steps=detail(Curriculum(),resolve(ID))['radiology_reference']['walkthrough']['steps']
    assert 'Do not assign resectability' in steps[1]['look']
    assert 'framework/version and treatment time point' in steps[1]['tip']
    assert 'proximal/distal segments' in steps[2]['look']
    assert 'multidisciplinary surgical assessment' in steps[2]['look']
    assert 'not by itself proof of viable tumour' in steps[2]['tip']
    assert 'does not establish microscopic invasion' in steps[3]['findings'][2]


def test_curriculum_overview_does_not_contradict_measured_reader_descriptors():
    node=Curriculum().nodes['rad.5.pancreas-tumour'];ref=node['reference']
    assert 'raises concern' in ref['approach'][3]['detail']
    assert 'perpendicular to the vessel' in ref['measure'][0]['how']
    assert 'not a complete current NCCN/DPCG algorithm' in ref['classify']['note']
    assert not any(row[2] in ['Upfront surgery','Non-surgical management'] for row in ref['classify']['rows'])
    plate=next(p for p in node['lesson_media'] if p['id']=='rad-5-pancreas-tumour-reasoning-plate')
    assert 'multidisciplinary' in plate['caption']
    assert 'determine resectability' not in plate['caption']


def test_vascular_quiz_context_and_numeric_plane_do_not_reintroduce_automatic_surgery():
    q=Curriculum().nodes['rad.5.pancreas-tumour']['quiz']
    assert 'Before treatment' in q[2]['prompt'] and 'NCCN-style anatomical' in q[2]['prompt']
    assert 'multidisciplinary team' in q[2]['prompt']
    assert 'perpendicular to the SMA' in q[5]['prompt'] and q[5]['answer']=='120'
    assert 'does not establish histological invasion' in q[5]['explain']
    assert 'do not alone prove technical feasibility' in q[6]['explain']
