"""Original bowel/mesenteric CT artwork does not grant phase, case or compartment assumptions."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bowel-trauma-published-source-review'


def source_rows():
    return {r['id']: r for r in detail(Curriculum(), resolve('ra.ct-abdominal-trauma'))['radiology_reference']['structure_atlas'] if r['id'].startswith('open-bowel-trauma-')}


def test_all_four_original_jpeg_streams_keep_pixels_and_exact_source_grants():
    proof = json.loads((REVIEW / 'original-source-review.json').read_text())
    package = json.loads((REVIEW / 'packaged-source-images.json').read_text())
    assert len(proof['figures']) == len(package['figures']) == 4
    assert {a['pmcid']: a['license'] for a in proof['articles']} == {'PMC6780049': 'CC BY 4.0', 'PMC7676803': 'CC BY 4.0'}
    for row in package['figures']:
        original = next(r for r in proof['figures'] if (r['pmcid'], r['figure_number']) == (row['pmcid'], row['figure_number']))
        path = ROOT / row['local_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'] == original['sha256']
        with Image.open(path) as image:
            assert image.mode == 'RGB' and image.size == (original['width'], original['height'])
            assert hashlib.sha256(image.tobytes()).hexdigest() == original['decoded_pixel_sha256']
        assert original['width'] > original['repository_dimensions'][0]
        assert original['acquisition'] == 'original_pdf_dct_stream_byte_identical'
        assert original['publisher_media_md5_verified'] and not original['source_pixels_changed']
    assert all(a['publisher_xml_pdf_md5_verified'] for a in proof['articles'])
    assert all(not h['runtime_promoted'] for h in proof['rights_holds'])


def test_repeated_pdf_artwork_and_unknown_case_phase_relationships_stay_explicit():
    proof = json.loads((REVIEW / 'original-source-review.json').read_text())
    for r in proof['figures']:
        if r['pmcid'] == 'PMC6780049':
            assert r['repeated_same_artwork_pdf_object_ids'] == {1: [120, 141], 2: [121, 142], 3: [122, 143]}[r['figure_number']]
            assert r['original_pdf_placements']
    rows = source_rows()
    for row in rows.values():
        assert row['modality'] == 'CT' and not row['source_context']['source_phase_specified']
        assert not row['source_context']['native_acquisition_phase_and_registration_verified']
        if 'pmc6780049' in row['id']:
            assert row['clinical_panels'] == ['A', 'B']
            assert row['source_context']['same_patient_between_panels_not_established']
            assert row['source_context']['repeated_pdf_artwork_is_not_independent_case_evidence']


def test_case_compartment_conflict_calipers_unlettered_views_and_missing_baseline_remain_unresolved():
    row = source_rows()['open-bowel-trauma-pmc7676803-fig1']
    context = row['source_context']
    assert context['source_caption_compartment_claim'] == 'intraluminal'
    assert context['source_body_compartment_claim'] == 'intramural'
    assert context['source_compartment_claims_unresolved']
    assert context['initial_ct_at_first_visit_reported'] is False
    assert context['source_caliper_calibration_independently_verified'] is False
    assert context['actual_unlettered_view_roles'] == {'left': 'coronal', 'right': 'axial'}
    assert 'clinical_panels' not in row
    assert 'not a matched negative-to-positive CT comparison' in row['caption']
    assert 'No A/B letters are added' in row['caption']


def test_source_step_links_do_not_grant_anatomical_or_model_coverage():
    ref = detail(Curriculum(), resolve('ra.ct-abdominal-trauma'))['radiology_reference']
    assert {i for s in ref['walkthrough']['steps'] for i in s['images'] if i.startswith('open-bowel-trauma-')} == set(source_rows())
    assets = [r for r in json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if r['id'].startswith('open-bowel-trauma-')]
    assert len(assets) == 4
    for row in assets:
        assert row['structure_ids'] == [] and row['requirement_coverage'] == {} and row['anatomical_review']['status'] == 'pending'
        assert not row['pixel_provenance']['highest_resolution_acquired_master_verified']
        rights = row['source']['license']
        assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT / rights['evidence_path']).read_bytes()).hexdigest() == rights['evidence_sha256']
