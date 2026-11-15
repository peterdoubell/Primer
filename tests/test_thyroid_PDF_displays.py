import hashlib,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/thyroid-pictorial-source-review'
def test_all_figures_preserve_streams_and_do_not_claim_native_RGB_or_clinical_approval():
    original=json.loads((OUT/'original-source-review.json').read_text());r=json.loads((OUT/'PDF-display-review.json').read_text())
    assert r['original_PDF_sha256']==original['original_PDF_sha256']
    assert len(r['figures'])==21 and r['source_output_intent']=='Coated FOGRA39 (ISO 12647-2:2004)'
    assert r['render_DPI']==72 and r['isolated_page_points_equal_source_pixel_dimensions']
    assert r['rendered_displays_are_derived_PDF_outputs'] and not r['direct_ICC_shortcut_matches_PDF_DeviceN_renderer']
    assert not r['source_US_acquisition_or_diagnostic_display_calibration_verified']
    for key in ['clinical_approval','runtime_promoted','structure_coverage_granted']:assert r[key] is False
    for source,display in zip(original['figures'],r['figures']):
        assert (source['figure_number'],source['original_PDF_object'],source['original_master_size'])==(display['figure_number'],display['original_PDF_object'],display['dimensions'])
        assert display['original_image_stream_and_decoded_channels_preserved_in_isolated_PDF'] and display['entire_original_image_object_rendered']
        assert not display['post_render_resampling_or_anatomical_edits'] and not display['rendered_RGB_is_unchanged_native_source_samples']
def test_cached_displays_preserve_declared_rgb_samples_and_profile():
    Image=pytest.importorskip('PIL.Image')
    cache=ROOT.parent/'thyroid-source-review/PDF-aware-display-review'
    if not cache.exists():pytest.skip('Original source/render cache unavailable')
    r=json.loads((OUT/'PDF-display-review.json').read_text());profile=(cache/'display-sRGB.icc').read_bytes()
    assert hashlib.sha256(profile).hexdigest()==r['display_sRGB_profile_sha256']
    for row in r['figures']:
        path=cache/row['display_file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['display_sha256']
        with Image.open(path) as im:
            assert im.mode=='RGB' and list(im.size)==row['dimensions'] and im.info['icc_profile']==profile
            assert hashlib.sha256(im.tobytes()).hexdigest()==row['decoded_display_RGB_sha256']
