"""Independent regression cases for authenticated source caching and thin runtimes."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run_isolated(code, tmp_path):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('TURSO', 'PRIMER_ACCESS_'))
           and k not in {'VERCEL', 'VERCEL_ENV'}}
    env.update(PRIMER_DB=str(tmp_path / 'reader.db'),
               PRIMER_BACKUP_DIR=str(tmp_path / 'backups'))
    result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr


def test_authenticated_native_code_cannot_be_publicly_cached_by_version_query(tmp_path):
    run_isolated(r'''
import logging,os
os.environ['PRIMER_ACCESS_USERNAME']='source-review'
os.environ['PRIMER_ACCESS_PASSWORD']='synthetic-test-password'
from fastapi.testclient import TestClient
import primer.server as server
from primer.stroke_source_delivery import NATIVE_PREFIX,NATIVE_BLOB_PREFIX
logging.disable(logging.CRITICAL)
with TestClient(server.app,follow_redirects=False) as c:
 for hosted in [False,True]:
  if hosted:os.environ['VERCEL']='1'
  for filename in ['reference.html','reference.js','manifest.json']:
   for query in ['', '?v=cache-poison', '?redirect=https://unreviewed.example&v=1']:
    for verb in ['GET','HEAD']:
     path=NATIVE_PREFIX+filename+query
     assert c.request(verb,path).status_code==401
     r=c.request(verb,path,auth=('source-review','synthetic-test-password'))
     assert r.status_code==200
     assert r.headers['cache-control']=='private, no-store'
     assert 'Authorization' in r.headers['vary'] and 'Cookie' in r.headers['vary']
     expected=server.CSP.replace("connect-src 'self';","connect-src 'self' "+NATIVE_BLOB_PREFIX+";") if filename=='reference.html' else server.CSP
     assert r.headers['content-security-policy']==expected
     if verb=='HEAD':assert r.content==b''
 assert "connect-src 'self';" in c.get('/app/index.html',auth=('source-review','synthetic-test-password')).headers['content-security-policy']
''', tmp_path)


def test_encoded_unknown_native_paths_and_host_queries_cannot_choose_redirect(tmp_path):
    run_isolated(r'''
import logging,os
os.environ['PRIMER_ACCESS_USERNAME']='source-review'
os.environ['PRIMER_ACCESS_PASSWORD']='synthetic-test-password'
os.environ['VERCEL']='1'
from fastapi.testclient import TestClient
import primer.server as server
from primer.stroke_source_delivery import delivery,NATIVE_PREFIX,PUBLICATION_PREFIX
logging.disable(logging.CRITICAL)
auth=('source-review','synthetic-test-password')
with TestClient(server.app,follow_redirects=False) as c:
 for path,row in delivery()['files'].items():
  for verb in ['GET','HEAD']:
   for host in ['other.example/healthz','other.example/api/state']:
    headers={'Host':host}
    assert c.request(verb,path,headers=headers).status_code==401
    r=c.request(verb,path+'?url=https://unreviewed.example/&next=//unreviewed.example',headers=headers,auth=auth)
    assert r.status_code==307 and r.headers['location']==row['url']
    assert r.headers['cache-control']=='private, no-store'
 for prefix in [NATIVE_PREFIX,PUBLICATION_PREFIX]:
  for name in ['nested/reference.html','reference.html/','%2freference.html','..%2freference.html','%252e%252e%252freference.html','%00reference.html','reference.html%5cunknown','sub-343_T1w.nii.gz']:
   for verb in ['GET','HEAD']:
    assert c.request(verb,prefix+name).status_code==401
    assert c.request(verb,prefix+name,auth=auth).status_code==404
''', tmp_path)


def test_absent_hosted_payload_metadata_does_not_accept_present_wrong_source(tmp_path):
    run_isolated(r'''
import os,tempfile,shutil
from pathlib import Path
from primer import stroke_source_delivery as delivery,stroke_native_inspectors as native
root=Path.cwd()
with tempfile.TemporaryDirectory() as td:
 thin=Path(td);code=thin/'web/anatomy/soop-stroke-sub342';code.mkdir(parents=True)
 for name in ['reference.html','reference.js','manifest.json']:shutil.copyfile(root/'web/anatomy/soop-stroke-sub342'/name,code/name)
 delivery.ROOT=thin;native.ROOT=thin
 delivery.delivery.cache_clear();native.references.cache_clear()
 os.environ['VERCEL']='1'
 assert len(delivery.delivery()['files'])==48
 assert native.references()['ra.acute-stroke'][0]['id']=='soop-stroke-sub342-native'
 os.environ.pop('VERCEL');delivery.delivery.cache_clear()
 try:delivery.delivery()
 except ValueError:pass
 else:raise AssertionError('Missing local source accepted')
 os.environ['VERCEL']='1';delivery.delivery.cache_clear()
 p=thin/'web/anatomy/soop-stroke-sub342/trace.native.gz';p.write_bytes(b'corrupt stored source')
 try:delivery.delivery()
 except ValueError:pass
 else:raise AssertionError('Present corrupt hosted source accepted')
''', tmp_path)
