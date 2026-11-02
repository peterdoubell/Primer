import os,tempfile,subprocess,sys
with tempfile.TemporaryDirectory()as d:
 env={k:v for k,v in os.environ.items()if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))};env.update(PRIMER_DB=d+'/db',PRIMER_CONTENT_DIR=d+'/content',PRIMER_BACKUP_DIR=d+'/backup',TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_ACCESS_USERNAME='synthetic-cavernous',PRIMER_ACCESS_PASSWORD='synthetic-password')
 code='''
from fastapi.testclient import TestClient
from primer import server,cavernous_photo_reference as c
import hashlib
with TestClient(server.app)as client:
 auth=('synthetic-cavernous','synthetic-password')
 for name,row in c.registry()['files'].items():
  assert client.get(c.PREFIX+name).status_code==401
  r=client.get(c.PREFIX+name,auth=auth);assert r.status_code==200
  assert hashlib.sha256(r.content).hexdigest()==row['sha256']
  assert r.headers['cache-control']=='private, no-store'
  assert client.head(c.PREFIX+name,auth=auth).content==b''
 for bad in ['missing.jpg','viewer/%69ndex.html']:
  assert client.get(c.PREFIX+bad,auth=auth).status_code==404
 r=client.get(c.PREFIX+'viewer/index.html',auth=auth)
 assert "img-src 'self' blob:"in r.headers['content-security-policy']and "frame-ancestors 'self'"in r.headers['content-security-policy']
 for identifier in ['ra.mri-sella','ra.brain-anatomy','ra.paediatric-neck-masses']:
  r=client.get('/api/radiology/modules/'+identifier,auth=auth);assert r.status_code==200
  found=[x for x in r.json()['radiology_reference'].get('source_native_inspectors',[])if x['id']==c.IDENTIFIER]
  assert found==([c.registry()['inspector']]if identifier=='ra.mri-sella'else[])
print('Nine authenticated source resources, anonymous denial, exact bytes, CSP and sella-only binding passed')
'''
 subprocess.run([sys.executable,'-c',code],env=env,check=True)
