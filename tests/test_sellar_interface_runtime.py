from pathlib import Path
import copy,hashlib,json,os,subprocess,sys
import pytest
from primer import sellar_interface_reference as source
from primer.source_volume_integrity import verified_volume_identity
R=Path(__file__).resolve().parents[1]

def test_exact_source_reference_and_restricted_bindings():
    refs=source.references();assert set(refs)=={'ra.brain-anatomy','ra.mri-sella'}
    item=refs['ra.mri-sella'][0]
    assert all(item[flag]is False for flag in source.FLAGS)
    assert item['source_grain']['source_interface_pairs']==36 and item['source_grain']['source_cell_faces']==652
    assert len(source.registry()['files'])==120
    for asset in source.registry()['virtual_metadata']:
        assert source.metadata_bytes(asset)==(R/'web/anatomy'/source.ATLAS/asset).read_bytes()


def test_missing_hosted_CT_uses_only_exact_existing_static_identity(tmp_path,monkeypatch):
    data=json.loads((R/'data/radiology/source-anatomy-references.json').read_bytes());inventory=json.loads((R/'data/radiology/radiology-static-source-volumes.json').read_bytes())
    for atlas in ['verse521','totalseg-v3-s0358']:
        volume=next(e['source_volume']for rows in data.values()for e in rows if e['atlas']==atlas and e.get('source_volume'))
        with pytest.raises(ValueError):verified_volume_identity(volume,tmp_path/'web',R/'data/radiology')
        monkeypatch.setenv('VERCEL','1')
        expected=inventory['files'][volume['src']]
        assert verified_volume_identity(volume,tmp_path/'web',R/'data/radiology')==expected['bytes']
        assert expected['sha256']==hashlib.sha256((R/'web'/volume['src'].removeprefix('/app/')).read_bytes()).hexdigest()
        for key in ['sha256','script_sha256']:
            changed=copy.deepcopy(volume);changed[key]='0'*64
            with pytest.raises(ValueError):verified_volume_identity(changed,tmp_path/'web',R/'data/radiology')
        monkeypatch.delenv('VERCEL')


def test_protected_resources_metadata_and_static_redirects(tmp_path):
    env={k:v for k,v in os.environ.items()if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backup'),TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_ACCESS_USERNAME='synthetic-sellar',PRIMER_ACCESS_PASSWORD='synthetic-password')
    code='''
from fastapi.testclient import TestClient
from primer import server,sellar_interface_reference as c
import hashlib,os
with TestClient(server.app)as client:
 auth=('synthetic-sellar','synthetic-password')
 for asset in c.registry()['files']:
  assert client.get(c.PREFIX+asset).status_code==401
  response=client.get(c.PREFIX+asset,auth=auth);assert response.status_code==200
  assert hashlib.sha256(response.content).hexdigest()==c.registry()['files'][asset]['sha256']
  assert response.headers['cache-control']=='private, no-store'
  assert client.head(c.PREFIX+asset,auth=auth).content==b''
 for asset in ['viewer/%69ndex.html','registry.json','missing.svg']:
  assert client.get(c.PREFIX+asset,auth=auth).status_code==404
 for identifier in [*c.BINDINGS,'ra.mri-epilepsy','ra.mri-neck-spaces','ra.paediatric-neck-masses']:
  r=client.get('/api/radiology/modules/'+identifier,auth=auth);assert r.status_code==200
  found=[x for x in r.json()['radiology_reference'].get('source_native_inspectors',[])if x['id']==c.IDENTIFIER]
  assert found==([c.registry()['inspector']]if identifier in c.BINDINGS else [])
 os.environ['VERCEL']='1'
 for asset in ['viewer/source-contacts.mesh.gz','schematics/contact-3011-3012-axial.svg']:
  r=client.get(c.PREFIX+asset,auth=auth,follow_redirects=False);assert r.status_code==307 and r.headers['location']=='/source-media/anatomy/'+c.ATLAS+'/'+asset
 for atlas in ['verse521','totalseg-v3-s0358']:
  r=client.get('/app/anatomy/'+atlas+'/ct-reference.html',auth=auth,follow_redirects=False);assert r.status_code==307 and r.headers['location']=='/source-media/anatomy/'+atlas+'/ct-reference.html'
'''
    result=subprocess.run([sys.executable,'-c',code],cwd=R,env=env,capture_output=True,text=True,timeout=180)
    assert result.returncode==0,result.stdout+result.stderr


def test_new_inverse_rejects_unknown_edits_or_descriptor_approval_drift():
    from tools.sellar_interface_runtime_compatibility import reviewed,before_interfaces_bytes,before_interfaces_fields
    proof=reviewed()
    for name,row in proof['files'].items():
        raw=(R/name).read_bytes();before=before_interfaces_bytes(name,raw)
        assert hashlib.sha256(before).hexdigest()==row['before_sha256']
        assert before_interfaces_bytes(name,before)==before
        with pytest.raises(ValueError):before_interfaces_bytes(name,raw+b'foreign')
    for identifier in source.BINDINGS:
        fields={'source_native_inspectors':[proof['inspector']]}
        assert before_interfaces_fields(identifier,fields)=={'source_native_inspectors':[]}
        for flag in [*source.FLAGS,'caption','duplicate']:
            changed=copy.deepcopy(fields)
            if flag=='caption':changed['source_native_inspectors'][0]['caption']+=' changed'
            elif flag=='duplicate':changed['source_native_inspectors'].append(proof['inspector'])
            else:changed['source_native_inspectors'][0][flag]=True
            with pytest.raises(ValueError):before_interfaces_fields(identifier,changed)
    with pytest.raises(ValueError):before_interfaces_fields('ra.mri-neck-spaces',fields)


def test_actual_authenticated_module_reader_keeps_all_source_pixels_and_geometry():
    d=R/'docs/sellar-source-interfaces-review-20261101/reader'
    browser=json.loads((d/'browser-proof.json').read_bytes());pixels=json.loads((d/'mri-pixel-proof.json').read_bytes());camera=json.loads((d/'camera-proof.json').read_bytes())
    assert browser['allPassed']and browser['authenticatedAppVerified']and browser['syntheticLoopback']and not browser['productionLearnerWrites']
    assert not browser['productionVerified']and not browser['clinicalApproval']and browser['errors']==[]
    assert {(r['width'],r['identifier'])for r in browser['mounts']}=={(w,i)for w in [390,1440]for i in source.BINDINGS}
    assert all(r['reopened']for r in browser['mounts'])and browser['MRIStates']==576
    assert [len(r['meshes'])for r in browser['contextGPU']]==[21]*4
    assert pixels['allPassed']and pixels['states']==576 and pixels['actualCanvasPixelsCompared']==251854848
    assert pixels['crosshairLocationsChecked']==3456 and not pixels['sourceSamplesResampled']
    assert camera['allPassed']and camera['actualGPUUniformCameraStates']==720
    assert camera['allVisibleLayersUseIdenticalGPUCameraUniforms']and camera['wholeContextFramingStates']==432 and camera['contactOnlyFramingStates']==288
    for name,digest in browser['sourceSHA256'].items():
        assert hashlib.sha256((R/'web/anatomy'/source.ATLAS/'viewer'/name).read_bytes()).hexdigest()==digest
