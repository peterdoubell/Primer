"""Exercise the authenticated frame policy on the native pelvic viewers."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_pelvic_ct_and_surface_pages_allow_same_origin_frames(tmp_path):
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(('TURSO', 'PRIMER_ACCESS_', 'VERCEL', 'BLOB_'))
    }
    env.update(
        PRIMER_DB=str(tmp_path / 'reader.db'),
        PRIMER_CONTENT_DIR=str(tmp_path / 'content'),
        PRIMER_BACKUP_DIR=str(tmp_path / 'backups'),
        PRIMER_ACCESS_USERNAME='synthetic-pelvic-reader',
        PRIMER_ACCESS_PASSWORD='fixture-only',
    )
    script = """
from fastapi.testclient import TestClient
from primer.server import app

auth = ('synthetic-pelvic-reader', 'fixture-only')
with TestClient(app) as client:
    for case in ('recist-pelvic-015', 'recist-pelvic-023'):
        prefix = '/app/anatomy/' + case + '/'
        for path in ('index.html', 'surfaces.html'):
            for method in ('GET', 'HEAD'):
                assert client.request(method, prefix + path).status_code == 401
                response = client.request(method, prefix + path, auth=auth)
                assert response.status_code == 200
                policy = response.headers['content-security-policy']
                assert "frame-ancestors 'self';" in policy
                assert "connect-src 'self';" in policy
        assert client.get(prefix + 'unlisted.html', auth=auth).status_code == 404
    homepage = client.get('/app/', auth=auth)
    assert "frame-ancestors 'none';" in homepage.headers['content-security-policy']
"""
    result = subprocess.run(
        [sys.executable, '-c', script], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
