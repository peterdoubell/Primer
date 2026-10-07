import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_original_masters_and_semantic_discrepancies_remain_source_specific():
    r=json.loads((ROOT/'docs/trigeminal-published-source-review/original-source-review.json').read_text())
    assert r['original_article_grant']=='CC BY 4.0' and len(r['figures'])==9
    assert [x['figure_number'] for x in r['figures']]==[1,6,12,13,19,20,21,22,28]
    assert all(x['original_decoded_samples_and_ICC_preserved'] and not x['source_pixels_resampled_or_enhanced'] for x in r['figures'])
    assert all(x['numbered_HTML_PDF_thumbnail_RGB_RMS']<2 for x in r['figures'])
    assert r['figures'][1]['source_ICC_name']=='IEC 61966-2.1 Default RGB colour space - sRGB'
    assert r['figures'][6]['source_caption_mandibular_V2_discrepancy']
    assert 'not silently corrected' in r['source_semantic_limits']['Fig21']
    assert '0/6/12 months' in r['source_semantic_limits']['Fig19']
    assert 'Normal reference' in r['source_semantic_limits']['Fig1']
    assert not r['original_anatomical_or_case_approval_granted'] and not r['runtime_promoted'] and not r['structure_coverage_granted']
