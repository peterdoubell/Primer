"""Acute pancreatitis requires actual case anatomy and clinical/maturity evidence."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1];ID='ra.ct-pancreatitis'


def inventory():
    d=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
    i=next(r for r in d['investigations'] if r['investigation_id']==ID)
    return {**d,'investigations':[i],'scope':{'catalog_investigation_ids':[ID]}},i


def test_full_report_contract_and_acute_complication_targets_are_retained():
    d,i=inventory();r=detail(Curriculum(),resolve(ID))['radiology_reference'];validate_reporting_snapshots(d,{ID:r['reporting']})
    assert i['source_contract_sha256']==digest({k:r.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    leaves={r['id']:r for r in requirements_for(i)};assert len(leaves)==258
    for target in ['whole_pancreas.uncinate','necrosis.gland_preserved_extrapancreatic_necrosis','spaces.transverse_mesocolon',
                   'collection.incomplete_wall_regions','collection.solid_debris','infection_context.possible_fistula_path',
                   'splenic_vein.collateral_connection','pseudoaneurysm.arterial_neck','bleeding.delayed_spread_region',
                   'disruption.source_viable_upstream_gland','bowel.source_perfusion_region','intervention.stent_course']:
        assert 'pancreatitis.'+target in leaves
    assert {r['checklist_index'] for s in i['structures'] for r in s['report_refs']}==set(range(5))


def test_parent_normal_pancreas_cannot_cover_necrosis_collections_or_vascular_complications():
    d,i=inventory();r=audit(d,{'assets':[{'id':'gross-pancreas','kind':'model','investigation_ids':[ID],
        'structure_ids':['pancreatitis.whole_pancreas','pancreatitis.collection']}]},expected_catalog_ids={ID})
    assert r['representation_requirements']==774 and r['counts']=={'verified':0,'unverified':0,'missing':774}
    assert r['clinical_commercial_ready'] is False
    leaves={r['id']:r for r in requirements_for(i)}
    for key in ['necrosis.pancreatic_necrotic_extent','walled_off_necrosis.actual_wall_or_absence','pseudoaneurysm.sac_margin']:
        assert 'source_context_purpose_mismatch' in inspect_binding({'kind':'clinical_image','modality':'CT','source_context':{'depicted_state':'normal_anatomy'}},leaves['pancreatitis.'+key])


def test_conditional_mri_and_ultrasound_cannot_borrow_ct_visibility():
    _,i=inventory();leaves={r['id']:r for r in requirements_for(i)}
    for key,modality in [('mri.mr_duct_course','MRI'),('ultrasound.distal_duct_if_visible','Ultrasound')]:
        row=leaves['pancreatitis.'+key];assert row['modality_scope']==[modality]
        assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding({'kind':'clinical_image','modality':'CT'},row)


def test_maturity_and_clinical_severity_do_not_reintroduce_calendar_or_imaging_shortcuts():
    node=Curriculum().nodes['rad.5.pancreas-acute'];q=node['quiz'];ref=node['reference']
    assert 'local complication' in q[3]['answer'] and 'without documented persistent organ failure' in q[3]['answer']
    assert 'Fluid-responsive hypotension alone does not establish' in q[3]['explain']
    assert q[4]['kind']=='choice' and 'reaching day 28 alone will not establish' in q[4]['answer']
    assert 'automatic day-28 switch' in ref['classify']['note']
    assert 'multidisciplinary assessment' in q[0]['answer']
    assert 'Routine CT-guided needle aspiration is unnecessary' in q[7]['explain']
    steps=detail(Curriculum(),resolve(ID))['radiology_reference']['walkthrough']['steps']
    assert 'does not automatically become' in steps[1]['tip']
    assert 'possible enteric fistula' in steps[1]['findings'][-1]
    assert 'raise concern' in steps[3]['findings'][0]


def test_positive_fine_features_cannot_borrow_normal_anatomy_context():
    _,i=inventory();leaves={r['id']:r for r in requirements_for(i)}
    for target,modality in [('splenic_vein.filling_defect_region','CT'),('biliary.actual_duct_stone','CT'),('ultrasound.stones_or_sludge','Ultrasound'),('mri.t1_haemorrhagic_regions','MRI')]:
        assert 'source_context_purpose_mismatch' in inspect_binding({'kind':'clinical_image','modality':modality,'source_context':{'depicted_state':'normal_anatomy'}},leaves['pancreatitis.'+target])
