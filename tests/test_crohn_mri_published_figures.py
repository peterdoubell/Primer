"""MRI sequence, patient and temporal context cannot be borrowed across panels."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/crohn-mri-published-source-review'


def source_rows():
    return {r['figure_number']: r for r in detail(Curriculum(), resolve('ra.mri-crohn'))['radiology_reference']['structure_atlas']}


def test_five_complete_original_jpegs_keep_native_pixels_and_exact_grant():
    proof = json.loads((REVIEW / 'original-source-review.json').read_text())
    package = json.loads((REVIEW / 'packaged-source-images.json').read_text())
    assert len(proof['figures']) == len(package['figures']) == 5
    article = proof['articles'][0]
    assert article['license'] == 'CC BY 4.0' and article['publisher_xml_pdf_md5_verified']
    assert set(r['figure_number'] for r in proof['figures']) == {1, 2, 3, 4, 6}
    for row in package['figures']:
        original = next(r for r in proof['figures'] if r['figure_number'] == row['figure_number'])
        path = ROOT / row['local_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'] == original['sha256']
        assert original['acquisition'] == 'original_pdf_dct_stream_byte_identical'
        assert original['width'] > original['repository_dimensions'][0]
        with Image.open(path) as image:
            assert image.size == (original['width'], original['height'])
            assert hashlib.sha256(image.tobytes()).hexdigest() == original['decoded_pixel_sha256']
        assert original['publisher_media_md5_verified'] and not original['source_pixels_changed']


def test_actual_lowercase_mri_panels_remain_distinct_from_ct_and_ultrasound():
    rows = source_rows()
    assert {n: r['clinical_panels'] for n, r in rows.items()} == {1: list('cde'), 2: list('cd'), 3: list('abcdef'), 4: list('abd'), 6: ['a']}
    for row in rows.values():
        assert row['modality'] == 'MRI'
        types = row['source_context']['panel_types']
        assert all(types[p] == 'MRI' for p in row['clinical_panels'])
        assert set(row['source_context']['source_mri_sequences']) == set(row['clinical_panels'])
        for ancillary in row.get('ancillary_panels', []):
            assert all(types[p] == ancillary['kind'] for p in ancillary['panels'])
    assert rows[4]['source_context']['panel_types'] == {'a': 'MRI', 'b': 'MRI', 'c': 'CT', 'd': 'MRI', 'e': 'CT', 'f': 'Ultrasound', 'g': 'Ultrasound'}


def test_distinct_patients_missing_sequences_and_timepoints_are_preserved():
    rows = source_rows()
    assert rows[1]['source_context']['adc_panel_supplied'] is False
    assert 'No ADC panel is supplied' in rows[1]['caption']
    context = rows[2]['source_context']
    assert context['multiple_reported_patients']
    assert context['panel_case_groups']['a'] != context['panel_case_groups']['c']
    context = rows[3]['source_context']
    assert context['panel_timepoints'] == dict.fromkeys('abc', 'baseline') | dict.fromkeys('def', 'six-month follow-up')
    assert not context['independent_spatial_registration_verified']
    assert rows[4]['source_context']['panel_timepoints']['e'] == 'not separately established'
    assert rows[6]['source_context']['referred_fat_suppressed_sequences_supplied'] is False
    assert rows[6]['source_context']['panel_timepoints']['b'] == 'two months later CT'
    assert 'Later CT cannot supply baseline MRI signal' in rows[6]['caption']


def test_reporting_links_do_not_grant_native_sequence_or_structure_coverage():
    ref = detail(Curriculum(), resolve('ra.mri-crohn'))['radiology_reference']
    linked = {i for s in ref['walkthrough']['steps'] for i in s['images'] if i.startswith('open-crohn-mri-')}
    assert linked == {r['id'] for r in ref['structure_atlas']}
    assets = [r for r in json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith('open-crohn-mri-')]
    assert len(assets) == 5
    for row in assets:
        assert row['structure_ids'] == [] and row['requirement_coverage'] == {}
        assert row['anatomical_review']['status'] == 'pending'
        assert row['source_context']['native_sequence_and_registration_verified'] is False
        rights = row['source']['license']
        assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT / rights['evidence_path']).read_bytes()).hexdigest() == rights['evidence_sha256']
        assert not row['pixel_provenance']['highest_resolution_acquired_master_verified']
