"""Reader API, shared lesson and hosted delivery retain the exact HRA source scope."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

import pytest


ROOT = Path(__file__).resolve().parents[1]
ATLAS_NAME = 'hra-female-pelvis-v1.10'
ATLAS = ROOT / 'web/anatomy' / ATLAS_NAME
MANIFEST_BYTES = (ATLAS / 'manifest.json').read_bytes()
MANIFEST = json.loads(MANIFEST_BYTES)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def reader_client(tmp_path, monkeypatch):
    # Isolate before the server import; even its import-time stores stay in QA.
    monkeypatch.setenv('PRIMER_DB', str(tmp_path / 'reader.db'))
    monkeypatch.setenv('PRIMER_BACKUP_DIR', str(tmp_path / 'backups'))
    for key in ['TURSO_DATABASE_URL', 'TURSO_AUTH_TOKEN', 'VERCEL', 'VERCEL_ENV']:
        monkeypatch.delenv(key, raising=False)
    from fastapi.testclient import TestClient
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    import primer.server as server
    monkeypatch.setattr(server, 'learner', LearnerStore(str(tmp_path / 'reader.db')))
    monkeypatch.setattr(server, 'wiki', WikiService(str(tmp_path / 'reader.db')))
    monkeypatch.setattr(server, 'DB_PATH', str(tmp_path / 'reader.db'))
    monkeypatch.setattr(server, 'BACKUP_DIR', str(tmp_path / 'backups'))
    monkeypatch.setattr(server, '_maintenance_loop', lambda *_args: None)
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV, 'reader')
    monkeypatch.setenv(server.ACCESS_PASSWORD_ENV, 'test-only-secret')
    with TestClient(server.app) as client:
        yield client, server


def test_reporting_api_and_shared_lesson_bind_the_same_uncropped_native_source(reader_client):
    from primer import radiology_catalog as catalog
    from primer.module_media import source_model_bindings
    client, _server = reader_client
    auth = ('reader', 'test-only-secret')
    assert client.get('/api/radiology/modules/ra.mri-endometriosis').status_code == 401
    response = client.get('/api/radiology/modules/ra.mri-endometriosis', auth=auth)
    assert response.status_code == 200
    report = response.json()
    references = report['radiology_reference']['source_anatomy_references']
    sources = [r for r in references if r['atlas'] == ATLAS_NAME]
    assert len(sources) == 1
    source = sources[0]
    assert source['family'] == 'female-pelvis-source'
    assert source['manifest_url'] == '/app/anatomy/' + ATLAS_NAME + '/manifest.json'
    assert source['manifest_sha256'] == sha(MANIFEST_BYTES)
    assert source['initial_layer'] == 'source-surfaces' and source['initial_cropped'] is False
    assert source['source_coordinate_system'] == 'native-gltf-y-up'
    assert not source.get('source_volume') and not source.get('source_image') and not source.get('patient_registration')
    assert 'independent of the published MRI cases and current patient' in source['population_note']
    assert source in source_model_bindings()['rad.5.uterine-mr']
    lesson = client.get('/api/curriculum/node/rad.5.uterine-mr', auth=auth)
    assert lesson.status_code == 200
    models = [m for m in lesson.json()['lesson_media'] if m.get('renderer') == 'radiology-anatomy']
    assert len(models) == 1 and source in models[0]['props']['source_references']
    mapping = catalog._source_anatomy_references()
    assert {i for i, rows in mapping.items() if any(r['atlas'] == ATLAS_NAME for r in rows)} == {'ra.mri-endometriosis'}
    assert not MANIFEST['clinical_approval'] and not MANIFEST['complete_reporting_anatomy_approved']
    assert not MANIFEST['every_structure_approved'] and not MANIFEST['full_module_fidelity_approved']


def test_all_54_reader_meshes_decode_exactly_and_hosted_requests_redirect(reader_client, monkeypatch):
    client, _server = reader_client
    auth = ('reader', 'test-only-secret')
    manifest_url = '/app/anatomy/' + ATLAS_NAME + '/manifest.json'
    assert client.get(manifest_url).status_code == 401
    delivered = client.get(manifest_url, auth=auth)
    assert delivered.status_code == 200 and delivered.content == MANIFEST_BYTES
    assert len(MANIFEST['parts']) == 54 and MANIFEST['total_triangles'] == 293490
    first = next(iter(MANIFEST['parts'].values()))
    assert client.get(first['file']).status_code == 401
    for part in MANIFEST['parts'].values():
        encoded = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
        response = client.get(part['file'], auth=auth)
        assert response.status_code == 200
        assert response.content == gzip.decompress(encoded)
        assert sha(response.content) == part['decoded_sha256']
        assert struct.unpack('<4sII', response.content[:12]) == (b'BP3D', part['vertices'], part['triangles'] * 3)
        assert len(response.content) == 12 + part['vertices'] * 24 + part['triangles'] * 12
    notice_url = '/app/anatomy/' + ATLAS_NAME + '/ATTRIBUTION.md'
    notice = client.get(notice_url, auth=auth)
    assert notice.status_code == 200 and notice.content == (ATLAS / 'ATTRIBUTION.md').read_bytes()
    assert 'CC BY 4.0' in notice.text and 'Visible Human Male' in notice.text
    assert '234 shared exact coordinate triangles' in notice.text
    monkeypatch.setenv('VERCEL', '1')
    assert client.get(first['file'], follow_redirects=False).status_code == 401
    for part in MANIFEST['parts'].values():
        response = client.get(part['file'], auth=auth, follow_redirects=False)
        assert response.status_code == 307
        assert response.headers['location'] == '/source-media' + part['file'].removeprefix('/app')
    response = client.get(first['file'] + '?qa=original', auth=auth, follow_redirects=False)
    assert response.status_code == 307 and response.headers['location'].endswith('?qa=original')
    assert client.get(manifest_url, auth=auth).content == MANIFEST_BYTES
    assert client.get(notice_url, auth=auth).content == notice.content


def test_hosted_missing_local_meshes_require_the_verified_cdn_inventory(tmp_path, monkeypatch):
    from primer.source_mesh_integrity import verified_mesh_contract
    monkeypatch.delenv('VERCEL', raising=False)
    atlas_root = tmp_path / ATLAS_NAME
    atlas_root.mkdir()
    data = ROOT / 'data/radiology'
    for part in MANIFEST['parts'].values():
        with pytest.raises(ValueError, match='missing'):
            verified_mesh_contract(part, atlas_root, data)
    monkeypatch.setenv('VERCEL', '1')
    for part in MANIFEST['parts'].values():
        header, byte_count = verified_mesh_contract(part, atlas_root, data)
        assert struct.unpack('<4sII', header) == (b'BP3D', part['vertices'], part['triangles'] * 3)
        assert byte_count == 12 + part['vertices'] * 24 + part['triangles'] * 12
    part = next(iter(MANIFEST['parts'].values()))
    for changes in [{'sha256': '0' * 64}, {'decoded_sha256': '0' * 64}, {'vertices': part['vertices'] + 1}]:
        with pytest.raises(ValueError, match='differs'):
            verified_mesh_contract(dict(part, **changes), atlas_root, data)


def test_source_assets_remain_reference_only_with_pending_anatomical_coverage():
    evidence = json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())
    records = [r for r in evidence['assets'] if r['id'] in MANIFEST['parts']]
    assert len(records) == 54
    for record in records:
        part = MANIFEST['parts'][record['id']]
        assert record['reference_only'] is True
        assert record['investigation_ids'] == ['ra.mri-endometriosis']
        assert record['structure_ids'] == [] and record['requirement_coverage'] == {}
        assert record['representation'] == 'complete_original_curated_source_surface'
        assert record['anatomical_review']['status'] == 'pending'
        assert record['sha256'] == part['sha256']
        assert record['geometry']['source_positions_sha256'] == part['source_positions_sha256']
        assert record['source']['license']['commercial_use'] is True
        assert record['source']['license']['review_status'] == 'verified'
        for path, digest in record['presentation_dependencies'].items():
            assert sha((ROOT / path).read_bytes()) == digest
        assert 'clinical' in record['limitations'].lower() and '234' in record['limitations']


def test_actual_reader_browser_mounts_the_supported_family_on_both_routes_and_viewports():
    review = json.loads((ROOT / 'docs/hra-female-pelvis-native-review/browser-integration-review.json').read_text())
    frontend = sha((ROOT / 'web/radiology-detailed-anatomy.js').read_bytes())
    assert review['frontend_sha256'] == frontend
    assert review['manifest_sha256'] == sha(MANIFEST_BYTES)
    assert review['all_requested_routes_and_viewports_passed']
    assert {(r['route'], r['viewport']['width']) for r in review['results']} == {
        ('reporting', 1440), ('reporting', 390), ('lesson', 1440), ('lesson', 390)}
    for result in review['results']:
        assert result['frontend_sha256'] == frontend
        assert result['frontend_family_supported'] and result['render_invocation_returned_source_viewer']
        assert result['all_54_runtime_meshes_fetched_decoded_and_gpu_drawn']
        assert result['mesh_count'] == len(result['meshes']) == 54
        assert result['triangle_count'] == 293490
        assert sum(draw['count'] for draw in result['initial']['draw_calls']) == 293490 * 3
        assert result['initial_uncropped'] and result['native_gpu_y_up'] and result['whole_source_extent_framed']
        assert result['selection_isolation_reset_verified'] and result['full_extent_toggle_restore_verified']
        assert result['attribution_and_scope_text_verified']
        assert result['source_labels_do_not_overlap']
        assert result['initial']['source_label_rects']['vertical_overlap_pixels'] == 0
        assert not result['cross_case_registration_or_fit_present']
        assert not result['horizontal_overflow'] and result['page_errors'] == [] and result['failed_requests'] == []
        assert (ROOT / 'docs/hra-female-pelvis-native-review' / result['screenshot']).is_file()
