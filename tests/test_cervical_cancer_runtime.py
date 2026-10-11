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
    assert 'source_context_documents' not in ref
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
    assert 'source_context_documents' not in lesson['radiology_reference']
    gallery=next(m for m in lesson['lesson_media'] if m['kind']=='source-gallery')
    assert gallery['investigation_ids']==['ra.mri-endometriosis','ra.mri-cervical-cancer','ra.mri-endometrial-cancer']
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
    # Preserve both prior reviews; bridge only this exact app revision.
    historical_raw=(EVIDENCE/'browser-integration-review.json').read_bytes()
    amendment_raw=(EVIDENCE/'browser-compatibility-amendment-20261011.json').read_bytes()
    previous_raw=(EVIDENCE/'browser-compatibility-amendment-algebra-trauma-20261011.json').read_bytes()
    current_raw=(EVIDENCE/'browser-compatibility-amendment-stroke-source-case-20261011.json').read_bytes()
    assert sha(previous_raw)=='e7c8b28d6b7bd20383456ebdefe871bf1392e1d369bd494bbe2181c716b2391c'
    assert sha(current_raw)=='cf1ec022686dec946225097f525effe362823515168fda4ad704a5caa91ff555'
    assert sha(historical_raw)=='d17017bb0a017711f349fe9d068450fa1969a0c6a07267195047b04d6f477073'
    assert sha(amendment_raw)=='521a75e89c385a389a787298f3b84844e2ff2a07f156ccd37b228a47a8ee12ae'
    historical=json.loads(historical_raw);amendment=json.loads(amendment_raw);previous=json.loads(previous_raw);current=json.loads(current_raw)
    assert amendment['historical_review_sha256']==sha(historical_raw)
    assert amendment['historical_app_js_sha256']==historical['app_js_sha256']=='4c88dab41f6e1e3d1b1b3c15721dc9d45eade4441fc6725df52a871e2464e563'
    assert amendment['app_js_sha256']=='be5ea9dcc4f1e44049a007771a6bb265e0d73c448a0df70c6e190084a42b468f'
    assert previous['app_js_sha256']=='a8dc2985ad28ed9a9b07bd17f87857b3bc389feb7d316049f66ff8f3cf22d29d'
    assert current['app_js_sha256']==sha((ROOT/'web/app.js').read_bytes())=='d77de3b299fc8af358e6c5fd2c785b22f3a8f19aa89f27a713d40be7c22b11a0'
    assert current['historical_review_sha256']==sha(historical_raw)
    assert current['historical_app_js_sha256']==historical['app_js_sha256']
    assert previous['previous_compatibility_amendment_sha256']==sha(amendment_raw)
    assert previous['previous_compatibility_app_js_sha256']==amendment['app_js_sha256']
    assert current['previous_compatibility_amendment_sha256']==sha(previous_raw)
    assert current['previous_compatibility_app_js_sha256']==previous['app_js_sha256']
    assert current['preserved_earlier_compatibility_amendment_sha256']==sha(amendment_raw)
    assert current['native_citation_wrapper_code_touched'] is True
    assert current['native_decoder_mesh_CT_renderer_code_touched'] is False
    assert current['new_explicit_metadata_field']=='publication_url'
    assert current['old_atlas_citation_fallback_unchanged']
    assert current['app_bytes_outside_changed_function_identical']
    assert current['historical_approval_scope_unchanged'] and not current['supersedes_historical_review']
    assert not current['supersedes_previous_compatibility_amendment']
    assert current['authenticated_reader'] and current['disposable_database_and_backups']
    assert not current['persistent_browser_profile_used'] and not current['production_or_deployment_verification']
    assert current['browser_and_contexts_closed'] and current['server_shutdown_owned_by_parent']
    assert not current['historical_capture_files_available_in_checkout']
    assert current['historical_missing_capture_count']==len(current['historical_missing_capture_files'])==16
    assert not current['historical_capture_reconstruction_or_replacement']
    assert all(not (EVIDENCE/file).exists() for file in current['historical_missing_capture_files'])
    assert current['unchanged_native_manifest_sha256']==sha((ROOT/'web/anatomy/hra-female-pelvis-v1.10/manifest.json').read_bytes())
    assert current['reviewed_visual_capture_count']==sum(len(r['screenshots']) for r in current['results'])
    for result in current['results']:
        assert result['served_app_js_sha256']==current['app_js_sha256']
        assert result['served_detailed_anatomy_js_sha256']==current['detailed_anatomy_js_sha256']
        assert result['source_context_documents_absent'] and result['api_source_context_documents_absent']
        assert result['source_context_document_checks']
        assert all(check['document_count']==0 for check in result['source_context_document_checks'])
        assert all(s['file'].startswith('stroke-source-case-20261011-') for s in result['screenshots'])
    assert amendment['historical_approval_scope_unchanged'] and not amendment['supersedes_historical_review']
    assert amendment['authenticated_reader'] and amendment['disposable_database_and_backups']
    assert not amendment['persistent_browser_profile_used'] and not amendment['production_or_deployment_verification']
    assert amendment['unchanged_native_manifest_sha256']==sha((ROOT/'web/anatomy/hra-female-pelvis-v1.10/manifest.json').read_bytes())
    assert previous['historical_review_sha256']==sha(historical_raw)
    assert previous['historical_app_js_sha256']==historical['app_js_sha256']
    assert previous['historical_approval_scope_unchanged'] and not previous['supersedes_historical_review']
    assert not previous['supersedes_previous_compatibility_amendment']
    assert previous['authenticated_reader'] and previous['disposable_database_and_backups']
    assert previous['browser_and_contexts_closed'] and previous['server_shutdown_owned_by_parent']
    assert previous['reviewed_visual_capture_count']==sum(len(r['screenshots']) for r in previous['results'])
    for result in previous['results']:
        assert result['served_app_js_sha256']==previous['app_js_sha256']
        assert result['source_context_documents_absent'] and result['api_source_context_documents_absent']
        assert all(s['file'].startswith('algebra-trauma-20261011-') for s in result['screenshots'])
    for review in [historical,amendment,previous,current]:
        assert review['all_requested_routes_and_viewports_passed']
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
            assert result['native_reference_viewer_count']==1 and result['native_reference_mesh_count']==54 and result['native_reference_uncropped']
            assert result['all54_source_objects_GPU_drawn'] and result['mesh_hashes_match_manifest']
            assert result['source_labels_nonoverlap']
            manifest=json.loads((ROOT/'web/anatomy/hra-female-pelvis-v1.10/manifest.json').read_text())
            parts={p['file']:p for p in manifest['parts'].values()}
            assert len(result['mesh_responses'])==54 and {r['path'] for r in result['mesh_responses']}==set(parts)
            for response in result['mesh_responses']:
                assert response['status']==200 and response['sha256']==parts[response['path']]['decoded_sha256']
                assert response['vertices']==parts[response['path']]['vertices'] and response['triangles']==parts[response['path']]['triangles']
            native=result['native_reference']
            assert native['native_y_up'] and native['cropped']=='false' and len(native['draw_calls'])==54
            assert sum(p['count'] for p in native['draw_calls'])==293490*3
            assert native['labelRects']['vertical_overlap_pixels']==0
            assert len(result['screenshots'])==4
            # Original recorded captures are unavailable; preserve the observation without inventing evidence.
            if review is not historical:
                for screenshot in result['screenshots']:assert sha((EVIDENCE/screenshot['file']).read_bytes())==screenshot['sha256']
            assert result['native_reference_is_independent_and_unregistered']
            assert result['page_errors']==[] and result['failed_requests']==[]
            assert not result['horizontal_overflow']
            if result['route']=='reporting':
                assert result['assessment_step_count']==8 and result['only_source_matched_step_images']
                assert result['assessment_prompts_do_not_assert_normality']

        assert not review['clinical_approval'] and not review['every_structure_approved'] and not review['fine_3D_tissue_layers_approved'] and not review['patient_registration_verified']
