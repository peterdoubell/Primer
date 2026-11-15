"""Cervical MRI source scope cannot silently become patient findings or fine anatomy."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for,validate_reporting_snapshots,audit
from tools.check_radiology_fidelity import digest
ROOT=Path(__file__).resolve().parents[1];INV='ra.mri-cervical-cancer'
def reference():return detail(Curriculum(),resolve(INV))['radiology_reference']
def test_cervical_walkthrough_uses_complete_assessment_prompts_without_inferred_normality():
 r=reference();w=r['walkthrough'];assert w['preset_mode']=='assessment-prompts'
 assert len(w['steps'])==len(r['reporting']['checklist'])==8
 assert not r['key_images'] and w['start']['module_illustrations'] is False
 for s in w['steps']:
  assert not s['parts']
  for p in s['normal'].values():
   assert '[__]' in p and 'Unassessed or uncertain' in p
   assert 'no parametrial invasion' not in p.lower() and 'No suspicious' not in p
 assert 'conceptual orientation only' in r['spatial_model']['reporting_aim']
 assert r['reporting']['classification'] is None and r['reporting']['criteria_table'] is None
 assert any('microscopic stage IA' in p for p in r['reporting']['pitfalls'])
 assert any('detrusor involvement alone' in p for p in r['reporting']['pitfalls'])
 systems=r['cancer_staging'];assert len(systems)==1 and systems[0]['id']=='cervix-figo'
 assert '2018' in systems[0]['version'] and 'corrected IB' in systems[0]['version']
 # Other MRI examinations in the broad lesson retain their own scoped reporting.
 for inv in ['ra.mri-endometriosis','ra.mri-endometrial-cancer']:
  other=detail(Curriculum(),resolve(inv))['radiology_reference'];assert other['reporting']!=r['reporting']
def test_complete_named_scope_preserves_thin_interfaces_sides_nodes_and_unknown_extent():
 d=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());i=next(x for x in d['investigations'] if x['investigation_id']==INV);r=reference()
 validate_reporting_snapshots({**d,'investigations':[i]},{INV:r['reporting']})
 assert i['source_contract_sha256']==digest({k:r.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
 leaves={x['id'] for x in requirements_for(i)};assert len(i['structures'])==162 and len(leaves)==762
 for side in ['left','right']:
  for suffix in ['parametrial.sacrouterine_uterosacral_ligament_origin.source_origin_endpoints_or_boundaries','urinary_layer.ureter_outer_wall_periureteral_interface.thickness_or_explicitly_unresolved_layer','node_station.common_iliac.actual_covered_identity_and_extent','lesion.each_pelvic_sidewall_extension_or_proximity.source_measurement_plane_scale_and_uncertainty']:
   assert 'cervical_cancer.'+side+'.'+suffix in leaves
 for suffix in ['central_layer.source_visible_outer_low_signal_stromal_ring.source_inner_and_outer_boundaries','adjacent_layer.bladder.source_resolved_mucosal_luminal_interface.source_resolution_and_uncertainty','spread.actual_renal_vein_level_reference.source_origin_endpoints_or_boundaries','planning.internal_os_distance.internal_os_reference_identity']:
  assert 'cervical_cancer.'+suffix in leaves
 scoped={**d,'investigations':[i],'scope':{'catalog_investigation_ids':[INV]}}
 report=audit(scoped,{'assets':[{'id':'gross-reference','kind':'model','investigation_ids':[INV],'structure_ids':['cervical_cancer.central.cervical_stroma_covered_extent']}]},expected_catalog_ids={INV})
 assert report['representation_requirements']==2286 and report['counts']['missing']==2286

def test_native_atlas_is_separate_shared_source_context_with_no_tissue_or_patient_approval():
 r=reference();endo=detail(Curriculum(),resolve('ra.mri-endometriosis'))['radiology_reference']
 assert len(r['source_anatomy_references'])==1 and r['source_anatomy_references']==endo['source_anatomy_references']
 source=r['source_anatomy_references'][0];assert source['atlas']=='hra-female-pelvis-v1.10' and source['initial_cropped'] is False
 m=json.loads((ROOT/'web/anatomy'/source['atlas']/'manifest.json').read_text())
 assert not m['clinical_approval'] and not m['complete_reporting_anatomy_approved'] and not m['full_module_fidelity_approved']
 assert not source.get('patient_registration') and not source.get('source_volume')
 assert 'unverified' in source['population_note']
