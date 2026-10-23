"""Exact source transport, thin production metadata and protected range delivery."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import pytest
from primer import holiatlas_reference as source

ROOT = Path(__file__).resolve().parents[1]


def test_reference_preserves_source_meaning_and_all_present_components():
    item = source.references()['ra.brain-anatomy'][0]
    assert all(item[key] is False for key in source.FLAGS)
    assert item['source_grain']['WMn_like_contrast_synthesized'] is True
    assert item['source_grain']['sulcal_classes_are_CSF_territories'] is True
    labels = json.loads(source.metadata_bytes('labels.json'))
    assert [labels[k] for k in ('presentClasses', 'missingNamedClasses', 'components26')] == [332, 18, 868]
    for row in labels['sourceClasses']:
        if not row['voxels']:
            assert row['missingSourceLabel'] and not row['components26']
        else:
            for component in row['components26']:
                assert component['focusSourceWorld'] == [v * .5 + origin for v, origin in
                    zip(component['focusSourceIJK'], [-90, -126, -72])]
    for name in ['../index.html', '%69ndex.html', 'missing.pack']:
        with pytest.raises(ValueError):
            source.validate_file(name)


def test_runtime_metadata_is_lossless_without_static_payloads(tmp_path, monkeypatch):
    assets = tmp_path / 'web/anatomy/holiatlas'
    assets.mkdir(parents=True)
    for name in source.AUTHORED - {'manifest.json', 'labels.json'}:
        shutil.copy2(ROOT / 'web/anatomy/holiatlas' / name, assets / name)
    data = tmp_path / 'data/radiology'
    data.mkdir(parents=True)
    for name in ['holiatlas-reference.json', 'holiatlas-manifest.json.gz', 'holiatlas-labels.json.gz']:
        shutil.copy2(ROOT / 'data/radiology' / name, data / name)
    expected = {name: source.metadata_bytes(name) for name in ['manifest.json', 'labels.json']}
    monkeypatch.setattr(source, 'ROOT', tmp_path)
    monkeypatch.setattr(source, 'REGISTRY', data / 'holiatlas-reference.json')
    monkeypatch.setenv('VERCEL', '1')
    for function in [source.registry, source.metadata_bytes, source.references]:
        function.cache_clear()
    try:
        assert source.references()['ra.brain-anatomy'][0]['id'] == source.IDENTIFIER
        for name, raw in expected.items():
            assert source.metadata_bytes(name) == raw
            assert not (assets / name).exists()
    finally:
        for function in [source.registry, source.metadata_bytes, source.references]:
            function.cache_clear()


def test_authenticated_route_preserves_range_bytes_and_rejects_path_aliases(tmp_path):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('TURSO', 'PRIMER_ACCESS_', 'VERCEL', 'BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path/'record.db'), PRIMER_CONTENT_DIR=str(tmp_path/'content'),
               PRIMER_BACKUP_DIR=str(tmp_path/'backups'), TURSO_DATABASE_URL='', TURSO_AUTH_TOKEN='',
               PRIMER_ACCESS_USERNAME='synthetic-holiatlas-test', PRIMER_ACCESS_PASSWORD='synthetic-test-password')
    script = '''
import os,json,hashlib
from fastapi.testclient import TestClient
from primer import server,holiatlas_reference as source
auth=('synthetic-holiatlas-test','synthetic-test-password')
manifest=json.loads(source.metadata_bytes('manifest.json'));row=manifest['volumes']['T1']['planes']['2'][0]
with TestClient(server.app) as client:
 for name in ['index.html','manifest.json','labels.json',row['file']]:
  assert client.get(source.PREFIX+name).status_code==401
  response=client.get(source.PREFIX+name,auth=auth);assert response.status_code==200
  assert response.headers['cache-control']=='private, no-store'
  if name=='index.html':assert "frame-ancestors 'self'" in response.headers['content-security-policy']
 for name in ['missing.pack','%69ndex.html']:
  assert client.get(source.PREFIX+name,auth=auth).status_code==404
 response=client.get(source.PREFIX+row['file'],auth=auth,headers={'Range':f"bytes={row['offset']}-{row['offset']+row['gzipBytes']-1}"})
 assert response.status_code==206
 assert response.headers['content-range']==f"bytes {row['offset']}-{row['offset']+row['gzipBytes']-1}/{manifest['packs'][row['file']]['bytes']}"
 assert hashlib.sha256(response.content).hexdigest()==row['gzipSHA256']
 os.environ['VERCEL']='1'
 response=client.get(source.PREFIX+row['file'],auth=auth,follow_redirects=False)
 assert response.status_code==307 and response.headers['location']=='/source-media/anatomy/holiatlas/'+row['file']
 reference=client.get('/api/radiology/modules/ra.brain-anatomy',auth=auth).json()['radiology_reference']
 ids={r['id'] for r in reference['source_native_inspectors']}
 assert {'holiatlas-source-template-reference','spl-nac-reporting-native-reference','spl-nac-limbic-native-reference'}<=ids
'''
    result = subprocess.run([sys.executable, '-B', '-c', script], cwd=ROOT, env=env,
                            text=True, capture_output=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
