import hashlib,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/thyroid-pictorial-source-review'
def test_source_binding_retains_original_float_order_and_colour_limits():
    r=json.loads((OUT/'original-source-review.json').read_text())
    assert r['original_article_grant']=='CC BY 4.0' and len(r['figures'])==21
    assert [x['original_PDF_object'] for x in r['figures']]==[33,34,32,36,37,38,39,44,46,43,45,49,50,52,51,54,55,56,57,61,62]
    assert r['figures'][9]['original_CMYK_channels_verified'] and not r['figures'][9]['browser_RGB_mapping_independently_approved']
    assert all(x['all_256_source_tints_verified_pure_CMYK_Black'] for x in r['figures'] if x['figure_number']!=10)
    assert all(x['publisher_figure_MD5_verified'] and not x['source_colour_interpretation_and_independent_anatomical_approval'] for x in r['figures'])
    assert all(x['original_master_size'][0]>=1032 for x in r['figures'])
    assert not r['figures_are_assumed_same_patient_or_matched_planes'] and not r['runtime_promoted'] and not r['structure_coverage_granted'] and not r['clinical_approval']
    assert hashlib.sha256((OUT/'PMC8864691.1.json').read_bytes()).hexdigest()==r['metadata_sha256']
def test_original_source_colour_channels_roundtrip_when_cache_exists(tmp_path):
    pytest.importorskip('pypdf');pytest.importorskip('PIL')
    from tools.anatomy_sources.review_thyroid_pictorial_original import review
    source=ROOT.parent/'thyroid-source-review'
    if not (source/'PMC8864691.1.pdf').exists():pytest.skip('Original source cache unavailable')
    review(source,tmp_path)
    assert (tmp_path/'original-source-review.json').read_bytes()==(OUT/'original-source-review.json').read_bytes()
