"""Source identity, grain, protected delivery and thin-function interpretation."""
from pathlib import Path
import copy,hashlib,json,os,shutil,subprocess,sys
import pytest
from primer import schirmer_vascular_reference as source
ROOT=Path(__file__).resolve().parents[1]
def clear():
 for f in [source.registry,source.metadata_bytes,source.references,source._check_file]:f.cache_clear()
@pytest.fixture
def thin(tmp_path,monkeypatch):
 assets=tmp_path/'web/anatomy/schirmer-vascular';assets.mkdir(parents=True);data=tmp_path/'data/radiology';data.mkdir(parents=True)
 for name in source.AUTHORED-{'manifest.json','labels.json','hierarchy.json'}:shutil.copy2(ROOT/'web/anatomy/schirmer-vascular'/name,assets/name)
 for name in ['schirmer-vascular-reference.json','schirmer-vascular-manifest.json.gz','schirmer-vascular-labels.json.gz','schirmer-vascular-hierarchy.json.gz']:shutil.copy2(ROOT/'data/radiology'/name,data/name)
 monkeypatch.setattr(source,'ROOT',tmp_path);monkeypatch.setattr(source,'REGISTRY',data/'schirmer-vascular-reference.json');monkeypatch.setenv('VERCEL','1');clear()
 yield tmp_path
 clear()
def test_exact_source_meaning_and_components():
 refs=source.references();assert set(refs)=={'ra.brain-anatomy','ra.acute-stroke'}
 for entries in refs.values():assert len(entries)==1 and all(entries[0][k]is False for k in source.FLAGS)
 labels=json.loads(source.metadata_bytes('labels.json'));assert {r['code']:r['publishedFigureLegendName']for r in labels['sourceClasses']}==source.NAMES
 assert labels['namedSourceClasses']==10 and labels['uninterpretedSourceClasses']==[19]and labels['components26']==15
 single=next(r for r in labels['sourceClasses']if r['code']==19);assert single['voxels']==1 and single['components26'][0]['focusSourceWorld']==[-52,-53,-47]
 assert all(r['individualFineStructureCoverageApproved']is False for r in labels['sourceClasses'])
 for name in ['../index.html','%69ndex.html','originals/mni_vascular_territories.nii.gz','unknown.pack']:
  with pytest.raises(ValueError):source.validate_file(name)
def test_thin_metadata_keeps_original_identity_without_static_payloads(thin):
 assert source.references()['ra.acute-stroke'][0]['id']==source.IDENTIFIER
 for name in ['manifest.json','labels.json','hierarchy.json']:
  assert not (thin/'web/anatomy/schirmer-vascular'/name).exists()
  assert hashlib.sha256(source.metadata_bytes(name)).hexdigest()==source.registry()['files'][name]['sha256']
@pytest.mark.parametrize('mutation',['approval','bindings','name_count','drop_pack','source_hash','source_grain','licence'])
def test_unreviewed_scope_changes_fail_closed(thin,monkeypatch,mutation):
 d=copy.deepcopy(source.registry())
 if mutation=='approval':d['clinical_approval']=True
 elif mutation=='bindings':d['bindings']['ra.mra-head']=[source.IDENTIFIER]
 elif mutation=='name_count':d['named_source_classes']=11
 elif mutation=='drop_pack':del d['files']['labels-axis-0-part-0.pack']
 elif mutation=='source_hash':d['source_inputs'][0]['sha256']='0'*64
 elif mutation=='source_grain':d['inspectors'][source.IDENTIFIER]['source_grain']['control_count']=16
 else:d['inspectors'][source.IDENTIFIER]['license']='CC0'
 raw=(json.dumps(d)+'\n').encode();source.REGISTRY.write_bytes(raw);monkeypatch.setattr(source,'REGISTRY_SHA256',hashlib.sha256(raw).hexdigest());clear()
 with pytest.raises(ValueError):source.references()
def test_modified_and_symlinked_authored_files_fail(thin):
 p=thin/'web/anatomy/schirmer-vascular/viewer.js';p.write_bytes(p.read_bytes()+b'\n')
 with pytest.raises(ValueError,match='length'):source.validate_file('viewer.js')
 p.unlink();p.symlink_to(ROOT/'web/anatomy/schirmer-vascular/viewer.js')
 with pytest.raises(ValueError,match='symlink'):source.validate_file('viewer.js')
def test_protected_routes_exact_ranges_and_both_reader_bindings(tmp_path):
 env={k:v for k,v in os.environ.items()if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))};env.update(PRIMER_DB=str(tmp_path/'record.db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backups'),TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_ACCESS_USERNAME='synthetic-vascular-test',PRIMER_ACCESS_PASSWORD='synthetic-test-password')
 script='''
import os,json,hashlib
from fastapi.testclient import TestClient
from primer import server,schirmer_vascular_reference as s
m=json.loads(s.metadata_bytes('manifest.json'));row=m['volumes']['FLAIR']['planes']['2'][52];auth=('synthetic-vascular-test','synthetic-test-password')
with TestClient(server.app)as client:
 for name in ['index.html','manifest.json','labels.json','semantic-mapping.json','territory-19.mesh.gz',row['file']]:
  assert client.get(s.PREFIX+name).status_code==401
  r=client.get(s.PREFIX+name,auth=auth);assert r.status_code==200 and r.headers['cache-control']=='private, no-store'
  if name=='index.html':assert "frame-ancestors 'self'"in r.headers['content-security-policy']
 for name in ['%69ndex.html','unknown.pack','originals/mni_vascular_territories.nii.gz']:
  assert client.get(s.PREFIX+name,auth=auth).status_code==404
 r=client.get(s.PREFIX+row['file'],auth=auth,headers={'Range':f"bytes={row['offset']}-{row['offset']+row['gzipBytes']-1}"});assert r.status_code==206 and hashlib.sha256(r.content).hexdigest()==row['gzipSHA256']
 assert r.headers['content-range']==f"bytes {row['offset']}-{row['offset']+row['gzipBytes']-1}/{m['packs'][row['file']]['bytes']}"
 for ident in ['ra.brain-anatomy','ra.acute-stroke']:
  data=client.get('/api/radiology/modules/'+ident,auth=auth).json();item=next(x for x in data['radiology_reference']['source_native_inspectors']if x['id']==s.IDENTIFIER);assert all(item[k]is False for k in s.FLAGS)
 os.environ['VERCEL']='1';r=client.get(s.PREFIX+row['file'],auth=auth,follow_redirects=False);assert r.status_code==307 and r.headers['location']=='/source-media/anatomy/schirmer-vascular/'+row['file']
'''
 run=subprocess.run([sys.executable,'-c',script],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120);assert run.returncode==0,run.stdout+run.stderr
