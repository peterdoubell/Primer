"""Native publication preservation, complete source roles and no invented coverage."""
import copy
import hashlib
import io
import json
from pathlib import Path

import pytest

from tools.anatomy_sources import package_traumatic_haemorrhage_sources as packaging

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/traumatic-haemorrhage-source-review'


@pytest.fixture(scope='module')
def proposal():
    return json.loads((REVIEW / 'integration-proposal.json').read_text())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def test_complete_publication_and_all_fifteen_native_objects_retained(proposal):
    proof = json.loads((REVIEW / 'original-source-review.json').read_text())
    assert proof['main_figure_numbers'] == list(range(1, 15))
    assert proof['native_image_object_count'] == len(proposal['images']) == 15
    assert proof['page_count'] == 50 and proof['original_PDF_bytes'] == 3032469
    raw = (ROOT / proof['original_PDF_path']).read_bytes()
    assert digest(raw) == proof['original_PDF_sha256'] == packaging.PDF_SHA
    assert raw == (REVIEW / 'source-center-tbi-2024' / packaging.PDF_NAME).read_bytes()
    assert proof['license'] == 'CC BY 4.0'
    assert proof['license_url'] == 'https://creativecommons.org/licenses/by/4.0/'
    assert proof['grant_page_1_based'] == 1
    assert not proof['publisher_MD5_or_other_publisher_digest_supplied']
    assert not proof['highest_resolution_publisher_master_verified']
    assert proposal['originals_plus_display_total_bytes'] == 24471521
    assert digest((REVIEW / 'original-source-review.json').read_bytes()) == proposal['source_review_sha256']
    packaging.validate_proposal(proposal)


def test_exact_encoded_streams_are_real_original_pdf_objects(proposal):
    PdfReader = pytest.importorskip('pypdf').PdfReader
    Image = pytest.importorskip('PIL.Image')
    reader = PdfReader(ROOT / 'web/reference-media/radiology-open/traumatic-haemorrhage' / packaging.PDF_NAME)
    assert 'Creative Commons License (CC-BY)' in reader.pages[0].extract_text()
    assert reader.trailer['/Root'].get('/OutputIntents') is None
    for fact in proposal['source_figures']:
        obj = reader.get_object(fact['PDF_object_id'])
        original = (ROOT / fact['original_encoded_stream_path']).read_bytes()
        assert original == obj._data
        assert digest(original) == fact['original_encoded_stream_sha256']
        assert obj['/Filter'] == '/DCTDecode'
        assert str(obj['/ColorSpace']) == '/' + fact['source_color_space']
        assert obj['/Width'] == fact['width'] and obj['/Height'] == fact['height']
        with Image.open(io.BytesIO(original)) as image:
            assert image.size == (fact['width'], fact['height'])
            assert image.mode == fact['original_stream_Pillow_mode']
            assert digest(image.tobytes()) == fact['original_stream_Pillow_decoded_sha256']
            assert 'icc_profile' not in image.info
        assert not fact['source_geometry_changed'] and not fact['source_crop_resample_or_repaint']
        assert packaging.caption(reader, fact['figure_identifier'], fact['caption_page_1_based']) == fact['source_caption_full']


def test_lossless_display_uses_native_dimensions_and_declared_pdf_colour_conversion(proposal):
    Image = pytest.importorskip('PIL.Image')
    for fact in proposal['source_figures']:
        raw = (ROOT / fact['display_path']).read_bytes()
        assert len(raw) == fact['display_bytes'] and digest(raw) == fact['display_sha256']
        with Image.open(io.BytesIO(raw)) as image:
            assert image.format == 'PNG' and image.mode == 'RGB'
            assert image.size == (fact['width'], fact['height'])
            assert digest(image.tobytes()) == fact['display_RGB_sample_sha256']
        assert fact['display_colour_conversion_applied']
        assert not fact['source_ICC_profile_supplied'] and not fact['PDF_output_intent_supplied']
    for asset in proposal['assets']:
        p = asset['pixel_provenance']
        assert p['source_pixels_changed']
        assert p['source_pixels_changed_reason'].startswith('Declared colour-space interpretation only')
        assert not p['source_geometry_changed'] and not p['cropped_resampled_or_repainted']


def test_pdf_renderer_independently_reconstructs_all_original_dimensions_and_samples(proposal):
    pymupdf = pytest.importorskip('pymupdf')
    document = pymupdf.open(ROOT / 'web/reference-media/radiology-open/traumatic-haemorrhage' / packaging.PDF_NAME)
    for fact in proposal['source_figures']:
        original = pymupdf.Pixmap(document, fact['PDF_object_id'])
        rgb = pymupdf.Pixmap(pymupdf.csRGB, original)
        assert original.n == fact['PDF_decoded_channel_count']
        assert digest(original.samples) == fact['PDF_decoded_channel_sha256']
        assert (rgb.width, rgb.height) == (fact['width'], fact['height'])
        assert digest(rgb.samples) == fact['display_RGB_sample_sha256']
    document.close()


def test_all_sixty_seven_clinical_panels_keep_modality_and_case_relationships(proposal):
    from primer.radiology_catalog import _validate_source_panel_roles
    rows = {r['figure_identifier']: r for r in proposal['images']}
    assert sum(len(r['source_context'].get('panel_types', {})) for r in rows.values()) == 67
    assert sum(t == 'MRI' for r in rows.values() for t in r['source_context'].get('panel_types', {}).values()) == 4
    for row in rows.values():
        _validate_source_panel_roles(row)
        assert row['source_context']['population']['life_stage'] == 'unknown'
        assert row['source_context']['laterality'] == 'unknown'
    panel = rows['2-panel-2']
    assert panel['modality'] == 'CT' and panel['ancillary_panels'][0]['panels'] == ['L4', 'L5']
    assert set(panel['clinical_panels']).isdisjoint({'L4', 'L5'})
    c = panel['source_context']
    assert c['time_descriptions']['J4'].startswith('2 hours later')
    assert c['time_descriptions']['J5'].startswith('2 days later')
    assert c['source_reconsidered_initial_J3_diagnosis'].startswith('Likely small intracerebral haemorrhage')
    assert not c['cross_modality_same_patient_registration_established']
    assert rows['9']['source_context']['different_patients_explicit_in_caption'] == [['A'], ['B']]
    assert not rows['3']['source_context']['carotid_dissection_demonstrated']
    assert not rows['7']['source_context']['matching_CT_supplied']
    assert rows['2-panel-1']['source_context']['source_3D_volume_rendered_views'] == ['A2', 'A4', 'A6']


def test_original_numbers_diagnoses_and_cohort_plots_do_not_grant_coverage(proposal):
    proof = json.loads((REVIEW / 'original-source-review.json').read_text())
    assert not proof['clinical_approval'] and not proof['fine_structure_coverage_granted']
    assert not proof['patient_consent_independently_verified']
    assert proof['supplementary_source_documents']['publisher_listed_DOCX_count'] == 52
    assert proof['supplementary_source_documents']['acquired_count'] == 0
    assert {'PMC5307932', 'PMC3026928', 'PMC4734784'}.issubset({s['pmcid'] for s in proof['excluded_sources']})
    for row, asset in zip(proposal['images'], proposal['assets']):
        assert row['id'] == asset['id'] and row['source_context'] == asset['source_context']
        assert asset['structure_ids'] == [] and asset['requirement_coverage'] == {}
        assert asset['anatomical_review']['status'] == 'pending'
        assert asset['source']['license']['commercial_use'] and asset['source']['license']['redistribution']
        assert not row['source_context']['native_DICOM_or_volumetric_stack_supplied']
        assert row['original_encoded_stream']['browser_display_without_PDF_colour_interpretation_is_not_authoritative']
        if row['modality'] == 'Schematic':
            assert row['kind'] == 'schematic'
            assert row['source_context']['statistical_population_plot_not_patient_image']
            assert 'clinical_panels' not in row


def test_ninds_original_documents_publisher_digests_and_all_native_appendix_media_retained():
    import urllib.parse
    import xml.etree.ElementTree as ET
    from zipfile import ZipFile
    Image = pytest.importorskip('PIL.Image')
    context = json.loads((REVIEW / 'ninds-2025-source-context-proposal.json').read_text())
    source = REVIEW / 'source-ninds-2025'
    assert context['pmcid'] == 'PMC12409119' and context['doi'] == '10.1089/neu.2025.0079'
    assert 'https://creativecommons.org/licenses/by/4.0/' in context['permissions_XML']
    assert context['license'] == context['borrowed_figure_donor']['license'] == 'CC BY 4.0'
    assert context['borrowed_figure_donor']['source_appendix_disclosed_slight_revision_retained']
    assert not context['borrowed_figure_donor']['figure_specific_excluded_credit_found']
    assert len(context['documents']) == 3 and context['total_public_context_document_bytes'] == 14403832
    for record in context['source_files']:
        raw = (source / record['filename']).read_bytes()
        assert digest(raw) == record['sha256'] and len(raw) == record['bytes']
        assert hashlib.md5(raw).hexdigest() == record['publisher_MD5']
        assert record['publisher_MD5_verified']
    for document in context['documents']:
        raw = (ROOT / document['local_path']).read_bytes()
        assert digest(raw) == document['sha256'] and len(raw) == document['bytes']
        assert document['unchanged_original'] and not document['clinical_approval']
    with ZipFile(source / 'neu.2025.0079_supplementary_appendix.docx') as original:
        assert context['native_media_entries'] == 28 and context['unique_native_artwork_digests'] == 26
        for artwork in context['original_source_appendix_all_media']:
            raw = original.read(artwork['native_DOCX_member'])
            assert digest(raw) == artwork['sha256']
            with Image.open(io.BytesIO(raw)) as image:
                assert image.size == (artwork['width'], artwork['height'])
                assert digest(image.tobytes()) == artwork['decoded_channel_sha256']
        doc = ET.fromstring(original.read('word/document.xml'))
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        text = [''.join(t.text or '' for t in p.findall('.//w:t', ns)) for p in doc.findall('.//w:p', ns)]
        assert all(p in text for p in context['original_appendix_credit_paragraphs'])
    assert context['complete_native_DOCX_layout_vectors_text_labels_and_media_preserved']
    assert not context['source_case_registration_between_TRACK_TBI_and_CENTER_TBI_established']
    assert not context['native_DICOM_segmentation_or_mesh_supplied']


@pytest.mark.parametrize('mutation', ['missing_figure', 'MRI_borrowed_as_CT', 'invented_DICOM', 'invented_coverage', 'wrong_license', 'wrong_digest'])
def test_contradictory_or_invented_source_claims_fail_before_integration(proposal, mutation):
    changed = copy.deepcopy(proposal)
    if mutation == 'missing_figure':
        changed['images'].pop()
    elif mutation == 'MRI_borrowed_as_CT':
        row = next(r for r in changed['images'] if r['figure_identifier'] == '2-panel-2')
        row['source_context']['panel_types']['L4'] = 'CT'
    elif mutation == 'invented_DICOM':
        changed['images'][1]['source_context']['native_DICOM_or_volumetric_stack_supplied'] = True
    elif mutation == 'invented_coverage':
        changed['assets'][0]['requirement_coverage'] = {'brain': ['complete']}
    elif mutation == 'wrong_license':
        changed['images'][0]['license'] = 'CC BY-NC 4.0'
    else:
        changed['images'][0]['sha256'] = '0' * 64
    with pytest.raises(ValueError):
        packaging.validate_proposal(changed)
