"""Renal-trauma teaching artwork preserves source samples, case/phase roles and grade limits."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/renal-trauma-published-source-review'


def source_rows():
    return {r['figure_number']: r for r in detail(Curriculum(), resolve('ra.ct-abdominal-trauma'))['radiology_reference']['structure_atlas']}


def test_eleven_original_figures_keep_gray_jpegs_and_two_native_rgb_icc_pngs():
    proof = json.loads((REVIEW / 'original-source-review.json').read_text())
    package = json.loads((REVIEW / 'packaged-source-images.json').read_text())
    assert len(proof['figures']) == len(package['figures']) == 11
    article = proof['articles'][0]
    assert article['license'] == 'CC BY 4.0' and article['publisher_xml_pdf_md5_verified']
    assert all(not r['runtime_promoted'] for r in proof['rights_holds'])
    for row in package['figures']:
        original = next(r for r in proof['figures'] if r['figure_number'] == row['figure_number'])
        path = ROOT / row['local_path']
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256'] == original['sha256']
        with Image.open(path) as image:
            assert image.size == (original['width'], original['height'])
            assert hashlib.sha256(image.tobytes()).hexdigest() == original['decoded_pixel_sha256']
            if row['figure_number'] in {6, 10}:
                profile = image.info['icc_profile']
                assert image.mode == 'RGB' and len(profile) == original['source_icc_profile_bytes'] == 3144
                assert hashlib.sha256(profile).hexdigest() == original['source_icc_profile_sha256']
                assert original['acquisition'] == 'lossless_png_original_pdf_dct_rgb_samples_and_icc_preserved'
            else:
                assert image.mode == 'L' and original['acquisition'] == 'original_pdf_dct_stream_byte_identical'
                assert hashlib.sha256(raw).hexdigest() == original['original_dct_stream_sha256']
        assert original['publisher_media_md5_verified'] and not original['source_pixels_changed']


def test_selected_ct_panels_do_not_borrow_dsa_or_static_volume_rendering_coverage():
    rows = source_rows()
    assert rows[8]['clinical_panels'] == list('abde')
    assert rows[10]['clinical_panels'] == ['a']
    assert rows[6]['clinical_panels'] == list('ac')
    assert rows[6]['source_context']['static_ct_volume_rendering_panels'] == list('bd')
    assert not rows[6]['source_context']['interactive_3d_or_complete_volume_coverage_granted']
    for number, panels in [(8, list('cf')), (10, list('bc'))]:
        row = rows[number]
        assert row['source_context']['radiographic_panels_are_digital_subtraction_angiography']
        assert row['ancillary_panels'][0]['kind'] == 'Radiography' and row['ancillary_panels'][0]['panels'] == panels
        assert all(row['source_context']['panel_types'][p] == 'Radiography' for p in panels)
    assert 'clinical_panels' not in rows[11]
    assert rows[11]['source_context']['caption_a_reference_without_visible_panel_label']
    assert 'no a panel label is visible' in rows[11]['caption']


def test_distinct_patients_phases_interventions_and_historical_grades_stay_explicit():
    rows = source_rows()
    for n in [1, 2, 6, 8]:
        context = rows[n]['source_context']
        assert context['multiple_reported_patients'] and len(set(context['panel_case_groups'].values())) == 2
    assert rows[1]['source_context']['source_phase_or_rendering_roles']['b'] == 'eight-minute delayed'
    assert rows[9]['source_context']['source_phase_or_rendering_roles'] == {'a': 'arterial', 'b': 'nephrographic'}
    assert rows[10]['source_context']['source_phase_or_rendering_roles']['c'] == 'DSA after stent'
    for row in rows.values():
        assert row['source_context']['historical_source_publication_year'] == 2015
        assert not row['source_context']['current_grade_reassigned']
        assert 'not reassigned under the current organ-specific revision' in row['limits']


def test_reader_links_preserve_pending_native_anatomical_and_model_review():
    ref = detail(Curriculum(), resolve('ra.ct-abdominal-trauma'))['radiology_reference']
    assert {i for s in ref['walkthrough']['steps'] for i in s['images'] if i.startswith('open-renal-trauma-')} == {r['id'] for r in ref['structure_atlas']}
    assets = [r for r in json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith('open-renal-trauma-')]
    assert len(assets) == 11
    for row in assets:
        assert row['structure_ids'] == [] and row['requirement_coverage'] == {} and row['anatomical_review']['status'] == 'pending'
        assert not row['source_context']['native_acquisition_and_registration_verified']
        assert not row['pixel_provenance']['highest_resolution_acquired_master_verified']
        rights = row['source']['license']
        assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT / rights['evidence_path']).read_bytes()).hexdigest() == rights['evidence_sha256']
