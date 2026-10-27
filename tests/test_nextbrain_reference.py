"""Pinned source scope and authenticated delivery for the ex vivo reference."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest
from primer import nextbrain_reference as source
ROOT = Path(__file__).resolve().parents[1]


def clear():
    source.registry.cache_clear()
    source.references.cache_clear()
    source._check.cache_clear()


def test_reference_preserves_source_limits_and_full_geometry_inventory():
    refs=source.references()
    assert set(refs)=={'ra.brain-anatomy'}
    item=refs['ra.brain-anatomy'][0]
    assert all(item[k] is False for k in source.FLAGS)
    manifest=json.loads(source.validate_file('manifest.json').read_bytes())
    assert manifest['sourceLUTSidePrefixesConflict'] is True
    assert manifest['annotationCrop']['offsetMRIijk']==[124,10,23]
    assert manifest['volumes']['MRI']['shape']==[880,880,640]
    labels=json.loads(source.validate_file('labels.json').read_bytes())
    assert sum(len(r['components26'])for r in labels['classes'])==3721
    assert any(r['rawLUTName'].startswith('Left-')for r in labels['classes'])
    assert all(not r['displayName'].startswith(('Left-','L_','ctx-rh-'))for r in labels['classes'])
    assert len(source.registry()['delivery']['files'])==333


@pytest.mark.parametrize('name',['../index.html','%69ndex.html','missing.pack','originals/mri.nii.gz'])
def test_no_unregistered_delivery(name):
    with pytest.raises(ValueError):source.validate_file(name)


def test_modified_source_and_symlinks_fail_closed(tmp_path,monkeypatch):
    assets=tmp_path/'web/anatomy/nextbrain';assets.mkdir(parents=True)
    shutil.copy2(ROOT/'web/anatomy/nextbrain/viewer.js',assets/'viewer.js')
    monkeypatch.setattr(source,'ROOT',tmp_path)
    p=assets/'viewer.js';p.write_bytes(p.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='length'):source.validate_file('viewer.js')
    p.unlink();p.symlink_to(ROOT/'web/anatomy/nextbrain/viewer.js')
    with pytest.raises(ValueError,match='symlink'):source.validate_file('viewer.js')
    clear()


def test_authenticated_exact_routes_and_narrow_blob_csp(tmp_path):
    env={k:v for k,v in os.environ.items()if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backups'),TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_ACCESS_USERNAME='synthetic-nextbrain',PRIMER_ACCESS_PASSWORD='synthetic-test-password')
    script='''
from fastapi.testclient import TestClient
from primer import server,nextbrain_reference as s
import hashlib
auth=('synthetic-nextbrain','synthetic-test-password')
with TestClient(server.app)as c:
 for name in sorted(s.AUTHORED):
  assert c.get(s.PREFIX+name).status_code==401
  r=c.get(s.PREFIX+name,auth=auth);assert r.status_code==200
  assert hashlib.sha256(r.content).hexdigest()==s.registry()['files'][name]['sha256']
  assert r.headers['cache-control']=='private, no-store'
  if name=='index.html':
   assert "connect-src 'self' "+s.BLOB_HOST+";"in r.headers['content-security-policy']
   assert "frame-ancestors 'self';"in r.headers['content-security-policy']
 for name in ['%69ndex.html','other.js','label-1.mesh.gz']:
  assert c.get(s.PREFIX+name,auth=auth).status_code==404
 data=c.get('/api/radiology/modules/ra.brain-anatomy',auth=auth).json()
 items=data['radiology_reference']['source_native_inspectors']
 assert len([x for x in items if x['id']==s.IDENTIFIER])==1
'''
    run=subprocess.run([sys.executable,'-c',script],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
    assert run.returncode==0,run.stdout+run.stderr


def test_pinned_browser_gpu_pixel_and_lesson_evidence():
    evidence=ROOT/'docs/nextbrain-reader-review-20261027'
    browser=json.loads((evidence/'browser-proof.json').read_bytes())
    assert browser['allPassed'] and browser['errors']==[]
    for name,digest in browser['files'].items():
        assert hashlib.sha256(source.validate_file(name).read_bytes()).hexdigest()==digest
    manifest=json.loads(source.validate_file('manifest.json').read_bytes())
    assert [r['code']for r in browser['gpu']]==list(range(1,99))
    for row in browser['gpu']:
        assert row['error']==0 and row['visible']>10
        for kind in ['positions','indices']:
            assert row['parts'][kind]==[c['sha256']for c in manifest['meshParts'][str(row['code'])]['parts'][kind]['chunks']]
    assert {(r['code'],r['mode'])for r in browser['cases']}=={(c,m)for c in range(1,99)for m in ['mri','schematic']}
    pixels=json.loads((evidence/'pixel-proof.json').read_bytes())
    assert pixels['allPassed'] and pixels['pixelsCompared']==372556800 and pixels['planes']==588
    assert pixels['browserProofSHA256']==hashlib.sha256((evidence/'browser-proof.json').read_bytes()).hexdigest()
    recovery=json.loads((evidence/'recovery-proof.json').read_bytes())
    assert recovery['allPassed'] and recovery['errors']==[]
    assert {c['failure']for c in recovery['cases']if 'failure'in c}=={'ignored-range','corrupt','mesh503','stale selection','invalid window','WebGL context loss'}
    remote=json.loads((evidence/'remote-browser-proof.json').read_bytes())
    assert remote['allPassed'] and len(remote['responses'])==30
    assert all(r['status']==(206 if r['range']else 200)for r in remote['responses'])
    lesson=json.loads((evidence/'lesson/proof.json').read_bytes())
    assert lesson['allPassed'] and lesson['syntheticLoopback'] and not lesson['productionLearnerWrites'] and lesson['errors']==[]
    assert {m['width']for m in lesson['mounts']}=={390,1440}
    for name,digest in lesson['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
