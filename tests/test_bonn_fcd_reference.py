"""Source identity, paired-reference meaning, protected routes and actual lesson."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from primer import bonn_fcd_reference as reference
ROOT=Path(__file__).resolve().parents[1]

def test_exact_protected_routes_and_source_descriptor(tmp_path):
    env={k:v for k,v in os.environ.items()if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backups'),TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_ACCESS_USERNAME='hippocampal-route-test',PRIMER_ACCESS_PASSWORD='synthetic-test-password')
    code='''
from fastapi.testclient import TestClient
from primer import server,bonn_fcd_reference as s
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
 response=client.get('/api/radiology/modules/ra.mri-epilepsy',auth=credentials);assert response.status_code==200
 items=response.json()['radiology_reference']['source_native_inspectors'];assert next(i for i in items if i['id']==s.IDENTIFIER)==s.registry()['inspector']
'''
    result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
    assert result.returncode==0,result.stdout+result.stderr

