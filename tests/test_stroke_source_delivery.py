"""Exact stroke source identities, private delivery and isolated native viewer access."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from primer import stroke_source_delivery as stroke
from primer import stroke_native_inspectors as native

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('change', ['project', 'store', 'hostname', 'ctp_review', 'soop_review', 'case',
                                  'module', 'investigation', 'proposal', 'missing', 'total', 'url_host', 'url_userinfo',
                                  'url_query', 'url_fragment', 'url_hash', 'source_path', 'role', 'mime',
                                  'license', 'bytes', 'sha', 'changed_values', 'original_changed',
                                  *stroke.APPROVAL_FLAGS])
def test_stroke_metadata_rejects_unreviewed_identity_or_approval(change, tmp_path, monkeypatch):
    data = json.loads(stroke.REGISTRY.read_text())
    src = next(src for src, row in data['files'].items() if row['role'] == 'source_original')
    row = data['files'][src]
    if change in {'project', 'store', 'hostname'}:
        data[{'project': 'project_id', 'store': 'store_id', 'hostname': 'blob_hostname'}[change]] = 'other'
    elif change in {'ctp_review', 'soop_review'}:
        data['independent_' + ('ctp' if change == 'ctp_review' else 'soop') + '_source_review_sha256'] = '0' * 64
    elif change == 'case':
        data['soop_pinned_root_tree'] = '0' * 40
    elif change == 'proposal':
        data['soop_source_proposal_sha256'] = '0' * 64
    elif change in {'module', 'investigation'}:
        data[change + '_id'] = 'other'
    elif change == 'missing':
        del data['files'][src]
    elif change == 'total':
        data['total_bytes'] += 1
    elif change == 'url_host':
        row['url'] = row['url'].replace(stroke.BLOB_HOST, 'unreviewed.example')
    elif change == 'url_userinfo':
        row['url'] = row['url'].replace('https://', 'https://reader@')
    elif change == 'url_query':
        row['url'] += '?other=1'
    elif change == 'url_fragment':
        row['url'] += '#other'
    elif change == 'url_hash':
        row['url'] = row['url'].replace(row['sha256'], '0' * 64)
    elif change == 'source_path':
        data['files'][stroke.NATIVE_PREFIX + 'nested/' + Path(src).name] = data['files'].pop(src)
    elif change == 'role':
        row['role'] = 'complete_native_storage_array'
    elif change == 'mime':
        row['content_type'] = 'text/html'
    elif change == 'license':
        row['license'] = 'CC BY-NC 4.0'
    elif change == 'bytes':
        row['bytes'] = True
    elif change == 'sha':
        row['sha256'] = 'unreviewed'
    elif change == 'changed_values':
        row['source_values_changed'] = True
    elif change == 'original_changed':
        row['source_original_bytes_changed'] = True
    else:
        row[change] = True
    registry = tmp_path / 'registry.json'
    registry.write_text(json.dumps(data))
    monkeypatch.setattr(stroke, 'REGISTRY', registry)
    monkeypatch.setattr(stroke, 'REGISTRY_SHA256', hashlib.sha256(registry.read_bytes()).hexdigest())
    monkeypatch.setattr(stroke, 'ROOT', tmp_path)
    monkeypatch.setenv('VERCEL', '1')
    stroke.delivery.cache_clear()
    try:
        with pytest.raises(ValueError):
            stroke.delivery()
    finally:
        stroke.delivery.cache_clear()


@pytest.mark.parametrize('change', ['binding', 'id', 'module', 'investigation', 'source', 'license',
                                  'array_original', 'array_transport', 'array_frame', 'array_affine', 'array_dtype', 'array_size',
                                  'mesh_source', 'mesh_role', 'mesh_approval', 'registration', 'crop',
                                  *stroke.APPROVAL_FLAGS])
def test_native_inspector_rejects_source_link_scope_and_approval_changes(change, tmp_path, monkeypatch):
    data = json.loads(native.REGISTRY.read_text())
    manifest = json.loads((ROOT / 'web/anatomy/soop-stroke-sub342/manifest.json').read_text())
    item = data['inspectors']['soop-stroke-sub342-native']
    if change == 'binding':
        data['bindings'] = {'ra.brain-anatomy': ['soop-stroke-sub342-native']}
    elif change == 'id':
        item['id'] = 'other'
    elif change in {'module', 'investigation'}:
        item[change + '_id'] = 'other'
    elif change == 'source':
        item['source_url'] = 'https://example.com/other-source'
    elif change == 'license':
        item['license'] = 'CC BY-NC 4.0'
    elif change == 'array_original':
        manifest['arrays']['trace']['source_file'] = manifest['arrays']['adc']['source_file']
    elif change == 'array_transport':
        manifest['arrays']['trace']['file'] = manifest['arrays']['adc']['file']
    elif change == 'array_frame':
        manifest['arrays']['trace']['frames'] += 1
    elif change == 'array_affine':
        manifest['arrays']['trace']['affine'][0][0] = float('inf')
    elif change == 'array_dtype':
        manifest['arrays']['trace']['dtype'] = '<f8'
    elif change == 'array_size':
        manifest['arrays']['trace']['decoded_bytes'] -= 2
    elif change == 'mesh_source':
        manifest['meshes']['acute']['source_mask_sha256'] = manifest['arrays']['chronic']['source_file_sha256']
    elif change == 'mesh_role':
        manifest['meshes']['acute']['source_mask_role'] = 'combined'
    elif change == 'mesh_approval':
        manifest['meshes']['acute']['clinical_or_named_anatomical_boundary_approval'] = True
    elif change == 'registration':
        manifest['T1_registered_to_diffusion'] = True
    elif change == 'crop':
        manifest['complete_arrays_no_crop'] = False
    else:
        item[change] = True
    directory = tmp_path / 'web/anatomy/soop-stroke-sub342'
    directory.mkdir(parents=True)
    for name in ['reference.html', 'reference.js']:
        (directory / name).write_bytes((ROOT / 'web/anatomy/soop-stroke-sub342' / name).read_bytes())
    (directory / 'manifest.json').write_text(json.dumps(manifest))
    item['manifest_sha256'] = hashlib.sha256((directory / 'manifest.json').read_bytes()).hexdigest()
    registry = tmp_path / 'inspector.json'
    registry.write_text(json.dumps(data))
    monkeypatch.setattr(native, 'ROOT', tmp_path)
    monkeypatch.setattr(native, 'REGISTRY', registry)
    monkeypatch.setattr(native, 'REGISTRY_SHA256', hashlib.sha256(registry.read_bytes()).hexdigest())
    native.references.cache_clear()
    try:
        with pytest.raises(ValueError):
            native.references()
    finally:
        native.references.cache_clear()


def test_exact_public_redirects_exclusions_and_original_brain_packets_are_preserved():
    delivery = stroke.delivery()
    routes = json.loads((ROOT / 'vercel.json').read_text())['routes']
    matching = [r for r in routes if r.get('dest', '').startswith((stroke.PUBLICATION_BLOB_PREFIX, stroke.NATIVE_BLOB_PREFIX))]
    assert len(matching) == 48
    for src, row in delivery['files'].items():
        public = '/source-media/' + src.removeprefix('/app/')
        route, = [r for r in matching if re.fullmatch(r['src'], public)]
        assert route['dest'] == row['url'] and route['status'] == 307
        assert route['headers']['Cache-Control'] == 'public, max-age=31536000, immutable'
    assert not any(re.fullmatch(r['src'], '/source-media/anatomy/soop-stroke-sub342/unknown.gz') for r in matching)
    ignored = (ROOT / '.vercelignore').read_text()
    assert '\nweb/reference-media/radiology-open/acute-stroke\n' in ignored
    assert 'web/anatomy/soop-stroke-sub342/*.gz' in ignored
    assert 'web/anatomy/soop-stroke-sub342/sub-342*.json' in ignored
    original = subprocess.run(['git', 'show', 'HEAD:data/radiology/native-source-delivery.json'], cwd=ROOT, capture_output=True, check=True).stdout
    assert (ROOT / 'data/radiology/native-source-delivery.json').read_bytes() == original
    original = subprocess.run(['git', 'show', 'HEAD:data/radiology/native-source-inspectors.json'], cwd=ROOT, capture_output=True, check=True).stdout
    assert (ROOT / 'data/radiology/native-source-inspectors.json').read_bytes() == original


def test_actual_private_get_head_hosted_fixed_redirects_and_isolated_browser_policy(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith('TURSO')
           and k not in {'VERCEL', 'VERCEL_ENV', 'PRIMER_ACCESS_USERNAME', 'PRIMER_ACCESS_PASSWORD'}}
    env.update(PRIMER_DB=str(tmp_path / 'stroke.db'), PRIMER_BACKUP_DIR=str(tmp_path / 'backups'))
    script = r'''
import hashlib,os
from fastapi import FastAPI
from fastapi.testclient import TestClient
import primer.server as server
from primer.stroke_source_delivery import delivery,PUBLICATION_PREFIX,NATIVE_PREFIX,PUBLICATION_BLOB_PREFIX,NATIVE_BLOB_PREFIX
files=delivery()['files'];auth=('stroke-reader','fixture-password')
os.environ[server.ACCESS_USERNAME_ENV]=auth[0];os.environ[server.ACCESS_PASSWORD_ENV]=auth[1]
with TestClient(server.app,follow_redirects=False) as client:
 for src,row in files.items():
  for method in [client.get,client.head]:assert method(src).status_code==401
  get=client.get(src,auth=auth);head=client.head(src,auth=auth)
  assert get.status_code==head.status_code==200,(src,get.status_code)
  assert len(get.content)==row['bytes'] and hashlib.sha256(get.content).hexdigest()==row['sha256']
  assert head.content==b'' and int(head.headers['content-length'])==row['bytes']
  assert 'content-encoding' not in get.headers
 for prefix in [PUBLICATION_PREFIX,NATIVE_PREFIX]:
  for suffix in ['unknown.gz','nested/reference.html','reference.html/','%2Freference.html','../unknown.gz']:
   assert client.get(prefix+suffix,auth=auth).status_code==404,(prefix,suffix)
 html=client.get(NATIVE_PREFIX+'reference.html',auth=auth)
 assert html.status_code==200
 assert "connect-src 'self' "+NATIVE_BLOB_PREFIX+";" in html.headers['content-security-policy']
 assert "connect-src 'self' https://ja2lsnp9uca4bivw.public.blob.vercel-storage.com;" not in html.headers['content-security-policy']
 ordinary=client.get('/app/index.html',auth=auth).headers['content-security-policy']
 assert "connect-src 'self';" in ordinary and PUBLICATION_BLOB_PREFIX in ordinary
 assert NATIVE_BLOB_PREFIX not in ordinary
 for name in ['reference.js','manifest.json']:
  response=client.get(NATIVE_PREFIX+name,auth=auth);assert response.status_code==200 and response.headers['content-security-policy']==server.CSP
 os.environ['VERCEL']='1'
 for src in files:
  for method in [client.get,client.head]:assert method(src).status_code==401
 app=FastAPI();app.add_api_route(PUBLICATION_PREFIX+'{asset:path}',server.stroke_publication_blob_delivery,methods=['GET','HEAD']);app.add_api_route(NATIVE_PREFIX+'{asset:path}',server.native_stroke_payload_delivery,methods=['GET','HEAD'])
 with TestClient(app,follow_redirects=False) as handler:
  for src,row in files.items():
   for method in [handler.get,handler.head]:
    response=method(src+'?url=https://unreviewed.example/other',headers={'Host':'other.example'})
    assert response.status_code==307 and response.headers['location']==row['url']
    assert response.headers['cache-control']=='private, no-store'
  for prefix in [PUBLICATION_PREFIX,NATIVE_PREFIX]:
   assert handler.get(prefix+'unknown.gz').status_code==404
   assert handler.get(prefix+'nested/unknown.gz').status_code==404
print('48 exact originals, private GET/HEAD/auth and fixed hosted redirects passed')
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=env, capture_output=True, text=True, timeout=160)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '48 exact originals' in result.stdout
