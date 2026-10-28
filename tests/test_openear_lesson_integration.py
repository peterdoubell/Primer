"""Authenticated native OpenEar route, source grain and both actual lesson bindings."""
from tools.coordinate_plane_runtime_compatibility import before_coordinate_plane_bytes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def test_protected_exact_routes_csp_and_both_lesson_descriptors(tmp_path):
    env={key:value for key,value in os.environ.items()if not key.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'record.db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),
               PRIMER_BACKUP_DIR=str(tmp_path/'backups'),TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',
               PRIMER_ACCESS_USERNAME='synthetic-openear-route-test',PRIMER_ACCESS_PASSWORD='synthetic-test-password')
    script='''
from fastapi.testclient import TestClient
from primer import server,openear_native_reference as source
from primer.curriculum import Curriculum
import hashlib
credentials=('synthetic-openear-route-test','synthetic-test-password')
with TestClient(server.app)as client:
 for name in sorted(source.AUTHORED):
  assert client.get(source.PREFIX+name).status_code==401
  assert client.head(source.PREFIX+name).status_code==401
  response=client.get(source.PREFIX+name,auth=credentials)
  assert response.status_code==200,(name,response.status_code)
  assert hashlib.sha256(response.content).hexdigest()==source.registry()['files'][name]['sha256'],name
  assert response.headers['cache-control']=='private, no-store'
  head=client.head(source.PREFIX+name,auth=credentials)
  assert head.status_code==200 and head.content==b''
  if name=='index.html':
   directives={line.strip().split()[0]:line.strip().split()[1:]for line in response.headers['content-security-policy'].split(';')if line.strip()}
   assert directives['connect-src']==["'self'",source.BLOB_HOST]
   assert directives['frame-ancestors']==["'self'"]
 for name in ['%69ndex.html','registry.json','missing.pack','source-mesh-12.ply','originals/Bone.nrrd','%2e%2e/index.html']:
  assert client.get(source.PREFIX+name,auth=credentials).status_code==404,name
 curriculum=Curriculum()
 for node_id,investigation in [('rad.5.temporal-bone','ra.ct-temporal-bone'),('rad.5.tinnitus','ra.tinnitus')]:
  response=client.get('/api/radiology/modules/'+investigation,auth=credentials)
  assert response.status_code==200
  fields=response.json()['radiology_reference']
  matching=[row for row in fields['source_native_inspectors']if row['id']==source.IDENTIFIER]
  assert matching==[source.registry()['inspector']]
  assert all(matching[0][key]is False for key in source.FLAGS)
  assert matching[0]['modality'].startswith('Registered source CBCT')
  assert matching[0]['source_grain']['originalSegmentationChannels']==13
  assert matching[0]['source_grain']['separateFullBoneMask']is True
  assert matching[0]['source_grain']['sourceIntensityIsVerifiedHU']is False
  assert matching[0]['source_grain']['effectiveSpatialResolutionEstablished']is False
  media=[row for row in curriculum.node(node_id)['lesson_media']if row['kind']=='source-native-inspectors']
  assert len(media)==1 and media[0]['investigation_ids']==[investigation],node_id
'''
    run=subprocess.run([sys.executable,'-c',script],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
    assert run.returncode==0,run.stdout+run.stderr


def test_recorded_authenticated_lesson_proof_matches_current_inputs():
    folder=ROOT/'docs/openear-native-review-20261027/lesson'
    proof=json.loads((folder/'proof.json').read_bytes())
    assert proof['allPassed'] and proof['syntheticLoopback'] and not proof['productionLearnerWrites']
    assert proof['errors']==[]
    assert {(row['nodeId'],row['width'])for row in proof['mounts']}=={(node,width)for node in ['rad.5.temporal-bone','rad.5.tinnitus']for width in [390,1440]}
    for name,digest in proof['files'].items():
        assert hashlib.sha256(before_coordinate_plane_bytes(name,(ROOT/name).read_bytes())).hexdigest()==digest,name
    for mount in proof['mounts']:
        assert mount['openedAndClosed'] and mount['schematicOverlapModeVerified']
        assert mount['credentialScope']=='loopback app origin only'
        assert {(s['code'],s['contrast'])for s in mount['states']}=={(code,contrast)for code in [4,13]for contrast in ['embedded','unembedded']}
        assert all(not s['overflow'] and s['display']=='cbct' for s in mount['states'])
        assert {g['meshId']for g in mount['gpu']}=={'openear-zeta-part4','openear-zeta-part12'}
        assert all(g['error']==0 for g in mount['gpu'])
        assert next(g for g in mount['gpu']if g['code']==13)['triangles']==7120812
    assert proof['responses'] and all(r['status']==(206 if r['range']else 200)for r in proof['responses'])
