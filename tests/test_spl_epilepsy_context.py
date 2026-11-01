"""Exact source reuse and bounded epilepsy temporal/ventricular context."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
from primer import spl_epilepsy_reference as context,spl_reporting_reference as source
R=Path(__file__).resolve().parents[1];D=R/'docs/epilepsy-source-context-review-20261101'
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def test_focused_context_preserves_original_anatomical_data_and_limits():
    bound=context.references();assert set(bound)=={'ra.mri-epilepsy'}
    assert (R/'web/anatomy/spl-epilepsy-context/manifest.json').read_bytes()==context.manifest_bytes()
    manifest=json.loads(context.manifest_bytes());original=json.loads(source.manifest_bytes())
    assert len(manifest['groups'])==13 and len(manifest['labels'])==217
    assert manifest['groups'][1:]==original['groups'][1:]
    assert manifest['labels']==original['labels'] and manifest['labelMeshes']==original['labelMeshes']
    assert manifest['volumes']==original['volumes'] and manifest['labelVolume']==original['labelVolume']
    assert manifest['groups'][0]['codes']==context.CONTEXT_CODES and manifest['defaultComparisonCode']==43
    assert set(source.references())=={'ra.brain-anatomy'} and 'defaultComparisonCode'not in original
    item=bound['ra.mri-epilepsy'][0]
    assert all(item[flag]is False for flag in source.FLAGS)
    assert item['source_grain']['initial_context_label_classes']==18
    assert not item['source_grain']['ventricular_wall_layers_separately_labelled']
    assert not item['source_grain']['hippocampal_subdivisions_separately_labelled']


def test_protected_virtual_metadata_and_original_payload_routes(tmp_path):
    env={k:v for k,v in os.environ.items()if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backups'),TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_ACCESS_USERNAME='synthetic-context',PRIMER_ACCESS_PASSWORD='synthetic-password')
    code='''
from fastapi.testclient import TestClient
from primer import server,spl_epilepsy_reference as c,spl_reporting_reference as s
import hashlib
with TestClient(server.app)as client:
 auth=('synthetic-context','synthetic-password')
 for asset in ['index.html','manifest.json','label-4.mesh.gz']:
  assert client.get(c.PREFIX+asset).status_code==401
 for asset in c.AUTHORED:
  response=client.get(c.PREFIX+asset,auth=auth);assert response.status_code==200
  assert hashlib.sha256(response.content).hexdigest()==c.registry()['files'][asset]['sha256']
  assert response.headers['cache-control']=='private, no-store'
  assert client.head(c.PREFIX+asset,auth=auth).content==b''
  if asset=='index.html':assert "frame-ancestors 'self'"in response.headers['content-security-policy']
 for asset in ['%69ndex.html','viewer.js','registry.json','missing.gz']:
  assert client.get(c.PREFIX+asset,auth=auth).status_code==404
 response=client.get(c.PREFIX+'label-4.mesh.gz',auth=auth,follow_redirects=False)
 assert response.status_code==307 and response.headers['location']==s.PREFIX+'label-4.mesh.gz'
 raw=client.get(c.PREFIX+'label-4.mesh.gz',auth=auth,follow_redirects=True).content
 assert hashlib.sha256(raw).hexdigest()==s.registry()['files']['label-4.mesh.gz']['sha256']
 for identifier in ['ra.mri-epilepsy','ra.brain-anatomy','ra.mri-dementia']:
  r=client.get('/api/radiology/modules/'+identifier,auth=auth);assert r.status_code==200
  found=[i for i in r.json()['radiology_reference']['source_native_inspectors']if i['id']==c.IDENTIFIER]
  assert found==([c.registry()['inspector']]if identifier=='ra.mri-epilepsy'else [])
'''
    result=subprocess.run([sys.executable,'-c',code],cwd=R,env=env,capture_output=True,text=True,timeout=180)
    assert result.returncode==0,result.stdout+result.stderr


def test_actual_lesson_and_reporting_views_match_native_pixels_and_gpu_data():
    proof=json.loads((D/'reader/proof.json').read_bytes())
    assert proof['allPassed']and proof['syntheticLoopback']and not proof['productionLearnerWrites']
    assert not proof['clinicalApproval']and not proof['completeReportingCoverage']and not proof['wholeLessonExternalImageDeliveryVerified']
    assert proof['errors']==[]and len(proof['cases'])==4
    assert {(r['width'],r['entry'])for r in proof['cases']}=={(w,e)for w in [390,1440]for e in ['lesson','reporting-model']}
    assert sum(len(r['pixelCases'])for r in proof['cases'])==480
    assert sum(p['pixels']for r in proof['cases']for p in r['pixelCases'])==34979840
    for case in proof['cases']:
        assert case['reopened']and len(case['gpu'])==18 and len(case['cameras'])==4
        assert case['initial']['selected']==4 and case['initial']['comparison']==43
        assert case['initial']['imageState']['overlay']=='pair'
        assert {r['code']for r in case['gpu']}==set(context.CONTEXT_CODES)
    for name,digest in proof['sourceSHA256'].items():assert sha((R/name).read_bytes())==digest,name
    index=json.loads((D/'evidence-index.json').read_bytes())
    assert not index['clinicalApproval'] and not index['completeReportingCoverage'] and not index['wholeGoalComplete']
    for name,digest in index['sourceSHA256'].items():assert sha((R/name).read_bytes())==digest,name
    for name,digest in index['proofSHA256'].items():assert sha((D/name).read_bytes())==digest,name


def test_source_granularity_does_not_convert_partial_context_to_fine_anatomy():
    proof=json.loads((D/'requirement-source-granularity.json').read_bytes())
    assert len(proof['pairedRequirements'])==12 and len(proof['retainedOtherContractGroups'])==6
    assert sum(len(r['requiredParts'])for r in proof['pairedRequirements'])==22
    assert proof['combinedClassesRemainCombined']and not proof['automaticClinicalApproval']and not proof['completeReportingCoverage']
    assert all(not p['requiredPartIndependentlyVerified']for r in proof['pairedRequirements']for p in r['requiredParts'])
    assert all(not r['clinicalApproval']for r in proof['pairedRequirements'])
    for name,digest in proof['sourceSHA256'].items():assert sha((R/name).read_bytes())==digest,name


def test_context_inverse_rejects_unrelated_edits_and_approval_drift():
    import copy,pytest
    from tools.spl_epilepsy_runtime_compatibility import reviewed,before_context_bytes,before_context_fields
    proof=reviewed()
    for name,row in proof['files'].items():
        raw=(R/name).read_bytes();before=before_context_bytes(name,raw)
        assert sha(before)==row['before_sha256']
        assert before_context_bytes(name,before)==before
        with pytest.raises(ValueError):before_context_bytes(name,raw+b'foreign change')
    fields={'source_native_inspectors':[proof['inspector']]}
    assert before_context_fields('ra.mri-epilepsy',fields)=={'source_native_inspectors':[]}
    assert fields['source_native_inspectors']==[proof['inspector']]
    for mutation in ['duplicate','clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved','caption']:
        changed=copy.deepcopy(fields)
        if mutation=='duplicate':changed['source_native_inspectors'].append(proof['inspector'])
        elif mutation=='caption':changed['source_native_inspectors'][0]['caption']+=' Unreviewed'
        else:changed['source_native_inspectors'][0][mutation]=True
        with pytest.raises(ValueError):before_context_fields('ra.mri-epilepsy',changed)
    with pytest.raises(ValueError):before_context_fields('ra.brain-anatomy',fields)
