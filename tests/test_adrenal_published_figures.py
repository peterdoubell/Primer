"""Original figure pixels, source rights and mixed-modality limits remain explicit."""
import hashlib
import json
from pathlib import Path

from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/adrenal-published-source-review'


def test_original_pdf_samples_or_encoded_streams_are_preserved_in_every_asset():
    source = json.loads((REVIEW / 'original-source-review.json').read_text())
    packaged = json.loads((REVIEW / 'packaged-source-images.json').read_text())
    assert source['publisher_xml_pdf_and_media_md5_verified'] is True
    assert source['license'] == 'CC BY 4.0'
    assert source['excluded_figure']['figure_number'] == 10
    assert source['figure2_sequence_label_ambiguity_preserved'] is True
    assert len(source['figures']) == len(packaged['figures']) == 10
    expected = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11}
    assert {r['figure_number'] for r in source['figures']} == expected
    assert sum(r['acquisition'] == 'original_pdf_dct_stream_byte_identical' for r in source['figures']) == 2
    for r in packaged['figures']:
        s = next(x for x in source['figures'] if x['figure_number'] == r['figure_number'])
        path = ROOT / r['local_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == r['sha256'] == s['sha256']
        with Image.open(path) as image:
            assert list(image.size) == [s['width'], s['height']]
            assert hashlib.sha256(image.tobytes()).hexdigest() == s['decoded_pixel_sha256']
        assert s['width'] >= s['repository_dimensions'][0] and s['height'] >= s['repository_dimensions'][1]
        assert s['original_encoded_stream_or_decoded_sample_readback_verified'] is True
        assert s['source_pixels_changed'] is False and s['clinical_approval'] is False
    assert packaged['clinical_approval'] is False and packaged['structure_coverage_granted'] is False


def test_mixed_ct_mri_and_ultrasound_panels_have_distinct_selected_roles():
    ref = detail(Curriculum(), resolve('ra.adrenal-lesions'))['radiology_reference']
    images = [r for r in ref['structure_atlas'] if r['id'].startswith('open-adrenal-')]
    assert len(images) == 10
    for image in images:
        types = image['source_context']['panel_types']
        assert all(types[p] == image['modality'] for p in image['clinical_panels'])
        assert {p for a in image.get('ancillary_panels', []) for p in a['panels']}.isdisjoint(image['clinical_panels'])
        assert all(a['kind'] != image['modality'] for a in image.get('ancillary_panels', []))
    by_number = {r['figure_number']: r for r in images}
    assert by_number[8]['clinical_panels'] == ['b', 'c', 'd']
    assert by_number[8]['ancillary_panels'][0]['kind'] == 'Ultrasound'
    assert by_number[11]['clinical_panels'] == ['c', 'd', 'e', 'f']
    assert 'ambiguity' in by_number[2]['caption']
    assert all('not current management guidance' in r['limits'] for r in images)


def test_licensed_adrenal_candidates_do_not_claim_clinical_or_structure_approval():
    data = json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())
    rows = [r for r in data['assets'] if r['id'].startswith('open-adrenal-')]
    assert len(rows) == 10
    for row in rows:
        assert row['structure_ids'] == [] and row['requirement_coverage'] == {}
        assert row['anatomical_review']['status'] == 'pending'
        license = row['source']['license']
        assert license['commercial_use'] and license['redistribution'] and license['review_status'] == 'verified'
        assert hashlib.sha256((ROOT / license['evidence_path']).read_bytes()).hexdigest() == license['evidence_sha256']
        assert row['pixel_provenance']['source_pixels_changed'] is False
