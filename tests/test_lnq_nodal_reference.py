"""Verify that the LNQ case reaches both reports through the reviewed viewer."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_lnq_reporting_bindings_and_authenticated_delivery(tmp_path):
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(('TURSO', 'PRIMER_ACCESS_', 'VERCEL', 'BLOB_'))
    }
    env.update(
        PRIMER_DB=str(tmp_path / 'reader.db'),
        PRIMER_CONTENT_DIR=str(tmp_path / 'content'),
        PRIMER_BACKUP_DIR=str(tmp_path / 'backups'),
        PRIMER_ACCESS_USERNAME='synthetic-lnq-reader',
        PRIMER_ACCESS_PASSWORD='fixture-only',
    )
    script = """
import os
from fastapi.testclient import TestClient
from primer import lnq_nodal_reference as source
from primer.server import app

auth = ('synthetic-lnq-reader', 'fixture-only')
prefix = '/app/anatomy/' + source.ATLAS + '/'
with TestClient(app) as client:
    assert client.get('/healthz').json()['source_native_inspector_metadata_validated']
    for investigation, expected_rows in source.references().items():
        result = client.get('/api/radiology/modules/' + investigation, auth=auth)
        assert result.status_code == 200
        entries = result.json()['radiology_reference']['source_native_inspectors']
        current = [row for row in entries if row['id'] == source.ATLAS]
        assert current == expected_rows
        assert current[0]['clinical_approval'] is False
        assert current[0]['modality'] == 'CT'
    for page in ('index.html', 'surfaces.html'):
        assert client.get(prefix + page).status_code == 401
        response = client.head(prefix + page, auth=auth)
        assert response.status_code == 200
        assert "frame-ancestors 'self';" in response.headers['content-security-policy']
        assert "connect-src 'self';" in response.headers['content-security-policy']
    assert client.get(prefix + 'unlisted.html', auth=auth).status_code == 404
    assert client.get(prefix + 'labels-int16.gz', auth=auth).status_code == 200
    os.environ['VERCEL'] = '1'
    response = client.head(prefix + 'labels-int16.gz', auth=auth, follow_redirects=False)
    assert response.status_code == 307
    assert response.headers['location'] == '/source-media/anatomy/' + source.ATLAS + '/labels-int16.gz'
"""
    result = subprocess.run(
        [sys.executable, '-c', script], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
