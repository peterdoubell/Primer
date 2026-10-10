"""Scoped reader delivery and shared lesson keep reviewed cervical originals."""
import hashlib
import io
import json
from pathlib import Path

from PIL import Image
import pytest


ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs/cervical-cancer-source-review'
CONTRACT=json.loads((EVIDENCE/'source-figure-contract.json').read_text())['structure_atlas']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('PRIMER_DB',str(tmp_path/'reader.db'))
    monkeypatch.setenv('PRIMER_BACKUP_DIR',str(tmp_path/'backups'))
    for key in ['TURSO_DATABASE_URL','TURSO_AUTH_TOKEN','VERCEL','VERCEL_ENV']:
        monkeypatch.delenv(key,raising=False)
    from fastapi.testclient import TestClient
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    import primer.server as server
    monkeypatch.setattr(server,'learner',LearnerStore(str(tmp_path/'reader.db')))
    monkeypatch.setattr(server,'wiki',WikiService(str(tmp_path/'reader.db')))
    monkeypatch.setattr(server,'DB_PATH',str(tmp_path/'reader.db'))
    monkeypatch.setattr(server,'BACKUP_DIR',str(tmp_path/'backups'))
    monkeypatch.setattr(server,'_maintenance_loop',lambda *_args:None)
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV,'reader')
    monkeypatch.setenv(server.ACCESS_PASSWORD_ENV,'test-only-secret')
    with TestClient(server.app) as reader:
        yield reader


def test_reader_delivers_all_32_current_originals_and_decimal_book_identity(client):
    endpoint='/api/radiology/modules/ra.mri-cervical-cancer';auth=('reader','test-only-secret')
    assert client.get(endpoint).status_code==401
    delivered=client.get(endpoint,auth=auth)
    assert delivered.status_code==200
    ref=delivered.json()['radiology_reference'];rows=ref['structure_atlas']
    assert len(rows)==32 and ref['key_images']==[]
    expected={r['id']:r for r in CONTRACT}
    for row in rows:
        original=expected[row['id']]
        for key in ['src','sha256','width','height','figure_number','source_figure_label','modality','source_caption_full','source_context']:
            assert row[key]==original[key]
        assert client.get(row['src']).status_code==401
        image=client.get(row['src'],auth=auth)
        assert image.status_code==200
        assert sha(image.content)==row['sha256']
        assert image.content==(ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes()
        decoded=Image.open(io.BytesIO(image.content));decoded.load()
        assert decoded.size==(row['width'],row['height'])
        assert not row['source_context']['native_acquisition_arrays_included']
        assert not row['source_context']['source_panels_independently_registered']
    normal=next(r for r in rows if r['id']=='open-cervical-cancer-normal-uterus-2018-fig3-1')
    assert normal['figure_number']=='3.1'
    assert Image.open(io.BytesIO(client.get(normal['src'],auth=auth).content)).info['icc_profile']
    source=ref['source_anatomy_references'][0]
    assert source['atlas']=='hra-female-pelvis-v1.10' and source['family']=='female-pelvis-source'
    assert source['initial_cropped'] is False and source['source_coordinate_system']=='native-gltf-y-up'


def test_shared_lesson_groups_reviewed_sources_and_never_loads_held_ra_thumbnails(client):
    auth=('reader','test-only-secret')
    lesson=client.get('/api/curriculum/node/rad.5.uterine-mr',auth=auth).json()
    gallery=next(m for m in lesson['lesson_media'] if m['kind']=='source-gallery')
    assert gallery['investigation_ids']==['ra.mri-endometriosis','ra.mri-cervical-cancer']
    sources={r['src']:r for r in CONTRACT}
    for image in lesson['radiology_reference']['key_images']:
        assert image['src'] in sources
        assert image['sha256']==sources[image['src']]['sha256']
        assert 'radiologyassistant.nl/assets/' not in image['src']
    models=[m for m in lesson['lesson_media'] if m.get('renderer')=='radiology-anatomy']
    assert len(models)==1 and len(models[0]['props']['source_references'])==1
    report=client.get('/api/radiology/modules/ra.mri-cervical-cancer',auth=auth).json()['radiology_reference']
    assert models[0]['props']['source_references']==report['source_anatomy_references']


def test_scoped_walkthrough_uses_original_ids_and_unfilled_assessment_prompts(client):
    auth=('reader','test-only-secret')
    ref=client.get('/api/radiology/modules/ra.mri-cervical-cancer',auth=auth).json()['radiology_reference']
    walk=ref['walkthrough'];ids={r['id'] for r in CONTRACT}
    assert walk['preset_mode']=='assessment-prompts' and len(walk['steps'])==8
    assert walk['start']['module_illustrations'] is False
    assert set(walk['start']['images']).issubset(ids)
    for step in walk['steps']:
        assert set(step['images']).issubset(ids)
        assert not any(i.startswith('uterine-mr-image-') for i in step['images'])
        for value in step['normal'].values():
            assert '[__]' in value and 'Actual source adequacy' in value and 'Unassessed or uncertain' in value
            assert not any(t in value for t in ['No parametrial invasion','No vaginal','No suspicious','Preserved low-signal','FIGO IIB'])


def test_actual_browser_checked_all_figures_prompts_and_native_reference_on_both_routes():
    review=json.loads((EVIDENCE/'browser-integration-review.json').read_text())
    assert review['all_requested_routes_and_viewports_passed']
    assert review['app_js_sha256']==sha((ROOT/'web/app.js').read_bytes())
    assert review['source_contract_sha256']==sha((EVIDENCE/'source-figure-contract.json').read_bytes())
    assert {(r['route'],r['viewport']['width']) for r in review['results']}=={
        ('reporting',1440),('reporting',390),('lesson',1440),('lesson',390)}
    for result in review['results']:
        assert result['complete_cervical_figure_count']==32
        assert result['all_native_image_response_hashes_match']
        assert result['book_heading_preserves_figure_3_1']
        assert result['source_case_modality_staging_limits_visible']
        assert result['enlarged_originals_and_native_size_control_verified']
        assert result['no_held_remote_ra_images']
        assert result['native_reference_mesh_count']==54 and result['native_reference_uncropped']
        assert result['native_reference_is_independent_and_unregistered']
        assert result['page_errors']==[] and result['failed_requests']==[]
        assert not result['horizontal_overflow']
        if result['route']=='reporting':
            assert result['assessment_step_count']==8 and result['only_source_matched_step_images']
            assert result['assessment_prompts_do_not_assert_normality']
