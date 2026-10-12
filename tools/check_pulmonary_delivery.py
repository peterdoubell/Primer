"""Full-app local and VERCEL-mode ASGI checks, using a synthetic isolated reader.

No external requests, uploads, deployments or production credentials are used.
"""
import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check():
    for key in list(os.environ):
        if key.startswith(('TURSO', 'PRIMER_ACCESS_', 'VERCEL', 'BLOB_')):
            os.environ.pop(key)
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='primer-pulmonary-delivery-') as temporary:
        os.environ.update(PRIMER_DB=str(Path(temporary) / 'reader.db'),
                          PRIMER_BACKUP_DIR=str(Path(temporary) / 'backups'),
                          PRIMER_ACCESS_USERNAME='pulmonary-source-review',
                          PRIMER_ACCESS_PASSWORD='synthetic-source-fixture')
        from fastapi.testclient import TestClient
        import primer.server as server
        from primer import pulmonary_source_delivery as source, pulmonary_native_inspectors as native
        from primer import source_native_inspectors as combined
        files = source.delivery()['files']
        auth = ('pulmonary-source-review', 'synthetic-source-fixture')
        rows = []
        counts = {'local_exact_get': 0, 'local_exact_head': 0, 'auth_rejections': 0,
                  'hosted_fixed_redirects': 0, 'authored_private_checks': 0,
                  'unknown_path_rejections': 0, 'lookup_before_auth_checks': 0,
                  'unconfigured_hosted_rejections': 0}
        with TestClient(server.app, follow_redirects=False) as client:
            for src, row in files.items():
                for verb in ('GET', 'HEAD'):
                    response = client.request(verb, src)
                    assert response.status_code == 401 and response.headers['cache-control'] == 'no-store', (src, response.status_code, dict(response.headers))
                    counts['auth_rejections'] += 1
                get = client.get(src, auth=auth)
                head = client.head(src, auth=auth)
                assert get.status_code == head.status_code == 200, (src, get.status_code, head.status_code)
                assert len(get.content) == row['bytes'] and hashlib.sha256(get.content).hexdigest() == row['sha256']
                assert head.content == b'' and int(head.headers['content-length']) == row['bytes']
                for response in (get, head):
                    assert response.headers['cache-control'] == 'private, no-store'
                    assert response.headers['content-type'].split(';')[0] == row['content_type']
                    assert 'content-encoding' not in response.headers
                    assert 'Authorization' in response.headers['vary'] and 'Cookie' in response.headers['vary']
                rows.append({'src': src, 'bytes': row['bytes'], 'sha256': hashlib.sha256(get.content).hexdigest(),
                             'local_get': 200, 'local_head': 200})
                counts['local_exact_get'] += 1
                counts['local_exact_head'] += 1
            for hosted in (False, True):
                if hosted:
                    os.environ['VERCEL'] = '1'
                for name in sorted(source.AUTHORED_FILES):
                    for query in ('', '?v=cache-poison', '?url=https://unreviewed.example&v=1'):
                        for verb in ('GET', 'HEAD'):
                            src = source.PREFIX + name + query
                            assert client.request(verb, src).status_code == 401
                            counts['auth_rejections'] += 1
                            response = client.request(verb, src, auth=auth)
                            assert response.status_code == 200 and response.headers['cache-control'] == 'private, no-store'
                            expected = server.CSP.replace("connect-src 'self';", "connect-src 'self' " + source.BLOB_PREFIX + ";").replace("frame-ancestors 'none';", "frame-ancestors 'self';") if name == 'reference.html' else server.CSP
                            assert response.headers['content-security-policy'] == expected
                            if verb == 'GET':
                                assert hashlib.sha256(response.content).hexdigest() == native.AUTHORED_SHA256[name]
                            else:
                                assert response.content == b''
                            counts['authored_private_checks'] += 1
                ordinary = client.get('/app/index.html', auth=auth)
                assert ordinary.headers['content-security-policy'] == server.CSP
                assert source.BLOB_PREFIX not in server.CSP and "connect-src 'self';" in server.CSP
                for name in ('unknown.gz', 'original-ct/00000430.dcm', 'original-ct/00000000.dcm',
                             'original-ct/00000001.dcm/extra', 'original-ct/nested/00000001.dcm',
                             'nested/reference.html', 'reference.html/', '%72eference.html',
                             'original-ct%2f00000001.dcm', 'original-ct/%30%30%30%30%30%30%30%31.dcm',
                             'original-ct/%2e%2e/reference.html', '%252e%252e%252freference.html',
                             '%00reference.html', 'original-ct%5c00000001.dcm', 'reference.html%5cunknown'):
                    for verb in ('GET', 'HEAD'):
                        src = source.PREFIX + name
                        assert client.request(verb, src).status_code == 401, src
                        counts['auth_rejections'] += 1
                        response = client.request(verb, src, auth=auth)
                        assert response.status_code == 404, (src, response.status_code)
                        counts['unknown_path_rejections'] += 1
                # Even cold or broken metadata cannot be reached by unauthenticated requests.
                with patch.object(native, 'references', side_effect=AssertionError('Lookup happened before auth')):
                    for name in ('reference.html', 'original-ct/00000001.dcm', 'unknown.gz'):
                        for verb in ('GET', 'HEAD'):
                            assert client.request(verb, source.PREFIX + name).status_code == 401
                            counts['lookup_before_auth_checks'] += 1
            for src, row in files.items():
                for verb in ('GET', 'HEAD'):
                    for host in ('unreviewed.example/healthz', 'unreviewed.example/api/state'):
                        headers = {'Host': host}
                        assert client.request(verb, src, headers=headers).status_code == 401
                        counts['auth_rejections'] += 1
                        response = client.request(verb, src + '?url=https://unreviewed.example/&next=//unreviewed.example',
                                                  headers=headers, auth=auth)
                        assert response.status_code == 307 and response.headers['location'] == row['url']
                        assert response.headers['cache-control'] == 'private, no-store'
                        assert 'Authorization' in response.headers['vary'] and 'Cookie' in response.headers['vary']
                        counts['hosted_fixed_redirects'] += 1
            health = client.get('/healthz')
            assert health.status_code == 200 and health.json()['source_pulmonary_metadata_validated'] is True
            assert all(value is True for key, value in health.json().items() if key.endswith('_metadata_validated'))
            keys = set(combined.references())
            assert keys == {'ra.brain-anatomy', 'ra.acute-stroke', 'ra.ct-pulmonary-nodules'}
            os.environ.pop('PRIMER_ACCESS_USERNAME')
            os.environ.pop('PRIMER_ACCESS_PASSWORD')
            with patch.object(native, 'references', side_effect=AssertionError('Lookup happened without access config')):
                for name in ('reference.html', 'original-ct/00000001.dcm', 'unknown.gz'):
                    for verb in ('GET', 'HEAD'):
                        assert client.request(verb, source.PREFIX + name).status_code == 503
                        counts['unconfigured_hosted_rejections'] += 1
        return {'schema_version': 1, 'scope': 'synthetic full-app ASGI local and VERCEL-mode fixtures',
                'external_requests_or_uploads': False, 'production_browser_or_hosted_blob_verified': False,
                'source_registry_sha256': source.REGISTRY_SHA256, 'inspector_registry_sha256': native.REGISTRY_SHA256,
                'source_review_sha256': source.REVIEW_SHA256, 'manifest_sha256': source.MANIFEST_SHA256,
                'source_payload_count': len(rows), 'source_payload_bytes': sum(row['bytes'] for row in rows),
                'counts': counts, 'files': rows, 'health': health.json(),
                'clinical_approval': False, 'fine_anatomical_approval': False,
                'structure_coverage_granted': False, 'current_patient_registration': False, 'whole_goal_complete': False,
                'all_checks_passed': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    proof = check()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({key: proof[key] for key in ('source_payload_count', 'source_payload_bytes', 'counts', 'all_checks_passed')}))
