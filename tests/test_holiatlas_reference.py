"""Exact source transport, thin production metadata and protected range delivery."""
from pathlib import Path
import hashlib
import copy
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
    for name in source.AUTHORED - {'manifest.json', 'labels.json', 'hierarchy.json'}:
        shutil.copy2(ROOT / 'web/anatomy/holiatlas' / name, assets / name)
    data = tmp_path / 'data/radiology'
    data.mkdir(parents=True)
    for name in ['holiatlas-reference.json', 'holiatlas-manifest.json.gz', 'holiatlas-labels.json.gz', 'holiatlas-hierarchy.json.gz']:
        shutil.copy2(ROOT / 'data/radiology' / name, data / name)
    expected = {name: source.metadata_bytes(name) for name in ['manifest.json', 'labels.json', 'hierarchy.json']}
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
 for name in ['index.html','manifest.json','labels.json','hierarchy.json','hierarchy-composition-right-insular-cortex.mesh.gz',row['file']]:
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


def test_every_thin_function_exclusion_has_a_static_delivery_build():
    import fnmatch
    config = json.loads((ROOT/'vercel.json').read_bytes())
    static = [row['src'] for row in config['builds'] if row.get('use') == '@vercel/static']
    excluded = [name for name in source.registry()['files']
                if name not in source.AUTHORED or name in {'manifest.json', 'labels.json', 'hierarchy.json'}]
    for name in excluded:
        path = 'web/anatomy/holiatlas/' + name
        assert any(fnmatch.fnmatchcase(path, pattern) for pattern in static), path


def test_hierarchy_preserves_source_scales_and_distinguishes_insula_from_opercula():
    hierarchy = json.loads(source.metadata_bytes('hierarchy.json'))
    assert {key: len(value['sourceClasses']) for key, value in hierarchy['levels'].items()} == {
        'structure': 53, 'tissue': 9, 'organ': 1, 'composition': 18}
    assert hierarchy['totalTriangles'] == 22598628
    assert sum(len(row['components26']) for level in hierarchy['levels'].values()
               for row in level['sourceClasses']) == 743
    right_insular_group = next(r for r in hierarchy['levels']['structure']['sourceClasses'] if r['code'] == 18)
    pure_insular = next(r for r in hierarchy['levels']['composition']['sourceClasses']
                       if r['sourceCompositionId'] == 'right-insular-cortex')
    assert right_insular_group['fineSourceCodes'] == [224, 226, 228, 230, 232]
    assert pure_insular['fineSourceCodes'] == [224, 230]
    assert pure_insular['voxels'] == 77649
    assert hierarchy['levels']['composition']['mutuallyExclusive'] is False
    for level in ('structure', 'tissue', 'organ'):
        assert hierarchy['levels'][level]['sourceHeaderUnits'] == ['unknown', 'unknown']
        assert hierarchy['levels'][level]['protocolMappingDisagreements'] == 0


@pytest.mark.parametrize('mutation', ['approval', 'count', 'membership', 'component', 'payload', 'partition', 'units'])
def test_hierarchy_rejects_unreviewed_scope_and_delivery_mutations(monkeypatch, mutation):
    original = source.metadata_bytes
    data = copy.deepcopy(source.registry())
    hierarchy = json.loads(original('hierarchy.json'))
    row = hierarchy['levels']['structure']['sourceClasses'][0]
    if mutation == 'approval':
        hierarchy['clinicalApproval'] = True
    elif mutation == 'count':
        hierarchy['presentClasses'] = data['hierarchy_classes'] = 78
    elif mutation == 'membership':
        row['fineSourceCodes'].append(65535)
    elif mutation == 'component':
        row['components26'].pop()
    elif mutation == 'payload':
        row['mesh']['gzipSHA256'] = '0' * 64
    elif mutation == 'partition':
        hierarchy['levels']['composition']['mutuallyExclusive'] = True
    else:
        hierarchy['levels']['structure']['sourceHeaderUnits'] = ['mm', 'unknown']
    monkeypatch.setattr(source, 'metadata_bytes', lambda name: json.dumps(hierarchy).encode()
                        if name == 'hierarchy.json' else original(name))
    with pytest.raises(ValueError):
        source.validate_hierarchy(data, json.loads(original('labels.json'))['sourceClasses'],
                                  json.loads(original('manifest.json')))
