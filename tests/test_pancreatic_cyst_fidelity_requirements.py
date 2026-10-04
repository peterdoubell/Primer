"""Cyst morphology must not substitute for fine anatomy, histology or an operative decision."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest

ROOT=Path(__file__).resolve().parents[1];ID='ra.pancreatic-cysts'


def inventory():
    d=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());i=next(r for r in d['investigations'] if r['investigation_id']==ID)
    return {**d,'investigations':[i],'scope':{'catalog_investigation_ids':[ID]}},i


def test_cyst_scope_keeps_every_reporting_section_and_fine_source_target():
    d,i=inventory();r=detail(Curriculum(),resolve(ID))['radiology_reference'];validate_reporting_snapshots(d,{ID:r['reporting']})
    assert i['source_contract_sha256']==digest({k:r.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    leaves={r['id']:r for r in requirements_for(i)};assert len(leaves)==183
    for target in ['wall.inner_boundary','septa.septal_junctions','mural_nodule.wall_attachment','mural_nodule.subtraction_artifact_check',
                   'main_duct.maximal_calibre_plane','communication.whole_connection_course','communication.uncertain_or_nonvisualized_interface',
                   'vascular_context.source_lumen_wall','mri.thin_mrcp_source_duct','presumed_mcn.region_of_diagnostic_uncertainty']:
        assert 'pancreatic_cyst.'+target in leaves
    assert {r['checklist_index'] for s in i['structures'] for r in s['report_refs']}==set(range(5))


def test_parent_and_normal_models_cannot_supply_cyst_or_positive_nodule_features():
    d,i=inventory();r=audit(d,{'assets':[{'id':'parent','kind':'model','investigation_ids':[ID],
        'structure_ids':['pancreatic_cyst.pancreas','pancreatic_cyst.wall']}]},expected_catalog_ids={ID})
    assert r['representation_requirements']==549 and r['counts']=={'verified':0,'unverified':0,'missing':549}
    leaves={r['id']:r for r in requirements_for(i)}
    for target in ['mural_nodule.source_enhancing_tissue','presumed_mcn.complete_observation','content.solid_debris']:
        assert 'source_context_purpose_mismatch' in inspect_binding({'kind':'clinical_image','modality':'MRI','source_context':{'depicted_state':'normal_anatomy'}},leaves['pancreatic_cyst.'+target])
    assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding({'kind':'clinical_image','modality':'CT'},leaves['pancreatic_cyst.mri.thin_mrcp_source_duct'])


def test_ipmn_framework_and_diagnostic_uncertainty_are_visible_in_effective_reader():
    r=detail(Curriculum(),resolve(ID))['radiology_reference']
    assert r['reporting']['classification']['version']=='Kyoto 2024'
    assert 'Presumed IPMN' in r['reporting']['classification']['applicability']
    assert 'complete guideline' in r['reporting']['classification']['summary']
    steps=r['walkthrough']['steps']
    assert 'Kyoto 2024' in steps[2]['findings'][0] and 'at least 5 mm' in steps[2]['findings'][0]
    assert '5 to under 10 mm' in steps[3]['findings'][1] and 'at least 10 mm' in steps[3]['findings'][1]
    assert 'not a diagnosis from communication alone' in steps[3]['findings'][0]
    assert 'no automatic treatment decision' in steps[2]['tip']


def test_shared_curriculum_retains_named_criteria_and_avoids_type_only_surgery():
    n=Curriculum().nodes['rad.5.pancreas-tumour'];q=n['quiz']
    assert '2017 international consensus' in q[1]['prompt'] and q[1]['answer']=='3'
    assert 'not present this as the complete Kyoto 2024' in q[1]['explain']
    assert 'diagnostic confidence' in q[7]['answer']
    assert 'rather than automatic resection' in q[8]['answer']
    assert 'below 40 mm' in q[8]['explain']
    assert not any(m['code']=='Main pancreatic duct > 8 mm' for m in n['reference']['modifiers'])
    assert any('Kyoto 2024' in m['meaning'] and 'calibre alone does not prove malignancy' in m['meaning'] for m in n['reference']['modifiers'])


def test_corrected_acute_report_override_actually_delivers_primary_sources():
    guide=detail(Curriculum(),resolve('ra.ct-pancreatitis'))['radiology_reference']['reporting']
    urls={s['url'] for s in guide['sources']}
    assert 'https://pubmed.ncbi.nlm.nih.gov/23100216/' in urls
    assert 'https://gastro.org/clinical-guidance/management-of-pancreatic-necrosis/' in urls
    assert guide['reviewed_at']=='2026-10-04'
    assert any('Fluid-responsive hypotension alone' in p for p in guide['pitfalls'])
