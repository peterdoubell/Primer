"""Scoped proof of source fidelity in the actual signed reader and hosted branch."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/acute-stroke-reader-review-20261011'


def read(name):
    return json.loads((DOC / name).read_text())


def test_actual_reader_route_matrix_preserves_all_source_figures_and_case_roles():
    proof = read('integrated-reader-proof.json')
    assert proof['passed'] is True and proof['browserHandlesClosed'] is True
    assert {(r['mode'], r['route'], r['width']) for r in proof['rows']} == {
        ('local', route, width) for route in ['reporting', 'lesson'] for width in [1440, 390]
    } | {('hosted', 'reporting', width) for width in [1440, 390]}
    for r in proof['rows']:
        assert r['passed'] and r['unrelatedSwitchClean']
        assert r['errors'] == [] and r['failedRequests'] == []
        assert len(r['figures']) == 13
        modalities = [m for f in r['figures'] for m in f['panelTypes'].values()]
        assert modalities.count('CT') == 83
        assert modalities.count('MRI') == 1
        assert modalities.count('Haemodynamic tracing') == 1
        for f in r['figures']:
            assert f['filter'] == 'none' and f['completeNativePopup']['zoomed']
            assert f['sourceContext']['current_patient_findings'] is False
            assert f['sourceContext']['patient_3D_supplied'] is False
            assert f['sourceContext']['source_calibration_or_HU_recoverable'] is False
        f6 = next(f for f in r['figures'] if f['id'].endswith('fig6'))
        assert f6['panelTypes']['F'] == 'MRI'
        assert 'next day' in f6['sourceContext']['CT_MRI_temporal_relation']
        assert 'not registered' in f6['sourceContext']['CT_MRI_temporal_relation']
        if r['route'] == 'reporting':
            assert len(r['prompts']) == 5
            for step in r['prompts']:
                assert step['noPartHighlight']
                assert all('[ ]' in f['value'] for f in step['fields'])


def test_full_native_arrays_separate_grids_models_and_live_positive_payloads_are_verified():
    proof = read('integrated-reader-proof.json')
    manifest = json.loads((ROOT / 'web/anatomy/soop-stroke-sub342/manifest.json').read_text())
    registry = json.loads((ROOT / 'data/radiology/acute-stroke-source-delivery.json').read_text())
    for r in proof['rows']:
        native = r['native']
        assert {s['role'] for s in native['sequences']} == set(manifest['arrays'])
        for s in native['sequences']:
            assert not ('t1' in s['buffers'] and 'flair' in s['buffers'])
            for role, b in s['buffers'].items():
                assert b['sha256'] == manifest['arrays'][role]['decoded_sha256']
                assert b['bytes'] == manifest['arrays'][role]['decoded_bytes']
            if s['role'] in ['t1', 'flair']:
                assert s['overlayDisabled'] is True and 'Separate' in s['values']
            if s['role'] in ['trace', 'adc']:
                assert 'original frame0 of1' in s['position']
        assert len(native['cameras']) == 9
        for draw in native['cameras']:
            assert draw['triangles'] == manifest['meshes'][draw['mask']]['triangles']
            assert draw['gpuError'] == 0
        assert "connect-src 'self' https://ja2lsnp9uca4bivw.public.blob.vercel-storage.com/anatomy/soop-stroke-sub342/;" in native['CSP']
        assert "connect-src 'self';" in r['CSP']
        if r['route'] == 'reporting':
            assert len(native['payloads']) == 21
            assert sum(p['bytes'] for p in native['payloads']) == 105836672
            for p in native['payloads']:
                assert p['sha256'] == registry['files'][p['src']]['sha256']
                if r['mode'] == 'hosted':
                    assert p['finalURL'] == registry['files'][p['src']]['url']
            assert len(native['negativeLoads']) == 1
            bad = native['negativeLoads'][0]
            assert bad['recovered'] and bad['intentionallyCorruptedNegativeFixtureOnly']
            assert bad['failure']['ready'] == 'false'
            assert bad['failure']['GPUUniform']
            assert bad['failure']['allDisabledExceptRetry']
            assert bad['failure']['planes'] == ['false'] * 3


def test_independent_source_pixel_oracle_covers_each_integrated_native_plane():
    pixels = read('native-pixel-oracle.json')
    assert pixels['frames'] == 126
    assert len(pixels['checks']) == 126
    assert {(r['mode'], r['route'], r['width'], r['role'], r['axis']) for r in pixels['checks']} == {
        (mode, route, width, role, axis)
        for mode, route, width in [
            ('local', 'reporting', 1440), ('local', 'reporting', 390),
            ('local', 'lesson', 1440), ('local', 'lesson', 390),
            ('hosted', 'reporting', 1440), ('hosted', 'reporting', 390)
        ]
        for role in ['trace', 'adc', 't1', 'flair', 'acute', 'chronic', 'combined']
        for axis in [0, 1, 2]
    }
    assert pixels['integrated_reader_proof_SHA256'] == hashlib.sha256((DOC / 'integrated-reader-proof.json').read_bytes()).hexdigest()
    assert pixels['production_UI_verified'] is False
    assert pixels['clinical_approval'] is False
    assert pixels['fine_anatomical_approval'] is False


def test_existing_population_brain_reader_and_original_payloads_remain_isolated():
    proof = read('brain-bounded-proof.json')
    assert proof['passed'] is True and proof['browserHandlesClosed'] is True
    assert {r['width'] for r in proof['rows']} == {1440, 390}
    for r in proof['rows']:
        assert r['lesson']['oldTemplateAndProbabilityLabelsPreserved']
        assert r['lesson']['noStrokeAssetsAfterSwitch']
        assert r['massp']['meshes'] == 6
        assert r['bodyparts_inspector_absent'] and r['guide_inspector_absent']
        assert len(r['popup']['planes']) == 3
    assert len(proof['existingBrainPayloads']) == 14
    assert sum(r['bytes'] for r in proof['existingBrainPayloads']) == 17434638
    assert proof['retained_original_brain_proofs_not_rebaselined'] is True


def test_frozen_reader_sources_and_unapproved_clinical_scope_are_explicit():
    proof = read('integrated-reader-proof.json')
    for flag in ['productionUIVerified', 'clinicalApproval', 'fineAnatomicalApproval',
                 'structureCoverageGranted', 'wholeGoalComplete']:
        assert proof[flag] is False
    for path, pin in proof['sourceHashes'].items():
        from tools.qft_runtime_compatibility import historical_runtime_bytes
        assert hashlib.sha256(historical_runtime_bytes(path, (ROOT / path).read_bytes())).hexdigest() == pin
    assert (DOC / 'caption-missing-before-repair.json').exists()
    assert read('caption-missing-before-repair.json')['displayedCompleteCaptionDetails'] == 0
    assert read('caption-missing-before-repair.json')['figures'] == 13


def test_final_cache_supplement_preserves_historical_reader_and_exact_private_boundaries():
    reader = read('integrated-reader-proof.json')
    final = read('final-cache-CSP-API-supplement.json')
    assert reader['historical_served_backend_SHA256'] == '607e717a8be8adf16b5fe4c9471770b6d07370627a097cffe58db7796c5acfe4'
    assert reader['historicalSourceHashes']['primer/server.py'] == reader['historical_served_backend_SHA256']
    from tools.qft_runtime_compatibility import historical_runtime_bytes
    assert final['server_SHA256'] == hashlib.sha256(historical_runtime_bytes('primer/server.py', (ROOT / 'primer/server.py').read_bytes())).hexdigest()
    assert final['passed'] and final['API_exactly_matches_completed_reader']
    assert len(final['checks']) == 24 and len(final['hosted_redirects']) == 96
    for row in final['checks']:
        assert row['status'] == (200 if row['signed'] else 401)
        if row['signed']:
            assert row['cache_control'] == 'private, no-store'
    for row in final['hosted_redirects']:
        assert row['status'] == 307 and row['cache_control'] == 'private, no-store'
    for flag in ['production_UI_verified', 'clinical_approval', 'fine_anatomical_approval', 'structure_coverage_granted']:
        assert final[flag] is False
    assert reader['final_backend_cache_supplement']['full_numerical_or_old_GUI_evidence_rebaselined'] is False
