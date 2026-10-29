"""Source identity, paired-reference meaning, protected routes and actual lesson."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from primer import hippocampal_rater_reference as reference
ROOT=Path(__file__).resolve().parents[1]

def test_verified_source_scope_and_remote_delivery():
    data=reference.registry();refs=reference.references()
    assert set(refs)=={'ra.mri-epilepsy'}
    assert all(refs['ra.mri-epilepsy'][0][flag] is False for flag in reference.FLAGS)
    assert data['delivery']['allRemoteHashesMatch'] and len(data['delivery']['files'])==34 and len(data['delivery']['originals'])==8
    m=json.loads(reference.validate_file('manifest.json').read_bytes())
    assert m['annotationReferenceVolume']=='mean' and m['rawRepetitionAnatomicalRegistrationVerified'] is False
    assert m['fullArchiveVerificationPending'] is False
    assert m['sourceArchiveAuthentication']['archiveSHA256']=='e76586274bba73f64f2355b093da3ae671fb8e77bb62c13528cfac9d4893ba2e'
    assert m['volumes']['primary']['counts'].get('7',0)==0 and m['volumes']['second']['counts']['7']==113

def test_exact_protected_routes_and_source_descriptor(tmp_path):
    env={k:v for k,v in os.environ.items()if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backups'),TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_ACCESS_USERNAME='hippocampal-route-test',PRIMER_ACCESS_PASSWORD='synthetic-test-password')
    code='''
from fastapi.testclient import TestClient
from primer import server,hippocampal_rater_reference as s
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
 for name in ['registry.json','%69ndex.html','unknown.pack','originals/Hippocampal_Segmentation.nii']:
  assert client.get(s.PREFIX+name,auth=credentials).status_code==404
 response=client.get('/api/radiology/modules/ra.mri-epilepsy',auth=credentials);assert response.status_code==200
 items=response.json()['radiology_reference']['source_native_inspectors'];assert next(i for i in items if i['id']==s.IDENTIFIER)==s.registry()['inspector']
'''
    result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
    assert result.returncode==0,result.stdout+result.stderr

def test_authenticated_lesson_and_hosted_bytes_match_current_sources():
    p=json.loads((ROOT/'docs/hippocampal-rater-review-20261028/lesson/proof.json').read_bytes())
    assert p['allPassed'] and p['browserChecksPassed'] and p['hostedPixelComparisonPassed'] and p['hostedPixelsComparedToOriginalNifti']==3291136
    assert p['syntheticLoopback'] and p['productionLearnerWrites'] is False and p['errors']==[]
    assert {r['width']for r in p['mounts']}=={390,1440}
    for row in p['mounts']:
        assert len(row['states'])==8 and row['rawRegistrationGuardVerified'] and row['openedAndClosed']
    for file,digest in p['files'].items():assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==digest,file
    assert p['responses'] and all(r['status']==(206 if r['range']else 200)for r in p['responses'])

def test_historical_inverse_is_exact_and_does_not_extend_approval():
    import copy
    import pytest
    from tools import hippocampal_rater_runtime_compatibility as bridge
    proof=bridge.reviewed()
    for name,row in proof['files'].items():
        raw=(ROOT/name).read_bytes();before=bridge.before_hippocampal_bytes(name,raw)
        assert hashlib.sha256(before).hexdigest()==row['before_sha256']
        with pytest.raises(ValueError,match='Unreviewed'):
            bridge.before_hippocampal_bytes(name,raw+b'\nforeign\n')
    fields={'source_native_inspectors':[{'id':'other'},proof['inspector']]}
    assert bridge.before_hippocampal_reference_fields('ra.mri-epilepsy',fields)=={'source_native_inspectors':[{'id':'other'}]}
    bad=copy.deepcopy(fields);bad['source_native_inspectors'][1]['clinical_approval']=True
    with pytest.raises(ValueError):bridge.before_hippocampal_reference_fields('ra.mri-epilepsy',bad)
