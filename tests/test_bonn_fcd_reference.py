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


def test_authenticated_lesson_exact_pre_geometry_source_evidence():
    proof=json.loads((ROOT/'docs/fcd-native-source-review-20261028/lesson/proof.json').read_bytes())
    assert proof['allPassed'] and proof['browserChecksPassed'] and proof['hostedPixelComparisonPassed']
    assert proof['hostedPixelsComparedToOriginalNifti']==884736
    assert proof['syntheticLoopback'] and not proof['productionLearnerWrites'] and not proof['errors']
    assert {r['width'] for r in proof['mounts']}=={390,1440}
    for row in proof['mounts']:
        assert len(row['states'])==3 and row['T1RegistrationGuardVerified'] and row['openedAndClosed']
    from tools.geometry_measures_runtime_compatibility import before_geometry_measures_bytes
    for file,digest in proof['files'].items():assert hashlib.sha256(before_geometry_measures_bytes(file,(ROOT/file).read_bytes())).hexdigest()==digest
    assert proof['responses'] and all(r['status']==(206 if r['range'] else 200) for r in proof['responses'])


def test_exact_fcd_inverse_rejects_unknown_bytes_and_approval_changes():
    import copy
    import pytest
    from tools import bonn_fcd_runtime_compatibility as bridge
    proof=bridge.reviewed()
    for name,row in proof['files'].items():
        raw=(ROOT/name).read_bytes()
        assert hashlib.sha256(bridge.before_fcd_bytes(name,raw)).hexdigest()==row['before_sha256']
        with pytest.raises(ValueError):bridge.before_fcd_bytes(name,raw+b'foreign edit')
    fields={'source_native_inspectors':[proof['inspector']]}
    assert bridge.before_fcd_reference_fields('ra.mri-epilepsy',fields)=={'source_native_inspectors':[]}
    bad=copy.deepcopy(fields);bad['source_native_inspectors'][0]['clinical_approval']=True
    with pytest.raises(ValueError):bridge.before_fcd_reference_fields('ra.mri-epilepsy',bad)
