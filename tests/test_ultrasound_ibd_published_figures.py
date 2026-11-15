"""Full original IUS figures retain distinct patient/modality roles and native gray samples."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/ultrasound-ibd-published-source-review'


def source_rows():
    return {r['figure_number']: r for r in detail(Curriculum(), resolve('ra.ultrasound-ibd'))['radiology_reference']['structure_atlas']}


def test_four_complete_original_figures_reuse_three_files_and_preserve_native_gray():
    proof = json.loads((REVIEW / 'original-source-review.json').read_text())
    package = json.loads((REVIEW / 'packaged-source-images.json').read_text())
    assert len(proof['figures']) == len(package['figures']) == 4
    assert proof['articles'][0]['license'] == 'CC BY 4.0'
    for row in package['figures']:
        original = next(r for r in proof['figures'] if r['figure_number'] == row['figure_number'])
        path = ROOT / row['local_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == original['sha256'] == row['sha256']
        with Image.open(path) as image:
            assert image.size == (original['width'], original['height'])
            assert hashlib.sha256(image.tobytes()).hexdigest() == original['decoded_pixel_sha256']
            if row['figure_number'] == 5:
                assert image.mode == 'L' and original['acquisition'] == 'lossless_png_original_pdf_gray_samples_exact'
            else:
                assert 'crohn-mri-pmc12634764-fig' in row['local_path']
                assert original['acquisition'] == 'original_pdf_dct_stream_byte_identical'
        assert original['publisher_media_md5_verified'] and not original['source_pixels_changed']


def test_actual_ultrasound_panels_and_separate_patient_time_and_ct_labels_remain_explicit():
    rows = source_rows()
    assert {n: r['clinical_panels'] for n, r in rows.items()} == {1: list('ab'), 2: list('ab'), 4: list('fg'), 5: ['a']}
    for row in rows.values():
        assert row['modality'] == 'Ultrasound'
        context = row['source_context']
        assert not context['real_time_or_cine_source_supplied'] and not context['doppler_settings_verified']
        assert all(context['panel_types'][p] == 'Ultrasound' for p in row['clinical_panels'])
        for other in row['ancillary_panels']:
            assert all(context['panel_types'][p] == other['kind'] for p in other['panels'])
    assert rows[2]['source_context']['panel_case_groups']['a'] != rows[2]['source_context']['panel_case_groups']['c']
    assert rows[4]['source_context']['panel_timepoints']['f'] == 'one week later'
    assert rows[5]['source_context']['panel_types'] == {'a': 'Ultrasound', 'b': 'CT'}
    assert rows[5]['source_context']['ct_b_contains_two_source_views']
    assert 'no c label is invented' in rows[5]['caption']


def test_source_links_grant_no_dynamic_or_anatomical_coverage():
    ref = detail(Curriculum(), resolve('ra.ultrasound-ibd'))['radiology_reference']
    assert {i for s in ref['walkthrough']['steps'] for i in s['images'] if i.startswith('open-ultrasound-ibd-')} == {r['id'] for r in ref['structure_atlas']}
    assets = [r for r in json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith('open-ultrasound-ibd-')]
    assert len(assets) == 4
    for row in assets:
        assert row['structure_ids'] == [] and row['requirement_coverage'] == {} and row['anatomical_review']['status'] == 'pending'
        assert not row['source_context']['native_acquisition_and_dynamic_source_verified']
        rights = row['source']['license']
        assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT / rights['evidence_path']).read_bytes()).hexdigest() == rights['evidence_sha256']
