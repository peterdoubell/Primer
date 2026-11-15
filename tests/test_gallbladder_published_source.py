"""Preserve original wall and complication images without dropping PDF mask information."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/gallbladder-published-source-review'


def test_all_nine_original_figures_have_exact_preserved_pixels_and_source_grants():
    proof=json.loads((REVIEW/'original-source-review.json').read_text())
    assert len(proof['figures'])==9
    assert all(a['license']=='CC BY 4.0' and a['publisher_xml_pdf_md5_verified'] for a in proof['articles'])
    for row in proof['figures']:
        path=REVIEW/row['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        with Image.open(path) as image:
            assert image.size==(row['width'],row['height']) and image.mode==row['pixel_mode']
            assert hashlib.sha256(image.tobytes()).hexdigest()==row['decoded_pixel_sha256']
        assert row['publisher_media_md5_verified'] and row['original_colour_and_mask_readback_verified']
        assert row['source_samples_changed'] is False and row['clinical_approval'] is False
    assert proof['separately_credited_figure_excluded']=={'pmcid':'PMC5359147','figure':4}
    assert proof['runtime_promoted'] is False
    mixed=next(r for r in proof['figures'] if (r['pmcid'],r['figure_number'])==('PMC12181115',4))
    assert mixed['source_panel_roles']=={'a':'Ultrasound','b':'CT','c':'Radiography'}


def test_perforation_soft_mask_is_retained_without_an_opaque_jpeg_substitution():
    proof=json.loads((REVIEW/'original-source-review.json').read_text())
    row=next(r for r in proof['figures'] if (r['pmcid'],r['figure_number'])==('PMC12181115',6))
    assert row['pixel_mode']=='RGBA' and row['soft_mask']['source_mask_preserved'] is True
    assert row['soft_mask']['paper_background_compositing_review_required'] is True
    assert row['panel_identifier_scheme']=='position_unlettered'
    assert row['source_panel_roles']=={'left':'Ultrasound','middle':'CT','right':'CT'}
    with Image.open(REVIEW/row['file']) as image:
        assert hashlib.sha256(image.getchannel('A').tobytes()).hexdigest()==row['soft_mask']['decoded_alpha_sha256']
        assert hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()==row['soft_mask']['original_colour_sha256']
        assert list(image.getchannel('A').getextrema())==row['soft_mask']['alpha_range']==[225,255]
    assert any('Twinkling Doppler artifact is not wall hypervascularity' in s for s in proof['limits'])
