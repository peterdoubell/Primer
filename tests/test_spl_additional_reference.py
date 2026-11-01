"""Source preservation, protected delivery and scoped application integration."""
from pathlib import Path
import copy
import gzip
import hashlib
import json
import os
import subprocess
import sys
import pytest
from primer import spl_additional_reference as source
from tools.spl_additional_runtime_compatibility import reviewed, before_additional_bytes, before_additional_fields

R=Path(__file__).resolve().parents[1]
D=R/'docs/spl-additional-source-review-20261101'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def test_publisher_geometry_retains_original_positions_and_every_strip_triangle(tmp_path):
    from tools.anatomy_sources.spl_additional_vtk import parse_additional_vtk
    from tools.anatomy_sources.spl_limbic_source import pack_mesh
    source.references()
    manifest=json.loads(source.manifest_bytes())
    rows=json.loads((D/'original-surfaces/acquisition.json').read_bytes())['rows']
    publisher={row['code']:row for row in manifest['publisherMeshes']}
    assert len(rows)==94
    for row in rows:
        name=Path(row['file']).name
        original=gzip.decompress((D/'originals'/(name+'.gz')).read_bytes())
        assert sha(original)==row['sha256']
        assert hashlib.sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()==row['gitBlobSHA1']
        path=tmp_path/name;path.write_bytes(original)
        parsed=parse_additional_vtk(path)
        payload,_,_=pack_mesh(parsed)
        mesh=publisher[row['code']]
        actual=gzip.decompress(source.validate_file(mesh['file']).read_bytes())
        assert actual==payload
        assert mesh['sourceOriginalSHA256']==sha(original)
        assert mesh['sourceOriginalGitBlobSHA1']==row['gitBlobSHA1']
    discrepancy=json.loads((D/'original-surfaces/4084-component-review.json').read_bytes())
    assert discrepancy['sourceModelLabelCorrespondenceResolved']is False
    assert discrepancy['allSourceGeometryPreserved']is True
    assert discrepancy['components'][0]['triangles']==8
    assert discrepancy['components'][0]['vertexToSameCodeCellCenterDistanceMm']['max']>34
    assert publisher[4084]['sourceLabelCorrespondenceUnresolved']is True


def test_protected_routes_and_module_bindings(tmp_path):
    env={k:v for k,v in os.environ.items()if not k.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backups'),TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_ACCESS_USERNAME='synthetic-additional',PRIMER_ACCESS_PASSWORD='synthetic-password')
    code='''
from fastapi.testclient import TestClient
from primer import server,spl_additional_reference as c
import hashlib,gzip
with TestClient(server.app)as client:
 auth=('synthetic-additional','synthetic-password')
 for asset in ['index.html','manifest.json','publisher-4084.mesh.gz','label-85.mesh.gz']:
  assert client.get(c.PREFIX+asset).status_code==401
 for asset in ['index.html','manifest.json','viewer.js','LICENSE.txt','ATTRIBUTION.txt','publisher-4084.mesh.gz','label-85.mesh.gz','label-85-faces.bin.gz']:
  response=client.get(c.PREFIX+asset,auth=auth);assert response.status_code==200
  expected=c.validate_file(asset).read_bytes() if asset!='manifest.json' else c.manifest_bytes()
  assert response.content==(gzip.decompress(expected) if asset.endswith('.bin.gz') else expected)
  assert response.headers['cache-control']=='private, no-store'
  assert client.head(c.PREFIX+asset,auth=auth).content==b''
  if asset=='index.html':assert "frame-ancestors 'self'"in response.headers['content-security-policy']
 for asset in ['%69ndex.html','registry.json','missing.gz','../spl-additional-reference.json']:
  assert client.get(c.PREFIX+asset,auth=auth).status_code==404
 for identifier in [*c.BINDINGS,'ra.mri-epilepsy','ra.paediatric-neck-masses','ra.head-neck-malignancy']:
  response=client.get('/api/radiology/modules/'+identifier,auth=auth);assert response.status_code==200
  found=[i for i in response.json()['radiology_reference'].get('source_native_inspectors',[])if i['id']==c.IDENTIFIER]
  assert found==([c.registry()['inspector']]if identifier in c.BINDINGS else [])
'''
    result=subprocess.run([sys.executable,'-c',code],cwd=R,env=env,capture_output=True,text=True,timeout=180)
    assert result.returncode==0,result.stdout+result.stderr


def test_historical_projection_rejects_changes_duplicates_and_scope_drift():
    proof=reviewed()
    for name,row in proof['files'].items():
        raw=(R/name).read_bytes();before=before_additional_bytes(name,raw)
        assert sha(before)==row['before_sha256']
        assert before_additional_bytes(name,before)==before
        with pytest.raises(ValueError):before_additional_bytes(name,raw+b'unreviewed')
    fields={'source_native_inspectors':[proof['inspector']]}
    for identifier in source.BINDINGS:
        assert before_additional_fields(identifier,fields)=={'source_native_inspectors':[]}
        for mutation in ['duplicate','caption','clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved']:
            changed=copy.deepcopy(fields)
            if mutation=='duplicate':changed['source_native_inspectors'].append(proof['inspector'])
            elif mutation=='caption':changed['source_native_inspectors'][0][mutation]+=' unreviewed'
            else:changed['source_native_inspectors'][0][mutation]=True
            with pytest.raises(ValueError):before_additional_fields(identifier,changed)
    with pytest.raises(ValueError):before_additional_fields('ra.paediatric-neck-masses',fields)


def test_authenticated_app_and_independent_native_pixel_evidence():
    browser=json.loads((D/'reader/pixel-browser-proof.json').read_bytes())
    pixels=json.loads((D/'reader/pixel-proof.json').read_bytes())
    assert browser['allPassed']and browser['syntheticLoopback']and not browser['productionLearnerWrites']
    assert not browser['productionVerified']and not browser['clinicalApproval']and browser['errors']==[]
    assert {(row['width'],row['identifier'])for row in browser['mounts']}=={(width,identifier)for width in [390,1440]for identifier in source.BINDINGS}
    assert all(row['reopened']for row in browser['mounts'])
    assert [row['meshes']for row in browser['gpu']]==[188,188]
    assert all(row['originalPositionIndexWorldBytesMatched']for row in browser['gpu'])
    assert pixels['allPassed']and pixels['cases']==1128 and pixels['actualCanvasPixelsCompared']==82202624
    assert pixels['originalSourceClasses']==94 and not pixels['sourceResampled']and not pixels['anatomicalVisibilityVerified']
    for name,digest in browser['sourceSHA256'].items():
        assert sha((R/'web/anatomy/spl-additional-source'/name).read_bytes())==digest
    index=json.loads((D/'evidence-index.json').read_bytes())
    for name,digest in index['sourceSHA256'].items():assert sha((R/name).read_bytes())==digest,name
    for name,digest in index['proofSHA256'].items():assert sha((D/name).read_bytes())==digest,name
    assert not index['clinicalApproval']and not index['wholeGoalComplete']
