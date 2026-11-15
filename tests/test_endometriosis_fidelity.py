"""Endometriosis source views cannot become native geometry, calibrated data or current findings."""
import hashlib,json
from pathlib import Path
from PIL import Image
from pypdf import PdfReader
from pypdf.generic import IndirectObject
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_msk_fidelity import requirements_for,validate_reporting_snapshots,audit
from tools.check_radiology_fidelity import digest
ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/'docs/endometriosis-source-review'
INV='ra.mri-endometriosis';PREFIX='open-endometriosis-esur-2025-'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def reference():return detail(Curriculum(),resolve(INV))['radiology_reference']

def test_original_pdf_image_objects_and_all_native_samples_match_runtime():
 proof=json.loads((REVIEW/'published-source-preservation.json').read_text());pdf=(REVIEW/'original-article.pdf').read_bytes()
 assert sha(pdf)==proof['original_PDF_sha256'] and not proof['source_pixels_modified']
 assert sha((REVIEW/'original-article.xml').read_bytes())==proof['original_XML_sha256']
 assert sha((REVIEW/'original-metadata.json').read_bytes())==proof['original_metadata_sha256']
 assert proof['publisher_XML_PDF_MD5_verified'] and 'creativecommons.org/licenses/by/4.0/' in proof['permissions_xml']
 assert not proof['clinical_approval'] and not proof['complete_reporting_anatomy_approved'] and not proof['native_3D_geometry_supplied']
 rows=reference()['structure_atlas'];assert len(rows)==18 and sum(r['kind']=='schematic' for r in rows)==13
 reader=PdfReader(REVIEW/'original-article.pdf')
 for record,row in zip(proof['figures'],rows):
  assert row['id']==record['id']
  raw=(ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes();assert sha(raw)==record['sha256']==row['sha256']
  obj=reader.get_object(IndirectObject(record['source_PDF_object'],0,reader))
  assert record['source_PDF_object'] in {r.idnum for r in reader.pages[record['source_PDF_page']-1]['/Resources']['/XObject'].values()}
  with Image.open(ROOT/'web'/row['src'].removeprefix('/app/')) as im:
   im.load();assert list(im.size)==record['dimensions']==[obj['/Width'],obj['/Height']]
   assert sha(im.tobytes())==record['decoded_pixel_sha256']
   if str(obj['/Filter'])=='/DCTDecode':assert raw==obj._data
   else:assert im.tobytes()==obj.get_data()
  assert row['license']=='CC BY 4.0' and not row['source_context']['biological_3d_model_created_from_artwork']


def test_cases_mri_photographs_surgery_and_caption_conflicts_stay_separate():
 rows={r['id'].removeprefix(PREFIX):r for r in reference()['structure_atlas']}
 assert rows['fig3']['source_context']['source_case_groups']=={'29_year_woman':['a','b'],'27_year_woman':['c','d']}
 assert 'displayed axial panel is d' in rows['fig3']['source_context']['source_scope_issue']
 assert '(&^HJYUa)' in rows['fig5']['source_caption_full']
 assert set(rows['fig5']['source_context']['source_case_groups'])=={'rectal_case_age_not_supplied','different_multifocal_case_age_not_supplied'}
 assert rows['fig4']['source_context']['population']['contains_source_adolescent_case']
 assert rows['fig4']['clinical_panels']==list('abcdefghij')
 assert rows['fig4']['source_context']['panel_types']['k']=='Clinical photograph'
 assert rows['fig6']['clinical_panels']==list('abcdefhi')
 assert rows['fig6']['source_context']['panel_types']['g']=='Clinical photograph'
 assert rows['fig6']['source_context']['panel_types']['j']=='Endoscopy'
 assert 'spans extra-pelvic rows' in rows['table2-l']['source_context']['source_scope_issue']
 for row in rows.values():
  assert not row['source_context']['different_figures_assumed_same_patient']
  assert not row['source_context']['native_acquisition_arrays_included']
  assert not row['source_context']['independent_calibrated_measurements_verified']


def test_all_report_steps_insert_assessment_prompts_and_only_their_source_figures():
 ref=reference();assert not ref['key_images'];w=ref['walkthrough']
 assert w['preset_mode']=='assessment-prompts' and len(w['steps'])==7
 assert 'kidney' in ' '.join(ref['reporting']['protocol'])
 ids={r['id'] for r in ref['structure_atlas']}
 for step in w['steps']:
  for prompt in step['normal'].values():assert '[__]' in prompt and 'Unassessed or unresolved' in prompt
  assert not any(' normal' in p.lower() or 'no bowel involvement' in p.lower() for p in step['normal'].values())
  assert set(step['images'])<=ids and step['images']
  assert not step['parts']
 assert w['start']['module_illustrations'] is False
 assert 'conceptual orientation only' in ref['spatial_model']['reporting_aim']
 assert len(ref['source_anatomy_references'])==1
 assert ref['source_anatomy_references'][0]['atlas']=='hra-female-pelvis-v1.10'
 assert ref['source_anatomy_references'][0]['initial_cropped'] is False
 # The same broad lesson also hosts other examinations; their effective scoped contracts remain separate.
 for inv in ['ra.mri-cervical-cancer','ra.mri-endometrial-cancer']:
  other=detail(Curriculum(),resolve(inv))['radiology_reference']
  assert other['reporting']!=ref['reporting']
  assert not any(r['id'].startswith(PREFIX) for r in other['structure_atlas'])


def test_full_named_scope_retains_every_fine_layer_side_and_unknown_extent():
 data=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text());item=next(i for i in data['investigations'] if i['investigation_id']==INV);ref=reference()
 validate_reporting_snapshots({**data,'investigations':[item]},{INV:ref['reporting']})
 assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
 leaves={r['id'] for r in requirements_for(item)};assert len(item['structures'])==190 and len(leaves)==877
 for side in ['left','right']:
  for suffix in ['adnexa.tube_ampulla.source_resolution_unresolved_or_unacquired_extent','ligament.proximal_uterosacral_ligament.adjacent_tissue_or_organ_interface','urinary_layer.ureter_outer_wall_periureteral_interface.thickness_or_explicitly_unresolved_layer','neural.S3_root_or_branch.source_origin_endpoints_or_boundaries']:
   assert 'endometriosis.'+side+'.'+suffix in leaves
 for suffix in ['bowel_layer.low_rectum.submucosa.source_inner_and_outer_boundaries','central.uterine_junctional_zone.source_resolution_unresolved_or_unacquired_extent','extra_pelvic.covered_diaphragm_and_pleural_peritoneal_interfaces.adjacent_tissue_or_organ_interface']:
  assert 'endometriosis.'+suffix in leaves
 scoped={**data,'investigations':[item],'scope':{'catalog_investigation_ids':[INV]}}
 result=audit(scoped,{'assets':[{'id':'gross-only','kind':'model','investigation_ids':[INV],'structure_ids':['endometriosis.central.uterus_covered_body_and_orientation']}]},expected_catalog_ids={INV})
 assert result['representation_requirements']==2631 and result['counts']['missing']==2631
 assets=[a for a in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if a['id'].startswith(PREFIX)]
 assert len(assets)==18 and all(a['anatomical_review']['status']=='pending' and not a['requirement_coverage'] for a in assets)
 hold=json.loads((REVIEW/'held-legacy-and-native-candidates.json').read_text());assert len(hold['legacy_remote_images'])==2 and not hold['native_model_published']


def test_malformed_table_identifiers_cannot_be_published(monkeypatch):
 import copy
 import pytest
 from primer import radiology_catalog as catalog
 original=catalog._read
 base=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())
 for field,value in [('source_table',0),('source_table',True),('source_table','2'),('source_table_panel','not-a-source-panel')]:
  data=copy.deepcopy(base);row=next(r for r in data[INV] if r.get('source_table'));row[field]=value
  monkeypatch.setattr(catalog,'_read',lambda name,*args,**kwargs: data if name=='radiology-open-images.json' else original(name,*args,**kwargs))
  catalog._structure_atlases.cache_clear()
  with pytest.raises(ValueError,match='Source table artwork'):catalog._structure_atlases()
 monkeypatch.setattr(catalog,'_read',original);catalog._structure_atlases.cache_clear()
