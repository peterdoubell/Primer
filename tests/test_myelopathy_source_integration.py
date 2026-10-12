"""Independent source pixels/rights/context checks and no-coverage integration regressions."""
import copy
import hashlib
import io
import os
import subprocess
import sys
import json
from pathlib import Path
import urllib.parse
import xml.etree.ElementTree as ET

import pytest

from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.anatomy_sources import integrate_myelopathy_sources as integration
from tools.anatomy_sources import traumatic_registry_amendment as trauma_amendment
from tools.anatomy_sources import stroke_registry_amendment as stroke_amendment
from tools.pulmonary_data_compatibility import restore_prior_view
from tools.check_msk_fidelity import audit,inspect_binding,requirements_for,validate_reporting_snapshots
from tools.check_radiology_fidelity import digest
from tools.msk_runtime_rights import license_issues,audit_reference_image_rights

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/myelopathy-published-source-review-20261011'
INV='ra.mri-myelopathy'
SOURCE_SHA='ef78550db4d9aebf9cf3471f3467227b9ec626ea098229dbbb5734408695640a'
REVIEW_SHA='ac775f60d6011bca10099a6607da02e4d99ea9489e9868ff0cf3948c60cba1b1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

@pytest.fixture(scope='module')
def source():
 proof=json.loads((FOLDER/'original-source-review.json').read_text())
 rows=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())[INV]
 evidence=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())
 assets=[a for a in evidence['assets'] if INV in a.get('investigation_ids',[])]
 inventory=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())
 item=next(i for i in inventory['investigations'] if i['investigation_id']==INV)
 integration.clear_catalog_caches()
 ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference']
 return proof,rows,assets,item,ref


def test_exact_independent_source_set_hashes_and_complete_media_byte_bound(source):
 proof,rows,assets,item,ref=source
 review=json.loads((ROOT/'docs/myelopathy-independent-source-review-20261011.json').read_text())
 assert sha(FOLDER/'original-source-review.json')==SOURCE_SHA
 assert sha(ROOT/'docs/myelopathy-independent-source-review-20261011.json')==REVIEW_SHA
 assert review['held_source_row_ids']==[]
 assert {r['id'] for r in rows}==set(review['approved_source_rows_as_frozen'])
 assert len(rows)==len(assets)==25 and sum(r['kind']=='schematic' for r in rows)==3
 paths=[ROOT/r['packaged_path'] for r in proof['figures']]+[ROOT/a['packaged_original_PDF_path'] for a in proof['articles']]
 assert len(paths)==27 and sum(p.stat().st_size for p in paths)==8738864
 for row in rows:assert sha(ROOT/'web'/row['src'].removeprefix('/app/'))==row['sha256']
 assert all(license_issues(a,ROOT)==[] for a in assets)
 rights=audit_reference_image_rights({'surfaces':['reporting:'+INV],'images':[{'src':r['src'],'uses':[{'surface':'reporting:'+INV,'id':r['id']}]} for r in rows]}, {'assets':assets},ROOT)
 assert rights['rights_ready'] and all(r['status']=='cleared' for r in rights['images'])


def test_publisher_xml_pdf_checksums_channels_annotations_and_icc_independently(source):
 Image=pytest.importorskip('PIL.Image');PdfReader=pytest.importorskip('pypdf').PdfReader
 proof,rows,*_=source;by_id={r['id']:r for r in rows}
 for article in proof['articles']:
  folder=FOLDER/('source' if article['pmcid']=='PMC6108975' else 'source-mogad')
  meta=json.loads((folder/(article['pmcid']+'.1.json')).read_text())
  for key,extension in [('xml_url','.xml'),('pdf_url','.pdf')]:
   b=(folder/(article['pmcid']+'.1'+extension)).read_bytes()
   assert hashlib.md5(b).hexdigest()==urllib.parse.parse_qs(urllib.parse.urlparse(meta[key]).query)['md5'][0]
  xml=ET.parse(folder/(article['pmcid']+'.1.xml'));permissions=ET.tostring(xml.find('.//permissions'),encoding='unicode')
  assert 'https://creativecommons.org/licenses/by/4.0/' in permissions
  pdf=PdfReader(folder/(article['pmcid']+'.1.pdf'))
  for fact in [f for f in proof['figures'] if f['pmcid']==article['pmcid']]:
   obj=pdf.get_object(fact['PDF_object_id']);mode=fact['source_mode'];size=(int(obj['/Width']),int(obj['/Height']));color=obj['/ColorSpace'].get_object()
   if str(obj['/Filter'])=='/DCTDecode':
    original=Image.open(io.BytesIO(obj._data));original.load();samples=original.tobytes()
   else:samples=obj.get_data()
   image=Image.open(ROOT/fact['packaged_path']);image.load()
   assert image.mode==mode and image.size==size and image.tobytes()==samples
   assert hashlib.sha256(samples).hexdigest()==fact['decoded_source_channel_sha256']
   if isinstance(color,list) and color[0]=='/ICCBased':
    profile=color[1].get_object().get_data();assert len(profile)==3144 and image.info['icc_profile']==profile
    assert int.from_bytes(profile[64:68],'big')==0
    expected='/Perceptual' if article['pmcid']=='PMC6108975' else '/RelativeColorimetric'
    assert str(obj['/Intent'])==expected
   fig=xml.find('.//fig[@id="'+fact['figure_id']+'"]');assert fig is not None
   assert ' '.join(fig.find('caption').itertext())==fact['source_caption_full']
   assert fig.find('attrib') is None and fig.find('permissions') is None
  assert (ROOT/article['packaged_original_PDF_path']).read_bytes()==(folder/(article['pmcid']+'.1.pdf')).read_bytes()


def test_registered_context_is_typed_without_losing_original_source_facts(source):
 _,rows,assets,_,_=source;by_id={a['id']:a for a in assets}
 for row in rows:
  c=row['source_context'];a=by_id[row['id']]
  assert c==a['source_context']
  assert c['setting'] in {'in_vivo','unknown'} and c['laterality'] in {'left','right','bilateral','unknown'}
  assert c['population']['life_stage'] in {'adult','immature','unknown'}
  assert not c['current_patient_findings'] and not c['native_DICOM_or_volumetric_stack_supplied']
  catalog._validate_source_panel_roles(row)
  assert inspect_binding(a,{'modality_scope':['MRI'],'context_requirements':[]})==[]
  if row['kind']=='schematic':
   assert a['kind']=='schematic' and row['modality']=='Schematic'
   assert c['setting']==c['population']['life_stage']==c['laterality']=='unknown'
   assert c['original_setting']=='schematic' and c['population']['original_life_stage']=='not_applicable'
   assert all(key not in c for key in ['selected_panels','panel_types','panel_states'])
   assert all(key not in row for key in ['clinical_panels','schematic_panels'])
  else:
   assert row['clinical_panels']==c['selected_panels']==a['representation_selection']['panels']
   assert all(c['panel_types'][p]=='MRI' for p in c['selected_panels'])
  assert row['color_context']['standalone_browser_display_equivalence_verified'] is False
  assert row['original_publication_pdf']['unchanged_original']
  assert a['pixel_provenance']['source_pixels_changed'] is False
  assert a['source_context_original_proof_relation']['evidence_sha256']==SOURCE_SHA
 fig18=next(r for r in rows if r['id']=='open-myelopathy-moghaddam2018-fig18')
 assert fig18['source_context']['laterality']=='unknown'
 assert fig18['source_context']['source_burned_acquisition_panel_markers']['c']['text']=='LEFT T-7'
 assert fig18['source_context']['original_panel_types']['c']=='DSA'
 assert fig18['ancillary_panels'][0]['kind']=='Radiography' and fig18['ancillary_panels'][0]['source_subtype']=='Digital subtraction angiography'
 fig22=next(r for r in rows if r['id']=='open-myelopathy-moghaddam2018-fig22')
 assert fig22['clinical_panels']==['a','c','d','e'] and fig22['ancillary_panels'][0]['panels']==['b']
 mog=next(r for r in rows if r['id']=='open-myelopathy-mogad2025-fig1')
 assert mog['source_context']['anatomical_sites_from_article_case_text']==['C6-T10 spinal cord']
 assert 'C6-T10 spinal cord' not in mog['source_context']['anatomical_sites_from_source_caption']


@pytest.mark.parametrize('bad_panel,asset_id',[('c','open-myelopathy-moghaddam2018-fig18'),('c','open-myelopathy-moghaddam2018-fig19'),('c','open-myelopathy-moghaddam2018-fig20'),('b','open-myelopathy-moghaddam2018-fig22')])
def test_non_mri_ancillary_panels_cannot_be_promoted_to_selected_mri_evidence(source,bad_panel,asset_id):
 _,rows,assets,_,_=source;row=copy.deepcopy(next(r for r in rows if r['id']==asset_id));a=copy.deepcopy(next(a for a in assets if a['id']==asset_id));row['clinical_panels']=row['source_context']['selected_panels']=[bad_panel]
 with pytest.raises(ValueError,match='displayed modality'):catalog._validate_source_panel_roles(row)
 a['source_context']['selected_panels']=[bad_panel];a['representation_selection']['panels']=[bad_panel]
 assert 'source_context_selected_panel_modality_mismatch' in inspect_binding(a,{'modality_scope':['MRI']})


def test_known_side_and_pathology_constraints_reject_wrong_or_normal_reference(source):
 _,_,assets,item,_=source;leaves=requirements_for(item);left=next(r for r in leaves if r['laterality']=='left');a=copy.deepcopy(next(a for a in assets if a['id']=='open-myelopathy-moghaddam2018-fig4'))
 assert 'source_context_laterality_mismatch' in inspect_binding(a,left)
 disease=next(r for r in leaves if r['parent_id']=='myelopathy.condition.multiple_sclerosis')
 a['source_context']['depicted_state']='normal_anatomy';a['source_context']['panel_states']={p:'normal_anatomy' for p in a['source_context']['selected_panels']}
 assert 'source_context_purpose_mismatch' in inspect_binding(a,disease)


def test_exact_current_walkthrough_all_fields_and_pending_fine_obligations(source):
 _,rows,assets,item,ref=source
 validate_reporting_snapshots({'investigations':[item]},{INV:ref['reporting']})
 assert item['source_contract_sha256']==digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
 assert len(item['structures'])==231 and len(requirements_for(item))==2422
 assert len(item['shared_quiz_requirement_crosswalk'])==12 and len(item['report_template_walkthrough_crosswalk'])==36
 assert len(item['literal_named_source_scope_crosswalk'])==58
 for group in item['structures']:
  assert group['context_instantiation_rules']['purpose']=='pathology_or_anatomical_reference'
  assert set(group['context_requirements'])<= {'purpose'}
  assert group['modality_scope'] and set(group['modality_scope'])<= {'MRI','CT','Radiography'}
  assert group['site_instantiation_status']=='pending' and not group['clinical_approval']
 assert item['runtime_integrated'] is True and item['shared_inventory_or_evidence_mutated'] is True
 assert item['original_source_draft_shared_inventory_or_evidence_mutated'] is False
 assert item['full_source_named_scope_independently_audited'] is False
 walk=ref['walkthrough'];assert walk['preset_mode']=='assessment-prompts' and walk['start']['module_illustrations'] is False
 assert len(walk['steps'])==5
 used=set(walk['start']['images'])|{r for step in walk['steps'] for r in step['images']}
 assert used=={r['id'] for r in rows}
 for i,step in enumerate(walk['steps']):
  assert step['images']==integration.STEP_IMAGES[i] and step['parts']==[]
  assert all('[__]' in text for text in step['normal'].values())
 assert 'not acquired' in str(walk['steps'][3]['normal'])
 assert all(not a['structure_ids'] and not a['requirement_coverage'] and a['anatomical_review']['status']=='pending' for a in assets)
 report=audit({'investigations':[item],'scope':{'catalog_investigation_ids':[INV]},'clinical_validation_status':'draft'}, {'assets':assets},ROOT,expected_catalog_ids={INV})
 assert report['representation_requirements']==7266 and report['counts']=={'verified':0,'unverified':0,'missing':7266}
 assert report['clinical_commercial_ready'] is False


def test_source_guard_rejects_changed_proof_before_writing_data(tmp_path):
 (tmp_path/'docs').mkdir();(tmp_path/integration.INDEPENDENT_PATH).write_bytes((ROOT/integration.INDEPENDENT_PATH).read_bytes())
 f=tmp_path/integration.FOLDER;f.mkdir();(f/'original-source-review.json').write_bytes((FOLDER/'original-source-review.json').read_bytes()+b' ')
 with pytest.raises(ValueError,match='fingerprint differs'):integration.validate_approved_sources(tmp_path)
 assert not (tmp_path/'data').exists()


def test_unrelated_json_values_and_references_keep_frozen_semantics(source):
 receipt=json.loads((FOLDER/'integration-receipt.json').read_text());ids={r['id'] for r in source[1]}
 dep_path=FOLDER/'registry-additive-dependency-review.json';dependency=json.loads(dep_path.read_text()) if dep_path.exists() else None
 changes={r['id']:r for r in dependency['updated_assets']} if dependency else {}
 for file,expect in receipt['unrelated_data'].items():
  data=json.loads((ROOT/file).read_text());tokens=integration.unrelated_token_fingerprints((ROOT/file).read_text(),Path(file),ids)
  data,tokens=restore_prior_view(file,data,tokens)
  data,tokens=stroke_amendment.restore_prior_view(file,data,tokens)
  data,tokens=trauma_amendment.restore_prior_view(file,data,tokens)
  if file.endswith('radiology-open-images.json'):data={k:v for k,v in data.items() if k!=INV}
  elif file.endswith('radiology-asset-evidence.json'):
   data={**data,'assets':[copy.deepcopy(a) for a in data['assets'] if a['id'] not in ids]}
   for asset in data['assets']:
    if asset['id'] not in changes:continue
    record=changes[asset['id']];assert digest(asset)==record['current_asset_semantic_sha256']
    key='assets:'+asset['id'];assert tokens[key]==record['current_asset_value_token_sha256'];assert expect['unrelated_value_token_fingerprints'][key]==record['prior_asset_value_token_sha256']
    asset['presentation_dependencies']['data/radiology/radiology-open-images.json']=record['previous_registry_sha256']
    if record['prior_history_field_present']:asset['presentation_dependency_history']=record['prior_history']
    else:asset.pop('presentation_dependency_history',None)
    assert digest(asset)==record['prior_asset_semantic_sha256'];tokens[key]=record['prior_asset_value_token_sha256']
  elif file.endswith('non-msk-structure-requirements.json'):data={**data,'investigations':[i for i in data['investigations'] if i['investigation_id']!=INV],'scope':{**data['scope'],'catalog_investigation_ids':[i for i in data['scope']['catalog_investigation_ids'] if i!=INV]}}
  else:data={**data,'investigations':{k:v for k,v in data['investigations'].items() if k!=INV}}
  assert digest(data)==expect['unrelated_semantic_sha256']
  assert tokens==expect['unrelated_value_token_fingerprints']


def test_registered_source_images_pdfs_get_head_and_unknown_delivery(source,tmp_path):
 proof,rows,*_=source;requests={r['src']:{'sha256':r['sha256'],'bytes':(ROOT/'web'/r['src'].removeprefix('/app/')).stat().st_size,'pdf':False} for r in rows}
 for article in proof['articles']:
  url='/app/'+article['packaged_original_PDF_path'].removeprefix('web/');requests[url]={'sha256':article['original_PDF_sha256'],'bytes':article['packaged_original_PDF_bytes'],'pdf':True}
 env={k:v for k,v in os.environ.items() if not k.startswith('TURSO') and k not in {'VERCEL','VERCEL_ENV'}};env['PRIMER_DB']=str(tmp_path/'source-delivery.db');env['PRIMER_BACKUP_DIR']=str(tmp_path/'backups')
 script=r"""
import hashlib,json,os,sys
from fastapi.testclient import TestClient
import primer.server as server
requests=json.load(sys.stdin)
with TestClient(server.app) as client:
 for url,expect in requests.items():
  get=client.get(url,follow_redirects=False);head=client.head(url,follow_redirects=False)
  assert get.status_code==head.status_code==200,(url,get.status_code,head.status_code)
  assert len(get.content)==expect['bytes'] and hashlib.sha256(get.content).hexdigest()==expect['sha256']
  assert int(head.headers['content-length'])==expect['bytes'] and head.content==b''
  if expect['pdf']:assert get.headers['content-type'].startswith('application/pdf')
 for method in [client.get,client.head]:assert method('/app/reference-media/radiology-open/unknown-source.pdf',follow_redirects=False).status_code==404
 # The real app intentionally blocks an unconfigured production database.
 # Exercise this source handler's redirect contract in a minimal ASGI app;
 # production DB/auth fail-closed protections are tested independently.
 from fastapi import FastAPI
 delivery=FastAPI();delivery.add_api_route('/app/reference-media/radiology-open/{asset}',server.radiology_image_delivery,methods=['GET','HEAD'])
 os.environ['VERCEL']='1'
 with TestClient(delivery) as delivery_client:
  for url,expect in requests.items():
   for method in [delivery_client.get,delivery_client.head]:
    response=method(url+'?download=source',follow_redirects=False)
    assert response.status_code==307 and response.headers['location']=='/source-media/'+url.removeprefix('/app/')+'?download=source'
  for method in [delivery_client.get,delivery_client.head]:assert method('/app/reference-media/radiology-open/unknown-source.pdf',follow_redirects=False).status_code==404
print('27 source image/PDF GET+HEAD routes, exact bytes/MIME, static redirects and unknown rejection verified')
"""
 run=subprocess.run([sys.executable,'-c',script],cwd=ROOT,input=json.dumps(requests),env=env,capture_output=True,text=True,timeout=60)
 assert run.returncode==0,run.stdout+run.stderr
 assert '27 source image/PDF' in run.stdout


@pytest.mark.parametrize('file,mutation',[
 ('data/radiology/radiology-open-images.json','source_caption'),
 ('data/radiology/radiology-asset-evidence.json','cross_investigation'),
 ('data/radiology/non-msk-structure-requirements.json','clinical_promotion'),
 ('data/radiology/non-msk-structure-requirements.json','duplicate_scope'),
 ('data/radiology/reporting-steps/neuroradiology.json','patient_finding'),
])
def test_exact_trauma_additive_amendment_rejects_modified_or_cross_scope_values(source,file,mutation):
 ids={r['id'] for r in source[1]};raw=(ROOT/file).read_text()
 data=json.loads(raw);tokens=integration.unrelated_token_fingerprints(raw,Path(file),ids)
 inv=trauma_amendment.INVESTIGATION
 if mutation=='source_caption':data[inv][0]['caption']+=' Unreviewed source claim.'
 elif mutation=='cross_investigation':
  asset=next(a for a in data['assets'] if a['id'].startswith('open-traumatic-'))
  asset['investigation_ids']=['ra.intracranial-haemorrhage']
 elif mutation=='clinical_promotion':
  item=next(i for i in data['investigations'] if i['investigation_id']==inv);item['clinical_approval']=True
 elif mutation=='duplicate_scope':data['scope']['catalog_investigation_ids'].append(inv)
 else:data['investigations'][inv]['steps'][0]['normal']['EXTRA-AXIAL BLOOD']='No haemorrhage.'
 with pytest.raises(ValueError):trauma_amendment.restore_prior_view(file,data,tokens)


def test_trauma_amendment_preserves_unrelated_changes_for_the_existing_historical_guard(source):
 file='data/radiology/radiology-open-images.json';raw=(ROOT/file).read_text();data=json.loads(raw)
 ids={r['id'] for r in source[1]};tokens=integration.unrelated_token_fingerprints(raw,Path(file),ids)
 unrelated=next(k for k in data if k not in {INV,trauma_amendment.INVESTIGATION})
 data[unrelated][0]['caption']+=' Unreviewed unrelated source claim.'
 restored,_=trauma_amendment.restore_prior_view(file,data,tokens)
 restored.pop(INV,None)
 receipt=json.loads((FOLDER/'integration-receipt.json').read_text())
 assert digest(restored)!=receipt['unrelated_data'][file]['unrelated_semantic_sha256']
 assert restored[unrelated][0]['caption'].endswith('Unreviewed unrelated source claim.')


def test_trauma_amendment_rejects_value_token_drift_and_unreviewed_paths(source):
 file='data/radiology/reporting-steps/neuroradiology.json';raw=(ROOT/file).read_text();data=json.loads(raw)
 ids={r['id'] for r in source[1]};tokens=integration.unrelated_token_fingerprints(raw,Path(file),ids)
 tokens['walkthrough:'+trauma_amendment.INVESTIGATION]='0'*64
 with pytest.raises(ValueError,match='raw value token'):
  trauma_amendment.restore_prior_view(file,data,tokens)
 with pytest.raises(ValueError,match='Unreviewed historical registry path'):
  trauma_amendment.restore_prior_view('data/radiology/other-case.json',data,tokens)
