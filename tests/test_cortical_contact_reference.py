"""Source identity, paired-reference meaning, protected routes and actual lesson."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from primer import cortical_contact_reference as reference
ROOT=Path(__file__).resolve().parents[1]

def test_exact_protected_routes_and_source_descriptor(tmp_path):
    env={k:v for k,v in os.environ.items()if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backups'),TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_ACCESS_USERNAME='hippocampal-route-test',PRIMER_ACCESS_PASSWORD='synthetic-test-password')
    code='''
from fastapi.testclient import TestClient
from primer import server,cortical_contact_reference as s
import hashlib
with TestClient(server.app)as client:
 credentials=('hippocampal-route-test','synthetic-test-password')
 for name in sorted(s.AUTHORED):
  assert client.get(s.PREFIX+name).status_code==401
  response=client.get(s.PREFIX+name,auth=credentials);assert response.status_code==200
  assert hashlib.sha256(response.content).hexdigest()==s.registry()['files'][name]['sha256']
  assert response.headers['cache-control']=='private, no-store'
  response=client.head(s.PREFIX+name,auth=credentials);assert response.status_code==200 and response.content==b''
  if name=='index.html':
   directives={line.strip().split()[0]:line.strip().split()[1:]for line in response.headers['content-security-policy'].split(';')if line.strip()}
   assert directives['connect-src']==["'self'",s.BLOB_HOST] and directives['frame-ancestors']==["'self'"]
 for name in ['registry.json','%69ndex.html','unknown.pack','originals/source.nii.gz']:
  assert client.get(s.PREFIX+name,auth=credentials).status_code==404
 for identifier in ['ra.brain-anatomy','ra.mri-epilepsy','ra.mri-dementia']:
  response=client.get('/api/radiology/modules/'+identifier,auth=credentials);assert response.status_code==200
  items=response.json()['radiology_reference']['source_native_inspectors'];matches=[i for i in items if i['id']==s.IDENTIFIER]
  assert matches==([s.registry()['inspector']] if identifier in ['ra.brain-anatomy','ra.mri-epilepsy'] else [])
'''
    result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
    assert result.returncode==0,result.stdout+result.stderr


def test_authenticated_contact_lesson_matches_current_runtime():
    proof=json.loads((ROOT/'docs/cortical-source-contacts-review-20261101/lesson/proof.json').read_bytes())
    assert proof['allPassed'] and proof['syntheticLoopback'] and not proof['productionLearnerWrites']
    assert not proof['errors'] and not proof['clinicalApproval'] and len(proof['mounts'])==4
    assert {(m['width'],m['identifier'])for m in proof['mounts']}=={(w,i)for w in [390,1440]for i in ['ra.brain-anatomy','ra.mri-epilepsy']}
    assert sum(len(m['states'])for m in proof['mounts'])==308
    assert all(m['allSourceGPUBytesMatched'] and m['reopened']for m in proof['mounts'])
    assert len(proof['responses'])==8 and all(r['status']==200 for r in proof['responses'])
    for file,digest in proof['sourceSHA256'].items():assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==digest,file
