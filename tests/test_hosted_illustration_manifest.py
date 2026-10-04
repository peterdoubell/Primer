"""The CDN inventory must preserve every local illustration and reject unknowns."""
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from primer import curriculum as module
from primer import server as srv

ROOT = Path(__file__).resolve().parents[1]


def test_hosted_inventory_matches_every_original(monkeypatch, tmp_path):
    records = json.loads(Path(module.ILLUSTRATION_MANIFEST).read_text())
    assert set(records) == module.LESSON_ILLUSTRATION_URLS
    for url, record in records.items():
        image = ROOT / 'web' / url.removeprefix('/app/')
        assert hashlib.sha256(image.read_bytes()).hexdigest() == record['sha256']
        assert module._webp_dimensions(str(image)) == (record['width'], record['height'])
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setattr(module, 'ILLUSTRATION_ROOT', str(tmp_path / 'excluded'))
    assert module._discover_lesson_illustrations() == module.LESSON_ILLUSTRATION_DIMENSIONS


@pytest.mark.parametrize('mutation', ['path', 'dimension', 'hash'])
def test_hosted_inventory_rejects_invalid_entries(monkeypatch, tmp_path, mutation):
    url = '/app/illustrations/seedling/example-800.webp'
    record = {'width': 800, 'height': 500, 'sha256': 'a' * 64}
    if mutation == 'path':
        url = '/app/illustrations/../example-800.webp'
    elif mutation == 'dimension':
        record['width'] = True
    else:
        record['sha256'] = 'invalid'
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({url: record}))
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setattr(module, 'ILLUSTRATION_ROOT', str(tmp_path / 'excluded'))
    monkeypatch.setattr(module, 'ILLUSTRATION_MANIFEST', str(manifest))
    with pytest.raises(ValueError, match='Invalid hosted'):
        module._discover_lesson_illustrations()


def test_illustration_delivery_preserves_bytes_query_and_access_gate(monkeypatch):
    url = sorted(module.LESSON_ILLUSTRATION_URLS)[0]
    monkeypatch.setenv(srv.ACCESS_USERNAME_ENV, 'reader')
    monkeypatch.setenv(srv.ACCESS_PASSWORD_ENV, 'secret')
    with TestClient(srv.app, follow_redirects=False) as client:
        monkeypatch.delenv('VERCEL', raising=False)
        assert client.get(url).status_code == 401
        local = client.get(url, auth=('reader', 'secret'))
        assert local.status_code == 200
        assert local.content == (ROOT / 'web' / url.removeprefix('/app/')).read_bytes()
        monkeypatch.setenv('VERCEL', '1')
        assert client.get(url).status_code == 401
        for method in ('get', 'head'):
            response = getattr(client, method)(url + '?v=original&tag=a&tag=b', auth=('reader', 'secret'))
            assert response.status_code == 307
            assert response.headers['location'] == url.replace('/app/', '/source-media/') + '?v=original&tag=a&tag=b'
        assert client.get('/app/illustrations/seedling/unknown-800.webp', auth=('reader', 'secret')).status_code == 404
    config = json.loads((ROOT / 'vercel.json').read_text())
    assert 'web/illustrations/**/*.webp' in config['builds'][0]['config']['excludeFiles']
    assert {'src': 'web/illustrations/**/*.webp', 'use': '@vercel/static'} in config['builds']


def test_hosted_radiology_illustrations_require_registered_url(monkeypatch, tmp_path):
    from primer import radiology
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setattr(radiology, 'DATA', tmp_path / 'data' / 'radiology')
    radiology.validate_image_source(sorted(module.LESSON_ILLUSTRATION_URLS)[0])
    with pytest.raises(ValueError, match='Unknown hosted'):
        radiology.validate_image_source('/app/illustrations/seedling/unknown-800.webp')
