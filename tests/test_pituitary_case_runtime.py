"""Protected delivery and explicit scientific scope for the processed source case."""
from pathlib import Path
import copy,hashlib,json,os,subprocess,sys
import pytest
from primer import pituitary_case_reference as source
R=Path(__file__).resolve().parents[1]

def test_exact_processed_case_and_single_module_binding():
    assert set(source.references())=={'ra.mri-sella'}
    item=source.references()['ra.mri-sella'][0]
    assert all(item[k]is False for k in source.FLAGS)
    assert item['source_grain']['source_planes']==4980
    assert item['source_grain']['annotation_qform_displacement_mm']==22.5
    assert not item['source_grain']['source_header_conflict_resolved']
    for asset in source.registry()['files']:source.validate_file(asset)
    m=json.loads(source.metadata_bytes('plane-package/manifest.json'))
    assert len(m['packs'])==82 and len(source.registry()['payloads'])==84
    assert all(v['acquisitionNative']is False for v in m['volumes'].values())


def test_private_delivery_ranges_and_byte_pinned_metadata(tmp_path):
    env={k:v for k,v in os.environ.items()if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backup'),TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_ACCESS_USERNAME='synthetic-pituitary',PRIMER_ACCESS_PASSWORD='synthetic-password')
    code='''
from fastapi.testclient import TestClient
from primer import server,pituitary_case_reference as c
import hashlib,os
with TestClient(server.app)as client:
 auth=('synthetic-pituitary','synthetic-password');data=c.registry()
 for asset,row in data['files'].items():
  assert client.get(c.PREFIX+asset).status_code==401
  response=client.get(c.PREFIX+asset,auth=auth);assert response.status_code==200
  assert hashlib.sha256(response.content).hexdigest()==row['sha256']
  assert response.headers['cache-control']=='private, no-store'
  assert client.head(c.PREFIX+asset,auth=auth).content==b''
 html=client.get(c.PREFIX+'provided-plane-viewer/index.html',auth=auth)
 assert "frame-ancestors 'self'"in html.headers['content-security-policy']and c.HOST in html.headers['content-security-policy']
 for asset in ['provided-plane-viewer/%69ndex.html','missing.json','registry.json']:
  assert client.get(c.PREFIX+asset,auth=auth).status_code==404
 for identifier in ['ra.mri-sella','ra.brain-anatomy','ra.mri-neck-spaces','ra.paediatric-neck-masses']:
  response=client.get('/api/radiology/modules/'+identifier,auth=auth);assert response.status_code==200
  found=[x for x in response.json()['radiology_reference'].get('source_native_inspectors',[])if x['id']==c.IDENTIFIER]
  assert found==([data['inspector']]if identifier in c.BINDINGS else [])
 os.environ['VERCEL']='1';c.local_payload.cache_clear()
 for group in ['payloads','originals']:
  for asset,row in data[group].items():
   assert client.get(c.PREFIX+asset).status_code==401
   if asset.startswith('source-models/'):continue
   r=client.get(c.PREFIX+asset,auth=auth,follow_redirects=False);assert r.status_code==307 and r.headers['location']==row['url']
   assert r.headers['cache-control']=='private, no-store'
   for invalid in ['bytes=0-','bytes=-1','bytes=1-0','bytes=0-1,3-4','bytes=0-'+str(row['bytes'])]:
    r=client.get(c.PREFIX+asset,auth=auth,headers={'Range':invalid},follow_redirects=False)
    assert r.status_code==416 and r.headers['content-range']=='bytes */'+str(row['bytes'])
   assert client.head(c.PREFIX+asset,auth=auth,headers={'Range':'bytes=0-15'},follow_redirects=False).status_code==206
'''
    result=subprocess.run([sys.executable,'-c',code],cwd=R,env=env,capture_output=True,text=True,timeout=180)
    assert result.returncode==0,result.stdout+result.stderr


def test_exact_inverse_rejects_unknown_bytes_and_approval_drift():
    from tools.pituitary_case_runtime_compatibility import reviewed,before_pituitary_bytes,before_pituitary_fields
    proof=reviewed()
    for name,row in proof['files'].items():
        raw=(R/name).read_bytes();before=before_pituitary_bytes(name,raw)
        assert hashlib.sha256(before).hexdigest()==row['before_sha256']
        assert before_pituitary_bytes(name,before)==before
        with pytest.raises(ValueError):before_pituitary_bytes(name,raw+b'foreign')
    fields={'source_native_inspectors':[proof['inspector']]}
    assert before_pituitary_fields('ra.mri-sella',fields)=={'source_native_inspectors':[]}
    for flag in [*source.FLAGS,'caption','duplicate']:
        changed=copy.deepcopy(fields)
        if flag=='caption':changed['source_native_inspectors'][0]['caption']+=' changed'
        elif flag=='duplicate':changed['source_native_inspectors'].append(proof['inspector'])
        else:changed['source_native_inspectors'][0][flag]=True
        with pytest.raises(ValueError):before_pituitary_fields('ra.mri-sella',changed)
    with pytest.raises(ValueError):before_pituitary_fields('ra.brain-anatomy',fields)


@pytest.mark.parametrize('folder',['reader','reader-hosted'])
def test_authenticated_reader_pixels_models_and_immutable_range_receipts(folder):
    d=R/'docs/pituitary-case-source-review-20261101';reader=d/folder
    browser=json.loads((reader/'browser-proof.json').read_bytes());pixels=json.loads((reader/'pixel-proof.json').read_bytes());camera=json.loads((reader/'model-camera-proof.json').read_bytes())
    assert browser['allPassed']and browser['authenticatedAppVerified']and browser['syntheticLoopback']
    assert not browser['productionLearnerWrites']and not browser['productionVerified']and browser['errors']==[]
    assert browser['cases']==40 and {(m['width'],m['identifier'])for m in browser['mounts']}=={(390,'ra.mri-sella'),(1440,'ra.mri-sella')}
    assert all(m['reopened']for m in browser['mounts'])and all(r['status']==206 for r in browser['rangeRequests'])
    assert pixels['allPassed']and pixels['actualPlainAndMarkedCanvasPixelsCompared']==21280840 and pixels['sourceSamplesAndCoordinateProbesChecked']==240
    assert not pixels['imageResamplingAppliedByPrimer']and not pixels['coordinateConflictResolved']
    assert camera['allPassed']and camera['GPUModelReadbacks']==4 and camera['GPUUniformCameraStates']==6
    for name,digest in browser['sourceSHA256'].items():assert hashlib.sha256((R/'web/anatomy'/source.ATLAS/'provided-plane-viewer'/name).read_bytes()).hexdigest()==digest
    receipt=json.loads((d/'immutable-delivery.json').read_bytes());ranges=json.loads((d/'live-ranges.json').read_bytes())
    assert receipt['allRemoteHashesMatch']and len(receipt['files'])==90
    assert hashlib.sha256((d/'immutable-delivery.json').read_bytes()).hexdigest()==source.registry()['remote_delivery_receipt_sha256']
    assert all(row['remoteHashVerified']for row in receipt['files'].values())
    assert ranges['all82PacksClaimed']and ranges['packsChecked']==82 and len(ranges['cases'])==246


def test_range_relay_bounds_upstream_headers_and_response_length(monkeypatch):
    import asyncio,httpx
    row=next(iter(source.registry()['payloads'].values()));asset=next(iter(source.registry()['payloads']))
    client_type=httpx.AsyncClient
    async def check(status,header,body,valid):
        def handler(request):
            assert str(request.url)==row['url']and request.headers['range']=='bytes=0-15'
            assert 'authorization'not in request.headers and 'cookie'not in request.headers
            return httpx.Response(status,headers={'Content-Range':header},stream=httpx.ByteStream(body))
        monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:client_type(transport=httpx.MockTransport(handler),**kw))
        if valid:assert await source.remote_range(asset,0,15)==body
        else:
            with pytest.raises(ValueError):await source.remote_range(asset,0,15)
    async def run():
        exact='bytes 0-15/'+str(row['bytes'])
        await check(206,exact,b'a'*16,True)
        for status,header,body in [(200,exact,b'a'*16),(206,'bytes 1-16/'+str(row['bytes']),b'a'*16),(206,exact,b'a'*17),(206,exact,b'a'*15)]:await check(status,header,body,False)
        for start,end in [(1,0),(0,row['bytes']),(0,2*1024*1024)]:
            with pytest.raises(ValueError):await source.remote_range(asset,start,end)
    asyncio.run(run())
