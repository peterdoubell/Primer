"""The Pat9 viewer retains its reviewed source scope and authenticated routes."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_pat9_reporting_source_and_viewer_delivery(tmp_path):
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(('TURSO', 'PRIMER_ACCESS_', 'VERCEL', 'BLOB_'))
    }
    env.update(
        PRIMER_DB=str(tmp_path / 'reader.db'),
        PRIMER_CONTENT_DIR=str(tmp_path / 'content'),
        PRIMER_BACKUP_DIR=str(tmp_path / 'backups'),
        PRIMER_ACCESS_USERNAME='synthetic-lynos-reader',
        PRIMER_ACCESS_PASSWORD='fixture-only',
    )
    script = """
import os
from fastapi.testclient import TestClient
from primer import lynos_pat9_reference as source
from primer.server import app, MESH_SOURCE_DIRECTORIES, NODE_SOURCE_ATLASES

expected = {
    'recist-pelvic-015', 'recist-pelvic-023',
    'recist-pelvic-023-follow-up-1', 'recist-pelvic-023-follow-up-2',
    'lnq-case-0571', source.ATLAS, 'aneurysm-cta-018', 'cmha-mca-005',
    'rhuh-sah-001', 'bp3d-dural-4.3', 'ward-swi-s1', 'illinois-uterus',
    'endometriosis-mri-evidence', 'hyperpic-venous', 'venat', 'ccth-a01-roi',
}
assert set(MESH_SOURCE_DIRECTORIES) == expected and len(expected) == 16
assert all(value == 'anatomy/' + name for name, value in MESH_SOURCE_DIRECTORIES.items())
assert NODE_SOURCE_ATLASES == frozenset({
    'recist-pelvic-015', 'recist-pelvic-023',
    'recist-pelvic-023-follow-up-1', 'recist-pelvic-023-follow-up-2',
    'lnq-case-0571', source.ATLAS,
})

auth = ('synthetic-lynos-reader', 'fixture-only')
prefix = '/app/anatomy/' + source.ATLAS + '/'
with TestClient(app) as client:
    assert client.get('/healthz').json()['source_native_inspector_metadata_validated']
    for atlas, directory in MESH_SOURCE_DIRECTORIES.items():
        manifest = client.get('/app/' + directory + '/delivery.json', auth=auth)
        assert manifest.status_code == 200, atlas
        files = manifest.json()['files']
        for asset in files:
            if not asset.endswith('.html'):
                continue
            page = client.head('/app/' + directory + '/' + asset, auth=auth)
            assert page.status_code == 200, (atlas, asset)
            may_embed = atlas in NODE_SOURCE_ATLASES and asset in {'index.html', 'surfaces.html', 'comparison.html'}
            expected_policy = "frame-ancestors 'self';" if may_embed else "frame-ancestors 'none';"
            assert expected_policy in page.headers['content-security-policy'], (atlas, asset)
    for investigation, expected in source.references().items():
        response = client.get('/api/radiology/modules/' + investigation, auth=auth)
        assert response.status_code == 200
        rows = response.json()['radiology_reference']['source_native_inspectors']
        assert [item['id'] for item in rows] == ['lnq-case-0571', source.ATLAS]
        assert [item for item in rows if item['id'] == source.ATLAS] == expected
        assert not expected[0]['clinical_approval']
    for page in ('index.html', 'surfaces.html'):
        for method in ('GET', 'HEAD'):
            assert client.request(method, prefix + page).status_code == 401
            response = client.request(method, prefix + page, auth=auth)
            assert response.status_code == 200
            policy = response.headers['content-security-policy']
            assert "frame-ancestors 'self';" in policy and "connect-src 'self';" in policy
    assert client.get(prefix + 'unlisted.html', auth=auth).status_code == 404
    metadata = client.get(prefix + 'source.json', auth=auth).json()
    assert metadata['shapeSliceRowColumn'] == [241, 512, 512]
    assert metadata['nodalLabels'][18]['primaryStationLiteral'] == '11L - Interlobar (Right)'
    assert metadata['nodalLabels'][20]['primaryStationLiteral'] == 'Undefined - Outside the scope of IASLC'
    for script in ('native-sections.mjs', 'mask-map.mjs'):
        assert client.get(prefix + script).status_code == 401
        response = client.get(prefix + script, auth=auth)
        assert response.status_code == 200
        assert 'javascript' in response.headers['content-type']
    assert client.get(prefix + 'mask-map.css').status_code == 401
    stylesheet = client.get(prefix + 'mask-map.css', auth=auth)
    assert stylesheet.status_code == 200
    assert 'text/css' in stylesheet.headers['content-type']
    result = client.get(prefix + 'ct-240.gz', auth=auth, headers={'Range': 'bytes=0-15'})
    assert result.status_code == 206 and result.content.startswith(b'\\x1f\\x8b')
    assert "frame-ancestors 'none';" in client.get('/app/', auth=auth).headers['content-security-policy']
    os.environ['VERCEL'] = '1'
    for member in ('ct-240.gz', 'nodes-000.gz', 'node-19.mesh.gz', 'esophagus.mesh.gz'):
        result = client.head(prefix + member, auth=auth, follow_redirects=False)
        assert result.status_code == 307
        assert result.headers['location'] == '/source-media/anatomy/' + source.ATLAS + '/' + member
    assert client.get(prefix + 'ct-999.gz', auth=auth).status_code == 404
"""
    result = subprocess.run(
        [sys.executable, '-c', script], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_mask_map_matches_independent_original_nifti_planes():
    subprocess.run(
        ['node', 'tools/anatomy_sources/check_pat9_mask_map.mjs'], cwd=ROOT,
        check=True, timeout=90,
    )
