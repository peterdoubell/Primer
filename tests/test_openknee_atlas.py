"""Transport, coordinate and provenance contracts for the optional left knee."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'web/anatomy/openknee-oks003'


@pytest.fixture(scope='module')
def manifest():
    return json.loads((DIRECTORY / 'manifest.json').read_text())


def test_native_left_knee_geometry_transports_match_reviewed_source_bounds(manifest):
    assert len(manifest['parts']) == 16
    assert sum(part['triangles'] for part in manifest['parts'].values()) == 307024
    for part in manifest['parts'].values():
        encoded = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(encoded).hexdigest() == part['sha256']
        raw = gzip.decompress(encoded)
        assert hashlib.sha256(raw).hexdigest() == part['decoded_sha256']
        magic, count, indices = struct.unpack_from('<III', raw)
        assert magic == 0x44335042 and count == indices == part['triangles'] * 3
        assert len(raw) == 12 + count * 24 + indices * 4
        low, high = [math.inf] * 3, [-math.inf] * 3
        for point in struct.iter_unpack('<fff', raw[12:12 + count * 12]):
            assert all(math.isfinite(value) for value in point)
            for axis, value in enumerate(point):
                low[axis] = min(low[axis], value)
                high[axis] = max(high[axis], value)
        assert [low, high] == part['bounds']
        assert part['source_triangles'] == part['triangles']
        assert part['omitted_source_facet_indices'] == []
    assert manifest['coordinate_system']['basis'] == 'RAS'
    assert manifest['coordinate_system']['units'] == 'millimeters'
    assert manifest['regions']['knee']['side'] == 'left'
    # In the original RAS frame of this left knee, the fibula is lateral (-X)
    # and the patella anterior (+Y), independently of display camera controls.
    assert manifest['parts']['oks003-fbb']['bounds'][1][0] < 0
    assert manifest['parts']['oks003-ptb']['bounds'][0][1] > 0


def test_source_correspondence_keeps_unresolved_parts_and_clinical_limits(manifest):
    validation = manifest['registration_validation']
    path = ROOT / 'web' / validation['evidence_file'].removeprefix('/app/')
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == validation['evidence_sha256']
    evidence = json.loads(raw)
    assert len(evidence['structures']) == 14
    assert sum(len(part['planes']) for part in evidence['structures']) == 84
    assert set(validation['unresolved_mask_source_ids']) == {'TBC-L', 'TBC-M'}
    assert evidence['no_fitted_transform'] is True
    for part in evidence['structures']:
        actual = manifest['parts']['oks003-' + part['id'].lower()]
        assert part['mesh_sha256'] == actual['source_sha256']
        assert part['mask']['sha256'] == actual['source_segmentation']['sha256']
    assert manifest['clinical_image_pair']['available'] is False
    assert validation['clinical_alignment_approval'] is False
    assert not list(DIRECTORY.glob('*.nii')) and not list(DIRECTORY.glob('*.raw'))
    assert '/tmp/' not in raw.decode() and '/Users/' not in raw.decode()
    assert manifest['license'] == 'CC BY-SA 3.0 Unported'
    source_license = manifest['source_license']
    license_bytes = (ROOT / 'web' / source_license['file'].removeprefix('/app/')).read_bytes()
    assert hashlib.sha256(license_bytes).hexdigest() == source_license['sha256']
    assert 'same' in (DIRECTORY / 'ATTRIBUTION.md').read_text().lower()


def test_openknee_http_delivery_decodes_original_geometry(manifest, tmp_path, monkeypatch):
    monkeypatch.setenv('PRIMER_DB', str(tmp_path / 'reader.db'))
    monkeypatch.setenv('PRIMER_BACKUP_DIR', str(tmp_path / 'backups'))
    from fastapi.testclient import TestClient
    from primer.server import app
    part = manifest['parts']['oks003-acl']
    with TestClient(app) as client:
        response = client.get(part['file'], headers={'Accept-Encoding': 'gzip'})
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/octet-stream'
    assert response.headers['content-encoding'] == 'gzip'
    assert hashlib.sha256(response.content).hexdigest() == part['decoded_sha256']
