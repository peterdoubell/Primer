"""Original publications retain exact byte identities and private application routes."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from primer import source_blob_delivery as blob

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('change', ['host', 'path', 'license', 'scope', 'approval', 'missing', 'hash', 'role'])
def test_publication_delivery_rejects_unreviewed_source_changes(change, tmp_path, monkeypatch):
    original = json.loads(blob.REGISTRY.read_text())
    mutated = copy.deepcopy(original)
    src = next(iter(mutated['files']))
    row = mutated['files'][src]
    if change == 'host':
        row['url'] = row['url'].replace(blob.BLOB_HOST, 'unreviewed.example')
    elif change == 'path':
        row['url'] += '?other-source=1'
    elif change == 'license':
        row['license'] = 'CC BY-NC 4.0'
    elif change == 'scope':
        mutated['files']['/app/anatomy/another-case/file.jpg'] = mutated['files'].pop(src)
    elif change == 'approval':
        mutated['clinical_approval'] = True
    elif change == 'missing':
        mutated['files'].pop(src)
    elif change == 'hash':
        row['url'] = row['url'].replace(row['sha256'], '0' * 64)
        row['sha256'] = '0' * 64
    else:
        row['role'] = 'publication_pdf'
    registry = tmp_path / 'delivery.json'
    registry.write_text(json.dumps(mutated))
    monkeypatch.setattr(blob, 'REGISTRY', registry)
    # Exercise structural rejection even when this test treats the mutation as a proposed reviewed packet.
    monkeypatch.setattr(blob, 'REGISTRY_SHA256', hashlib.sha256(registry.read_bytes()).hexdigest())
    blob.delivery.cache_clear()
    try:
        with pytest.raises(ValueError):
            blob.delivery()
    finally:
        blob.delivery.cache_clear()


def test_document_ids_cannot_be_rebound_or_promoted():
    documents = json.loads((ROOT / 'docs/traumatic-haemorrhage-source-review/ninds-2025-source-context-proposal.json').read_text())['documents']
    unrelated_src, unrelated = next(iter(blob.delivery()['files'].items()))
    wrong = copy.deepcopy(documents)
    for row in wrong:
        row.update(src=unrelated_src, sha256=unrelated['sha256'], bytes=unrelated['bytes'], mime_type=unrelated['content_type'])
    with pytest.raises(ValueError, match='differs'):
        blob.validate_context_documents(wrong)
    for flag in ['clinical_approval', 'current_patient_findings', 'patient_registration_verified', 'fine_structure_coverage_granted']:
        wrong = copy.deepcopy(documents)
        wrong[0][flag] = True
        with pytest.raises(ValueError, match='promote'):
            blob.validate_context_documents(wrong)


def test_exact_public_routes_and_browser_policy_are_narrowly_registered():
    data = blob.delivery()
    routes = json.loads((ROOT / 'vercel.json').read_text())['routes']
    new = [row for row in routes if 'traumatic' in row.get('src', '')]
    assert len(new) == 34
    assert {row['dest'] for row in new} == {row['url'] for row in data['files'].values()}
    import re
    for src, item in data['files'].items():
        public = '/source-media/' + src.removeprefix('/app/')
        matches = [row for row in new if re.fullmatch(row['src'], public)]
        assert len(matches) == 1 and matches[0]['dest'] == item['url']
        assert matches[0]['status'] == 307
    assert not any(re.fullmatch(row['src'], '/source-media/reference-media/radiology-open/traumatic-haemorrhage/unknown.png') for row in new)
    assert 'web/reference-media/radiology-open/traumatic-haemorrhage/*' in (ROOT / '.vercelignore').read_text()


def test_actual_authenticated_get_head_and_hosted_redirects_keep_original_bytes(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith('TURSO')
           and k not in {'VERCEL', 'VERCEL_ENV', 'PRIMER_ACCESS_USERNAME', 'PRIMER_ACCESS_PASSWORD'}}
    env.update(PRIMER_DB=str(tmp_path / 'source.db'), PRIMER_BACKUP_DIR=str(tmp_path / 'backups'))
    script = r'''
import hashlib,os
from fastapi import FastAPI
from fastapi.testclient import TestClient
import primer.server as server
from primer.source_blob_delivery import delivery,PREFIX,BLOB_PREFIX
data=delivery();auth=('source-reader','fixture-password')
os.environ[server.ACCESS_USERNAME_ENV]=auth[0];os.environ[server.ACCESS_PASSWORD_ENV]=auth[1]
with TestClient(server.app,follow_redirects=False) as client:
 for src,row in data['files'].items():
  assert client.get(src).status_code==401
  get=client.get(src,auth=auth);head=client.head(src,auth=auth)
  assert get.status_code==head.status_code==200
  assert len(get.content)==row['bytes'] and hashlib.sha256(get.content).hexdigest()==row['sha256']
  assert head.content==b'' and int(head.headers['content-length'])==row['bytes']
 assert client.get(PREFIX+'unknown.png',auth=auth).status_code==404
 assert client.get(PREFIX+'centertbi-2024-fig1.png/',auth=auth).status_code==404
 assert client.get(PREFIX+'nested/centertbi-2024-fig1.png',auth=auth).status_code==404
 assert client.get('/healthz').json()['source_blob_metadata_validated'] is True
 html=client.get('/app/index.html',auth=auth)
 assert BLOB_PREFIX in html.headers['content-security-policy'].split('connect-src')[0]
 assert "connect-src 'self';" in html.headers['content-security-policy']
 os.environ['VERCEL']='1'
 for src in data['files']:assert client.get(src).status_code==401
 # The outer private gate is verified above; exercise just the fixed production delivery handler.
 app=FastAPI();app.add_api_route(PREFIX+'{asset:path}',server.publication_blob_delivery,methods=['GET','HEAD'])
 with TestClient(app,follow_redirects=False) as handler:
  for src,row in data['files'].items():
   for request in [handler.get,handler.head]:
    response=request(src)
    assert response.status_code==307 and response.headers['location']==row['url']
    assert response.headers['cache-control']=='private, no-store'
  assert handler.get(PREFIX+'unknown.png').status_code==404
  assert handler.get(PREFIX+'centertbi-2024-fig1.png/').status_code==404
print('34 exact GET/HEAD originals and hosted identity-pinned redirects verified')
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=env,
                            text=True, capture_output=True, timeout=100)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '34 exact GET/HEAD' in result.stdout
