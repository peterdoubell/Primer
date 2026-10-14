"""Publisher locators preserve source images and cannot claim tissue segmentation."""
import gzip
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/thoracic-source-label-review-20261014'
ORIGINAL = ROOT / 'docs/thoracic-ultrasound-source-review-20261013'


def test_every_locator_uses_an_unchanged_original_source_and_bounded_pixel_rect():
    manifest = json.loads((REVIEW / 'manifest.json').read_text())
    assert len(manifest['images']) == 6
    assert sum(len(r['locations']) for r in manifest['images']) == 27
    assert manifest['clinical_approval'] is manifest['structure_coverage_granted'] is False
    assert manifest['three_dimensional_registration'] is manifest['original_images_modified'] is False
    original_manifest = json.loads((ORIGINAL / 'manifest.json').read_text())
    for row in manifest['images']:
        encoded = (REVIEW / row['file']).read_bytes()
        assert encoded == (ORIGINAL / 'assets' / row['id']).read_bytes()
        assert hashlib.sha256(encoded).hexdigest() == row['sha256']
        assert list(Image.open(REVIEW / row['file']).size) == row['dimensions']
        source = row['source_metadata']
        assert source == original_manifest['sources'][row['source_id']]
        evidence = gzip.decompress((ORIGINAL / source['jats_path']).read_bytes())
        assert hashlib.sha256(evidence).hexdigest() == source['jats_sha256']
        assert source['authors'] and source['license'] == 'CC BY 4.0'
        assert len({r['id'] for r in row['locations']}) == len(row['locations'])
        for location in row['locations']:
            x, y, w, h = location['rect']
            assert all(type(v) is int for v in [x, y, w, h])
            assert x >= 0 and y >= 0 and w > 0 and h > 0
            assert x+w <= row['dimensions'][0] and y+h <= row['dimensions'][1]
            assert location['segmented_tissue_boundary'] is False


def test_actual_browser_crops_and_coordinates_cover_every_locator_at_both_widths():
    manifest = json.loads((REVIEW / 'manifest.json').read_text())
    proof = json.loads((REVIEW / 'browser-proof.json').read_text())
    expected = {(w, r['id'], loc['id']) for w in [1440, 390]
                for r in manifest['images'] for loc in r['locations']}
    assert {(r['width'], r['image'], r['location']) for r in proof['rows']} == expected
    assert len(proof['rows']) == 54 and not proof['errors']
    assert proof['failed_source_hides_previous_image']
    assert all(r['native_decoded_crop_pixels_exact'] and r['locator_coordinates_match_original_pixels'] for r in proof['rows'])
    for name, digest in proof['implementation_sha256'].items():
        assert hashlib.sha256((REVIEW / name).read_bytes()).hexdigest() == digest


def test_locator_and_inflow_limits_are_visible_to_the_reader():
    html = (REVIEW / 'index.html').read_text()
    assert '[hidden]{display:none!important}' in html
    assert 'not a tissue boundary' in html
    assert 'Signal panels do not identify valve leaflet morphology' in html
    assert 'current-patient diagnosis' in html
