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
    from tools.anatomy_sources.pulmonary_ui_compatibility import restore_previous_app
    # The prior receipt still binds d77 exactly; undo only the three recorded pulmonary functions.
    assert current['app_js_sha256']==sha(restore_previous_app().encode())=='d77de3b299fc8af358e6c5fd2c785b22f3a8f19aa89f27a713d40be7c22b11a0'
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



def test_pulmonary_source_only_amendment_preserves_current_legacy_browser_evidence():
    from tools.anatomy_sources import pulmonary_ui_compatibility as bridge
    raw=(EVIDENCE/'browser-compatibility-amendment-pulmonary-source-only-20261011.json').read_bytes()
    assert sha(raw)=='cf85b38d7ef86b046eedccca91b1cab8b59b98ffb27e23c1fe3c98ac38fae78e'
    amendment=json.loads(raw)
    assert amendment['schema_version']==1
    from tools.thoracic_motion_ui_compatibility import restore_previous_motion_ui
    from tools.thoracic_data_compatibility import restore_raw
    assert amendment['app_js_sha256']==bridge.AFTER==sha(restore_previous_motion_ui((ROOT/'web/app.js').read_text()).encode())
    assert amendment['previous_app_js_sha256']==bridge.BEFORE==sha(bridge.restore_previous_app().encode())
    assert amendment['native_presentation_change_scope']=='pulmonary_source_only_mounting'
    assert amendment['historical_approval_scope_unchanged'] is True
    for field in ['clinical_approval','fine_anatomical_approval','structure_coverage_granted',
                  'current_patient_registration','every_structure_approved','fine_3D_tissue_layers_approved',
                  'patient_registration_verified','whole_goal_complete','supersedes_historical_review',
                  'supersedes_previous_compatibility_amendment','supersedes_any_historical_receipt',
                  'historical_capture_reconstruction_or_replacement','production_or_deployment_verification',
                  'native_decoder_mesh_CT_renderer_code_touched',
                  'server_restart_or_shutdown_performed_by_amendment_agent']:
        assert amendment[field] is False
    for filename,digest in amendment['preserved_historical_receipts_sha256'].items():
        assert sha((EVIDENCE/filename).read_bytes())==digest
    assert len(amendment['preserved_historical_receipts_sha256'])==4
    previous=json.loads((EVIDENCE/'browser-compatibility-amendment-stroke-source-case-20261011.json').read_bytes())
    assert amendment['previous_compatibility_amendment_sha256']==sha((EVIDENCE/'browser-compatibility-amendment-stroke-source-case-20261011.json').read_bytes())
    assert amendment['unchanged_native_manifest_sha256']==previous['unchanged_native_manifest_sha256']==sha((ROOT/'web/anatomy/hra-female-pelvis-v1.10/manifest.json').read_bytes())
    inverse=amendment['exact_app_inverse']
    assert inverse['path']==bridge.DELTA and inverse['sha256']==bridge.DELTA_SHA
    assert sha(restore_raw(inverse['helper_path'], (ROOT/inverse['helper_path']).read_bytes()))==inverse['helper_sha256']
    assert inverse['changed_functions']==['sourceNativeInspector','renderRadiologyDesk','renderReportWalkthrough']
    assert inverse['app_bytes_outside_changed_functions_identical'] is True
    assert inverse['reconstructed_previous_app_sha256']==bridge.BEFORE
    delta=json.loads((ROOT/bridge.DELTA).read_bytes())
    assert amendment['guarded_paths_sha256']==delta['guarded_paths_sha256']
    assert amendment['native_reader_smoke']==delta['native_reader_smoke']
    assert sha((ROOT/amendment['native_reader_smoke']['path']).read_bytes())==amendment['native_reader_smoke']['sha256']
    for path,digest in amendment['guarded_paths_sha256'].items():
        assert sha((ROOT/path).read_bytes())==digest
    browser_record=amendment['browser_review']
    assert browser_record['path']=='docs/pulmonary-nodule-integration-review-20261011/compatibility-browser/cervical/review.json'
    browser_raw=(ROOT/browser_record['path']).read_bytes()
    assert sha(browser_raw)==browser_record['sha256']
    browser=json.loads(browser_raw)
    assert browser['all_requested_routes_and_viewports_passed'] is True and browser['owned_isolated_qa_server'] is True
    assert browser['app_js_sha256']==bridge.AFTER
    assert browser['source_contract_sha256']==amendment['source_contract_sha256']==sha((EVIDENCE/'source-figure-contract.json').read_bytes())
    assert browser['detailed_anatomy_js_sha256']==amendment['detailed_anatomy_js_sha256']==sha((ROOT/'web/radiology-detailed-anatomy.js').read_bytes())
    assert {(row['route'],row['viewport']['width']) for row in browser['results']}=={('reporting',1440),('reporting',390),('lesson',1440),('lesson',390)}
    original_rows=json.loads((EVIDENCE/'source-figure-contract.json').read_bytes())['structure_atlas']
    originals={row['id']:row for row in original_rows}
    manifest=json.loads((ROOT/'web/anatomy/hra-female-pelvis-v1.10/manifest.json').read_bytes())
    parts={row['file']:row for row in manifest['parts'].values()}
    for result in browser['results']:
        assert result['served_app_js_sha256']==bridge.AFTER
        assert result['served_detailed_anatomy_js_sha256']==amendment['detailed_anatomy_js_sha256']
        assert result['complete_cervical_figure_count']==32
        assert result['all_native_image_response_hashes_match'] is True
        assert {row['id'] for row in result['image_responses']}==set(originals)
        for response in result['image_responses']:
            original=originals[response['id']]
            body=(ROOT/'web'/original['src'].removeprefix('/app/')).read_bytes()
            assert response['status']==200 and response['src']==original['src']
            assert response['sha256']==original['sha256']==sha(body) and response['bytes']==len(body)
        assert all(row['complete'] and row['source_caption_full_matches'] and row['case_modality_limits_visible'] and row['display_filter']=='none' for row in result['figure_checks'])
        assert result['source_case_modality_staging_limits_visible'] is True
        assert result['enlarged_originals_and_native_size_control_verified'] is True and result['no_held_remote_ra_images'] is True
        assert all(row['native_size_control'] and row['original'] for row in result['enlarged'])
        assert result['native_reference_viewer_count']==1 and result['native_reference_mesh_count']==54
        assert result['all54_source_objects_GPU_drawn'] is True and result['native_reference_uncropped'] is True
        assert result['native_reference_is_independent_and_unregistered'] is True
        assert len(result['mesh_responses'])==54 and {row['path'] for row in result['mesh_responses']}==set(parts)
        for response in result['mesh_responses']:
            part=parts[response['path']]
            assert response['status']==200 and response['sha256']==part['decoded_sha256']
            assert response['vertices']==part['vertices'] and response['triangles']==part['triangles']
        native=result['native_reference']
        assert native['native_y_up'] is True and native['cropped']=='false' and len(native['draw_calls'])==54
        assert sum(row['count'] for row in native['draw_calls'])==293490*3
        assert result['source_labels_nonoverlap'] is True and native['labelRects']['vertical_overlap_pixels']==0
        assert result['page_errors']==[] and result['failed_requests']==[] and result['horizontal_overflow'] is False
        if result['route']=='reporting':
            assert result['assessment_step_count']==8 and result['only_source_matched_step_images'] is True
            assert result['assessment_prompts_do_not_assert_normality'] is True
            assert result['assessment']['all_prompts_unfilled'] is True and result['assessment']['assembled_report_has_all_sections'] is True
    assert amendment['capture_count']==16==sum(len(row['screenshots']) for row in browser['results'])
    assert amendment['capture_file_hashes_verified'] is True
    expected_captures=[{'path':str(Path(browser_record['path']).parent/shot['file']),'sha256':shot['sha256']} for row in browser['results'] for shot in row['screenshots']]
    assert amendment['screenshots']==expected_captures
    for capture in amendment['screenshots']:
        assert sha((ROOT/capture['path']).read_bytes())==capture['sha256']
    for field in ['clinical_approval','every_structure_approved','fine_3D_tissue_layers_approved','patient_registration_verified','production_or_deployment_verification']:
        assert browser[field] is False



@pytest.mark.parametrize('change',['extra_app_bytes','unscoped_case','extra_native_function'])
def test_pulmonary_inverse_cannot_accept_any_unreviewed_app_change(change):
    from tools.anatomy_sources import pulmonary_ui_compatibility as bridge
    app=(ROOT/'web/app.js').read_text()
    if change=='extra_app_bytes':app+='\n// Unreviewed bytes outside the recorded functions.\n'
    elif change=='unscoped_case':app=app.replace('lidc-idri-0525','another-source-case',1)
    else:app+='\nfunction unreviewedNativeRenderer() {}\n'
    with pytest.raises(ValueError,match='Unreviewed'):
        bridge.restore_previous_app(app)


@pytest.mark.parametrize('field,value',[
    ('native_presentation_change_scope','arbitrary_renderer'),
    ('native_decoder_mesh_CT_renderer_code_touched',True),
    ('native_presentation_code_touched',False),
    ('clinical_approval',True),('fine_anatomical_approval',True),
    ('reopens_or_extends_any_review',True),
])
def test_pulmonary_refresh_cannot_rebase_or_extend_the_historical_scope(field,value):
    import copy
    from tools.anatomy_sources import pulmonary_ui_compatibility as bridge,ui_refresh
    step=copy.deepcopy(next(row for row in ui_refresh.load()['refreshes'] if row['id']==bridge.REFRESH_ID))
    step[field]=value
    with pytest.raises(ValueError,match='scope'):
        bridge.validate_refresh(step)
