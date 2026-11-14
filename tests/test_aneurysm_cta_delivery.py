"""Exercise the release payload, alignment evidence and authenticated asset routing."""
import gzip
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from primer.learner import LearnerStore
from primer.wiki import WikiService

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'anatomy/aneurysm-cta-018'
DIRECTORY = ROOT / 'web' / ATLAS
PREFIX = '/app/' + ATLAS + '/'


def test_anatomy_delivery_preserves_the_source():
    inventory = json.loads((DIRECTORY / 'delivery.json').read_text())['files']
    assert {path.name for path in DIRECTORY.iterdir()} == set(inventory) | {'delivery.json'}
    for name, row in inventory.items():
        raw = (DIRECTORY / name).read_bytes()
        assert len(raw) == row['bytes']
        assert hashlib.sha256(raw).hexdigest() == row['sha256'], name

    volume = json.loads((DIRECTORY / 'volume.json').read_text())
    proof = json.loads((ROOT / 'docs/aneurysm-cta-018/alignment-proof.json').read_text())
    surface, = json.loads((DIRECTORY / 'surfaces.json').read_text())
    assert volume['shape'] == [512, 512, 334]
    expected_section = 1
    all_samples = hashlib.sha256()
    for chunk in volume['chunks']:
        assert chunk['firstSection'] == expected_section
        expected_section += chunk['sections']
        samples = gzip.decompress((DIRECTORY / chunk['file']).read_bytes())
        assert len(samples) == chunk['decodedBytes'] == 2 * 512 * 512 * chunk['sections']
        assert hashlib.sha256(samples).hexdigest() == chunk['sha256']
        all_samples.update(samples)
    assert expected_section == 335
    assert all_samples.hexdigest() == volume['storedSamplesSha256'] == proof['decodedStoredSamplesSha256']
    assert [index for index, row in enumerate(volume['sections'], 1) if row['contour']] == list(range(232, 244))
    assert surface['triangles'] == 1456
    for mesh in (surface, surface['source']):
        decoded = gzip.decompress((DIRECTORY / mesh['file']).read_bytes())
        assert hashlib.sha256(decoded).hexdigest() == mesh['sha256']
        assert len(decoded) == mesh['decodedBytes']
    assert not proof['clinicalApproval']

    config = json.loads((ROOT / 'vercel.json').read_text())
    pattern = f'web/{ATLAS}/*.gz'
    assert {'src': pattern, 'use': '@vercel/static'} in config['builds']
    assert pattern in config['builds'][0]['config']['excludeFiles'].removesuffix('}').split(',')
    assert {path.name for path in ROOT.glob(pattern)} == {
        row['file'] for row in [*volume['chunks'], surface, surface['source']]
    }


def test_hosted_payload_requires_reader_access(tmp_path, monkeypatch):
    import primer.server as server

    directory = tmp_path / 'web' / ATLAS
    directory.mkdir(parents=True)
    manifest = (DIRECTORY / 'delivery.json').read_bytes()
    (directory / 'delivery.json').write_bytes(manifest)
    monkeypatch.setattr(server, 'WEB_DIR', str(tmp_path / 'web'))
    monkeypatch.setattr(server, 'learner', LearnerStore(str(tmp_path / 'reader.db')))
    monkeypatch.setattr(server, 'wiki', WikiService(str(tmp_path / 'reader.db')))
    monkeypatch.setattr(server, 'BACKUP_DIR', str(tmp_path / 'backups'))
    monkeypatch.setattr(server, '_maintenance_loop', lambda *_: None)
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV, 'reader')
    monkeypatch.setenv(server.ACCESS_PASSWORD_ENV, 'fixture-only')
    with TestClient(server.app) as client:
        for name in json.loads(manifest)['files']:
            if not name.endswith('.gz'):
                continue
            assert client.get(PREFIX + name).status_code == 401
            for method in ('GET', 'HEAD'):
                response = client.request(method, PREFIX + name, auth=('reader', 'fixture-only'), follow_redirects=False)
                assert response.status_code == 307, name
                assert response.headers['location'] == '/source-media/' + ATLAS + '/' + name
                assert 'content-encoding' not in response.headers
        assert client.get(PREFIX + 'unlisted.gz', auth=('reader', 'fixture-only')).status_code == 404
