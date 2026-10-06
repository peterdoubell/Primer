"""Cardiac mass patterns and normal generic geometry cannot substitute for actual lesion evidence."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import audit,requirements_for,validate_reporting_snapshots
ROOT=Path(__file__).resolve().parents[1];IDENT='ra.cardiac-masses'
def test_each_lesion_attachment_mimic_and_reporting_field_is_required():
    data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(i for i in data['investigations'] if i['investigation_id']==IDENT);ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];single={**data,'scope':{**data['scope'],'catalog_investigation_ids':[IDENT]},'investigations':[item]}
    assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')});validate_reporting_snapshots(single,{IDENT:ref['reporting']})
    assert len(item['structures'])==67 and len(requirements_for(item))==588 and {r['checklist_index'] for s in item['structures'] for r in s['report_refs']}==set(range(5))
    ids={r['id'] for r in requirements_for(item)}
    for suffix in ['left_appendage.each_attachment_or_invasive_interface','mitral_valve.unresolved_thin_or_uncovered_boundary','left_papillary_chordal.each_resolved_chordal_course',
        'coumadin_ridge.each_source_resolved_attachment','crista_terminalis.relation_to_adjacent_wall_valve_or_vessel','chiari_network.every_unresolved_or_variant_part',
        'thrombus.each_solid_fluid_fat_blood_fibrous_or_calcific_component','myxoma.every_attachment_stalk_or_base','metastasis.clinical_operative_or_pathology_correspondence',
        'enhancement.organised_thrombus_enhancement_uncertainty','mixing_artefact.missing_or_uncovered_followup','effects.clinical_pressure_or_tamponade_evidence','spread.unresolved_or_unexamined_sites']:
        assert 'cardiac_mass.'+suffix in ids
    result=audit(single,{'assets':[{'id':'generic-normal-heart','kind':'model','investigation_ids':[IDENT],'structure_ids':['cardiac_mass.left_atrium','cardiac_mass.myxoma']}]},expected_catalog_ids={IDENT})
    assert result['counts']=={'verified':0,'unverified':0,'missing':1764} and item['clinical_validation_status'].startswith('draft_')
def test_diagnosis_function_and_unperformed_tests_are_not_normal_presets():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];s=ref['walkthrough']['steps'];r=ref['reporting']
    assert all(e['normal']=={} for e in s)
    assert 'not automatic histology' in s[0]['tip'] and 'actual measurement plane/phase' in s[1]['tip']
    assert 'organised chronic thrombus may rarely enhance peripherally' in s[3]['tip']
    assert 'obtained adequately assessed acquisitions' in s[3]['findings'][0] and 'remains uncertain' in s[3]['findings'][2]
    assert 'does not contain the actual mass' in ref['walkthrough']['spatial_model']['reporting_aim']
    assert any('FDG uptake' in p and 'not' in p for p in r['pitfalls']) and r['escalation']
def test_noncommercial_source_images_and_clinical_approval_are_not_borrowed():
    p=json.loads((ROOT/'docs/cardiac-mass-source-review.json').read_text());rows={r['pmcid']:r for r in p['sources']}
    assert rows['PMC10818366']['actual_license']=='CC BY 4.0' and rows['PMC9558634']['actual_license']=='CC BY-NC-SA 4.0'
    assert all(not r['images_reused'] and not r['anatomical_approval'] for r in rows.values()) and not p['clinical_approval'] and not p['structure_coverage_granted']
