"""Actual grayscale wall figures retain source rights, bands and clinical-context limits."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bowel-wall-published-source-review'
SELECTED = {6, 9, 12, 13, 14, 15, 17, 18, 20, 22}


def test_actual_cc_by_2_grant_is_preserved_and_not_combined_with_other_grants():
    permissions = ET.fromstring('<permissions xmlns:x="http://www.w3.org/1999/xlink"><license x:href="http://creativecommons.org/licenses/by/2.0/"/></permissions>')
    assert exact_license(permissions) == ('CC BY 2.0', 'https://creativecommons.org/licenses/by/2.0/')
    mixed = ET.fromstring('<permissions xmlns:x="http://www.w3.org/1999/xlink"><license x:href="https://creativecommons.org/licenses/by/2.0/"/><license x:href="https://creativecommons.org/licenses/by/4.0/"/></permissions>')
    with pytest.raises(ValueError):
        exact_license(mixed)
    restricted = ET.fromstring('<permissions xmlns:x="http://www.w3.org/1999/xlink"><license x:href="https://creativecommons.org/licenses/by-nc/2.0/"/></permissions>')
    with pytest.raises(ValueError):
        exact_license(restricted)


def test_all_ten_complete_figures_preserve_native_grayscale_samples_or_encoded_streams():
    proof = json.loads((REVIEW / 'original-source-review.json').read_text())
    package = json.loads((REVIEW / 'packaged-source-images.json').read_text())
    assert {r['figure_number'] for r in proof['figures']} == SELECTED
    assert len(package['figures']) == 10 and len(proof['rights_holds']) == 12
    assert all(not r['runtime_promoted'] for r in proof['rights_holds'])
    assert proof['articles'][0]['license'] == 'CC BY 2.0'
    methods = {}
    for row in package['figures']:
        source = next(r for r in proof['figures'] if r['figure_number'] == row['figure_number'])
        path = ROOT / row['local_path']; assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'] == source['sha256']
        with Image.open(path) as image:
            assert image.mode == 'L' and image.size == (source['width'], source['height'])
            assert hashlib.sha256(image.tobytes()).hexdigest() == source['decoded_pixel_sha256']
        assert source['publisher_media_md5_verified'] and not source['source_pixels_changed']
        methods[source['figure_number']] = source['acquisition']
    assert {n for n, m in methods.items() if m == 'lossless_png_original_devicegray_pdf_samples_exact'} == {9, 20, 22}
    assert sum(m == 'original_pdf_dct_stream_byte_identical' for m in methods.values()) == 7


def test_reader_retains_original_labels_unlettered_figures_and_source_only_diagnoses():
    ref = detail(Curriculum(), resolve('ra.ct-bowel-wall'))['radiology_reference']
    rows = {r['figure_number']: r for r in ref['structure_atlas'] if r['id'].startswith('open-bowel-wall-')}
    assert set(rows) == SELECTED
    assert rows[9]['clinical_panels'] == rows[20]['clinical_panels'] == rows[22]['clinical_panels'] == ['a', 'b']
    assert all('clinical_panels' not in r for n, r in rows.items() if n not in {9, 20, 22})
    assert 'not a healthy or non-IBD example' in rows[17]['caption']
    assert 'not an independent microbiological diagnosis' in rows[14]['caption']
    assert 'do not independently prove those results' in rows[22]['caption']
    assert 'Complete fistula tract/openings' in rows[13]['caption']
    assert all(r['source_background'] == 'white' and not r['source_context']['native_phase_timing_verified'] for r in rows.values())
    assert all(not r['source_context']['independent_patient_identity_verified'] for r in rows.values())


def test_cleared_source_pixels_do_not_grant_wall_layer_fistula_or_model_coverage():
    rows = [r for r in json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith('open-bowel-wall-')]
    assert len(rows) == 10
    for row in rows:
        assert row['structure_ids'] == [] and row['requirement_coverage'] == {} and row['anatomical_review']['status'] == 'pending'
        rights = row['source']['license']; assert rights['name'] == 'CC BY 2.0'
        assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT / rights['evidence_path']).read_bytes()).hexdigest() == rights['evidence_sha256']
        assert not row['pixel_provenance']['highest_resolution_acquired_master_verified']
