"""Native atlas inspection reaches its exact lesson and retains source byte gates."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media
from primer import radiology_catalog
from primer import source_native_inspectors as native
from tools.anatomy_sources.brain_native_delivery_amendment import restored_historical_contract, MEDIA

ROOT = Path(__file__).resolve().parents[1]


def test_native_inspector_reaches_only_matching_brain_lesson_and_source_model():
    curriculum = Curriculum()
    node = curriculum.node('rad.5.brain-anatomy')
    _validate_lesson_media(node)
    assert [m for m in node['lesson_media'] if m['kind'] == 'source-native-inspectors'] == [MEDIA]
    assert all(not any(m['kind'] == 'source-native-inspectors' for m in n['lesson_media'])
               for n in curriculum.nodes.values() if n['id'] not in {node['id'], 'rad.4.stroke', 'rad.4.pulmonary-nodule', 'rad.5.pleura', 'rad.5.cardiac-mri', 'rad.5.coronary-ct', 'rad.5.cardiac-masses-devices'})
    thoracic = curriculum.node('rad.5.pleura')
    thoracic_media, = [m for m in thoracic['lesson_media'] if m['kind'] == 'source-native-inspectors']
    assert thoracic_media['investigation_ids'] == ['ra.thoracic-ultrasound']
    thoracic_model = next(m for m in thoracic['lesson_media'] if m.get('renderer') == 'radiology-anatomy')
    assert thoracic_model['props']['source_native_only'] is True
    assert [m['id'] for m in thoracic_model['props']['native_inspectors']] == ['bp3d-thoracic-original-surfaces','totalseg-s0028-lung-native','totalseg-s0028-basal-context','totalseg-v1-s0028-cardiac-native', 'bp3d-cardiac-original-context', 'baskaran-2020-cardiac-comparisons']
    pulmonary = curriculum.node('rad.4.pulmonary-nodule')
    pulmonary_media, = [m for m in pulmonary['lesson_media'] if m['kind'] == 'source-native-inspectors']
    assert pulmonary_media['investigation_ids'] == ['ra.ct-pulmonary-nodules']
    pulmonary_model = next(m for m in pulmonary['lesson_media'] if m.get('renderer') == 'radiology-anatomy')
    assert pulmonary_model['props']['source_native_only'] is True
    assert [m['id'] for m in pulmonary_model['props']['native_inspectors']] == ['lidc-idri-0525-native']
    stroke = curriculum.node('rad.4.stroke')
    stroke_inspector, = [m for m in stroke['lesson_media'] if m['kind'] == 'source-native-inspectors']
    assert stroke_inspector['investigation_ids'] == ['ra.acute-stroke']
    ref = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.brain-anatomy'))['radiology_reference']
    inspector, = ref['source_native_inspectors']
    assert inspector['bound_source_ids'] == ['massp2-subcortical-reference']
    assert not inspector['clinical_approval'] and not inspector['fine_anatomical_approval']
    model = next(m for m in node['lesson_media'] if m.get('renderer') == 'radiology-anatomy')
    assert len(model['props']['source_references']) == 2


@pytest.mark.parametrize('field,value', [('investigation_ids',['ra.mri-myelopathy']),
                                        ('title','Complete clinical anatomy approval'),
                                        ('id','another-inspector')])
def test_historical_scope_rejects_any_unreviewed_inspector_amendment(field,value):
    contract = {'lesson_media':[copy.deepcopy(MEDIA)]}
    contract['lesson_media'][0][field] = value
    with pytest.raises(ValueError,match='Unreviewed'):
        restored_historical_contract(contract,'rad.5.brain-anatomy')


def test_registered_payload_packet_matches_source_manifest_and_hosted_identity():
    manifest = json.loads((ROOT/'web/anatomy/brain-fine-massp2/manifest.json').read_text())
    arrays = [manifest['labels'],*manifest['contrasts'].values(),*manifest['probabilities'].values()]
    delivered = native.delivery()['files']
    assert len(arrays) == len(delivered) == 14
    assert sum(row['bytes'] for row in arrays) == 17434638
    for row in arrays:
        raw = (ROOT/'web'/row['file'].removeprefix('/app/')).read_bytes()
        assert len(raw) == delivered[row['file']]['bytes'] == row['bytes']
        assert hashlib.sha256(raw).hexdigest() == row['sha256'] == delivered[row['file']]['sha256']
        assert row['sha256'] in delivered[row['file']]['url']


def test_actual_get_head_auth_redirect_and_unknown_routes(tmp_path):
    env={k:v for k,v in os.environ.items() if not k.startswith('TURSO')
         and k not in {'VERCEL','VERCEL_ENV','PRIMER_ACCESS_USERNAME','PRIMER_ACCESS_PASSWORD'}}
    env.update(PRIMER_DB=str(tmp_path/'native.db'),PRIMER_BACKUP_DIR=str(tmp_path/'backups'))
    script=r'''
import hashlib,os
from fastapi import FastAPI
from fastapi.testclient import TestClient
import primer.server as server
from primer.source_native_inspectors import delivery
files=delivery()['files']
host=delivery()['blob_hostname']
with TestClient(server.app,follow_redirects=False) as client:
 for src,row in files.items():
  get=client.get(src);head=client.head(src)
  assert get.status_code==head.status_code==200
  assert len(get.content)==row['bytes'] and hashlib.sha256(get.content).hexdigest()==row['sha256']
  assert head.content==b'' and int(head.headers['content-length'])==row['bytes']
 html=client.get('/app/anatomy/brain-fine-massp2/reference.html')
 assert "connect-src 'self' https://"+host+";" in html.headers['content-security-policy']
 attribution=client.get('/app/anatomy/brain-fine-massp2/ATTRIBUTION.md')
 assert attribution.status_code==200 and attribution.headers['content-security-policy']==server.CSP
 assert attribution.content==open('web/anatomy/brain-fine-massp2/ATTRIBUTION.md','rb').read()
 assert client.get('/app/math-topology-lab.js').headers['content-security-policy']==server.CSP
 assert client.get('/app/anatomy/brain-fine-massp2/unknown.gz').status_code==404
 os.environ['VERCEL']='1';os.environ[server.ACCESS_USERNAME_ENV]='native-reader';os.environ[server.ACCESS_PASSWORD_ENV]='test-password'
 for src in files:assert client.get(src).status_code==401
 assert client.get('/app/anatomy/brain-fine-massp2/ATTRIBUTION.md').status_code==401
 # Production DB fail-closed behavior is independent of this source handler.
 app=FastAPI();app.add_api_route('/app/anatomy/brain-fine-massp2/{asset}',server.native_brain_payload_delivery,methods=['GET','HEAD'])
 with TestClient(app,follow_redirects=False) as handler:
  for src,row in files.items():
   for method in [handler.get,handler.head]:
    response=method(src);assert response.status_code==307 and response.headers['location']==row['url']
    assert response.headers['cache-control']=='private, no-store'
  assert handler.get('/app/anatomy/brain-fine-massp2/unknown.gz').status_code==404
print('14 exact native payload GET/HEAD routes, hosted auth gate, static redirects and unknown rejection passed')
'''
    result=subprocess.run([sys.executable,'-c',script],cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stdout+result.stderr
    assert '14 exact native payload' in result.stdout
