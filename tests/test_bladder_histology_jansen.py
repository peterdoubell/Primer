"""Original tissue evidence must preserve specimen and processed-rendering boundaries."""
import copy
import hashlib
import io
import json
from pathlib import Path

from PIL import Image
import pytest

from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve, _validate_source_panel_roles, reporting_image
from tools.check_msk_fidelity import inspect_binding, requirements_for

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bladder-histology-jansen-source-review'
PREFIX = 'bladder-histology-jansen-2019-fig'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rows():
    return {r['figure_number']: r for r in detail(Curriculum(), resolve('ra.mri-bladder'))['radiology_reference']['structure_atlas']
            if r['id'].startswith(PREFIX)}


def test_complete_original_rasters_have_native_pixels_profile_and_pdf_provenance():
    proof = json.loads((REVIEW / 'original-source-review.json').read_text())
    assert proof['original_article_license'] == 'CC BY 4.0'
    assert proof['publisher_xml_pdf_md5_verified']
    assert sha((REVIEW / 'original-article.xml').read_bytes()) == proof['original_XML_sha256']
    assert sha((REVIEW / 'original-article.pdf').read_bytes()) == proof['original_PDF_sha256']
    assert not proof['native_slide_data_publicly_available'] and not proof['source_native_3d_created']
    assert not proof['clinical_approval'] and not proof['complete_reporting_anatomy_approved']
    figures = rows()
    assert set(figures) == {1, 4, 6}
    assert [(r['figure_number'], r['pdf_page'], r['pdf_object_id']) for r in proof['figures']] == [(1, 3, 44), (4, 4, 62), (6, 5, 68)]
    for source in proof['figures']:
        figure = figures[source['figure_number']]
        path = ROOT / 'web' / figure['src'].removeprefix('/app/')
        assert sha(path.read_bytes()) == source['sha256'] == figure['sha256']
        with Image.open(path) as image:
            image.load()
            assert image.mode == 'RGB' and image.size == (source['width'], source['height'])
            assert sha(image.tobytes()) == source['decoded_pixel_sha256']
            assert sha(image.info['icc_profile']) == source['original_ICC_sha256']
        assert source['independent_poppler_pixels_exact'] and source['all_panels_preserved']
        assert not source['source_pixels_changed']


def test_retained_pdf_objects_decode_to_every_delivered_sample():
    pypdf = pytest.importorskip('pypdf')
    from pypdf.generic import IndirectObject
    reader = pypdf.PdfReader(REVIEW / 'original-article.pdf')
    for source in json.loads((REVIEW / 'original-source-review.json').read_text())['figures']:
        obj = reader.get_object(IndirectObject(source['pdf_object_id'], 0, reader))
        image = (Image.open(io.BytesIO(obj._data)) if str(obj['/Filter']) == '/DCTDecode' else
                 Image.frombytes('RGB', (obj['/Width'], obj['/Height']), obj.get_data()))
        image.load()
        assert sha(image.tobytes()) == source['decoded_pixel_sha256']
        assert sha(obj['/ColorSpace'][1].get_object().get_data()) == source['original_ICC_sha256']


def test_workstation_and_processed_tissue_roles_and_specimen_identity_remain_distinct():
    figures = rows()
    for figure in figures.values():
        _validate_source_panel_roles(figure)
        context = figure['source_context']
        assert figure['modality'] == 'Histology' and context['setting'] == 'ex_vivo'
        assert not context['original_slide_or_volume_arrays_supplied']
        assert not context['flat_rendering_is_native_3d_geometry']
        assert not context['source_native_registration_verified']
        assert not context['source_full_fine_anatomy_approved']
    assert figures[1]['clinical_panels'] == ['right_tissue']
    assert figures[1]['ancillary_panels'][0]['kind'] == 'Clinical photograph'
    assert figures[1]['source_context']['source_specimen_id'] == 'not_stated'
    assert figures[4]['source_context']['source_specimen_id'] == figures[6]['source_context']['source_specimen_id'] == 'Jansen2019_specimen1'
    assert figures[4]['source_context']['source_reported_pathology']['T_stage'] == 'Ta'
    assert 'blurred' in figures[6]['caption'] and 'not absent anatomy' in figures[6]['caption']
    wrong = copy.deepcopy(figures[1]); wrong['source_context']['panel_types']['left_workstation'] = 'Histology'
    with pytest.raises(ValueError, match='ancillary panel roles'):
        _validate_source_panel_roles(wrong)
    assert reporting_image(figures[1])
    wrong = copy.deepcopy(figures[1]); wrong['source_tissue_evidence'] = False
    assert not reporting_image(wrong)
    wrong = copy.deepcopy(figures[1]); wrong['source_context']['setting'] = 'in_vivo'
    assert not reporting_image(wrong)


def test_histology_does_not_approve_mri_detrusor_or_complete_layer_coverage():
    requirements = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    bladder = next(r for r in requirements['investigations'] if r['investigation_id'] == 'ra.mri-bladder')
    leaves = {r['id']: r for r in requirements_for(bladder)}
    assets = json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    selected = [a for a in assets if a['id'].startswith(PREFIX)]
    assert len(selected) == 3
    for asset in selected:
        assert asset['structure_ids'] == [] and asset['requirement_coverage'] == {}
        assert asset['anatomical_review']['status'] == 'pending'
        assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding(asset, leaves['bladder.detrusor.source_resolved_extent'])
        rights = asset['source']['license']
        assert rights['commercial_use'] and rights['redistribution']
        assert sha((ROOT / rights['evidence_path']).read_bytes()) == rights['evidence_sha256']


def test_original_niazi_tissue_is_delivered_without_borrowing_processed_mask_coverage():
    figures = detail(Curriculum(), resolve('ra.mri-bladder'))['radiology_reference']['structure_atlas']
    assert len(figures) == 4
    niazi = next(r for r in figures if r['id'] == 'bladder-histology-niazi-2020-fig1')
    assert niazi['source_tissue_evidence'] is True and niazi['clinical_panels'] == ['a']
    assert niazi['source_context']['panel_types'] == {
        'a': 'Histology', 'b': 'Segmentation mask', 'c': 'Segmentation mask', 'd': 'Masked histology'}
    assert {p for r in niazi['ancillary_panels'] for p in r['panels']} == {'b', 'c', 'd'}
    assert sha((ROOT / 'web' / niazi['src'].removeprefix('/app/')).read_bytes()) == '00ce9cfef46fc35e0da612787d63738eaf859b7ab21468130aaef5157609cb60'
    assert not niazi['source_context']['source_full_fine_anatomy_approved']
    assert not niazi['source_context']['source_native_registration_verified']
