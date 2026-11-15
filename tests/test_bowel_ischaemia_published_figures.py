"""Published arterial/venous examples retain exact pixels and source-only claims."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bowel-ischaemia-published-source-review'


def test_eight_complete_ct_figures_preserve_pdf_streams_and_existing_phase_pairs():
    source = json.loads((REVIEW / 'original-source-review.json').read_text())
    packaged = json.loads((REVIEW / 'packaged-source-images.json').read_text())
    assert len(source['figures']) == len(packaged['figures']) == 8
    assert {r['figure_number'] for r in packaged['figures']} == set(range(2, 10))
    assert source['articles'][0]['license'] == 'CC BY 4.0'
    assert source['articles'][0]['publisher_xml_pdf_md5_verified']
    for row in packaged['figures']:
        original = next(r for r in source['figures'] if r['figure_number'] == row['figure_number'])
        path = ROOT / row['local_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'] == original['sha256']
        assert original['acquisition'] == 'original_pdf_dct_stream_byte_identical'
        assert original['publisher_media_md5_verified'] and not original['source_pixels_changed']
        with Image.open(path) as image:
            assert image.size == (original['width'], original['height'])
            assert hashlib.sha256(image.tobytes()).hexdigest() == original['decoded_pixel_sha256']
        assert row['reuses_existing_obstruction_file'] == (row['figure_number'] in {2, 3, 4})
        if row['reuses_existing_obstruction_file']:
            assert path.name.startswith('bowel-obstruction-')


def test_phase_projection_repeat_case_and_histological_limits_survive_reader_delivery():
    ref = detail(Curriculum(), resolve('ra.ct-bowel-ischaemia'))['radiology_reference']
    rows = {r['figure_number']: r for r in ref['structure_atlas'] if r['id'].startswith('open-bowel-ischaemia-')}
    assert set(rows) == set(range(2, 10))
    assert rows[2]['source_context']['source_case_group'] == rows[3]['source_context']['source_case_group']
    assert rows[4]['source_context']['panel_acquisition_claims']['C'] == 'unenhanced; source repeats A'
    assert rows[5]['source_context']['panel_acquisition_claims'] == {'A': 'venous phase', 'B': 'arterial phase'}
    assert 'maximum intensity projection' in rows[7]['source_context']['panel_acquisition_claims']['B']
    assert 'phase/contrast not separately specified' == rows[8]['source_context']['panel_acquisition_claims']['B']
    assert 'necrotic changes confined to mucosa' in rows[8]['caption']
    assert 'does not independently prove' in rows[8]['caption']
    assert 'vessel-size ratio alone does not establish' in rows[9]['caption']
    for row in rows.values():
        assert not row['source_context']['independent_acquisition_metadata_verified']
        assert row['source_background'] == 'white' and row['modality'] == 'CT'
        assert row['clinical_panels'] == list(row['source_context']['panel_acquisition_claims'])


def test_rights_review_does_not_grant_full_wall_vascular_or_three_dimensional_coverage():
    data = json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())
    rows = [r for r in data['assets'] if r['id'].startswith('open-bowel-ischaemia-')]
    assert len(rows) == 8
    for row in rows:
        assert row['structure_ids'] == [] and row['requirement_coverage'] == {}
        assert row['anatomical_review']['status'] == 'pending'
        rights = row['source']['license']
        assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT / rights['evidence_path']).read_bytes()).hexdigest() == rights['evidence_sha256']
        assert row['pixel_provenance']['source_pixels_changed'] is False
        assert row['pixel_provenance']['highest_resolution_acquired_master_verified'] is False
