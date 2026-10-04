"""Biliary projection examples retain original pixels and cannot prove clinical completeness."""
import hashlib
import json
from pathlib import Path
from PIL import Image

from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_msk_fidelity import inspect_binding, requirements_for

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/biliary-published-source-review'


def test_original_biliary_images_preserve_each_encoded_or_decoded_pdf_pixel():
    source = json.loads((REVIEW / 'original-source-review.json').read_text())
    packaged = json.loads((REVIEW / 'packaged-source-images.json').read_text())
    assert len(source['figures']) == len(packaged['figures']) == 6
    assert all(a['license'] == 'CC BY 4.0' and a['publisher_xml_pdf_md5_verified'] for a in source['articles'])
    assert sum(r['acquisition'] == 'original_pdf_dct_stream_byte_identical' for r in source['figures']) == 5
    for row in packaged['figures']:
        s = next(x for x in source['figures'] if (x['pmcid'], x['figure_number']) == (row['pmcid'], row['figure_number']))
        path = ROOT / row['local_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == s['sha256'] == row['sha256']
        with Image.open(path) as image:
            assert list(image.size) == [s['width'], s['height']]
            assert hashlib.sha256(image.tobytes()).hexdigest() == s['decoded_pixel_sha256']
        assert s['publisher_media_md5_verified'] is True
        assert s['original_encoded_stream_or_decoded_pixel_readback_verified'] is True
        assert s['source_pixels_changed'] is False
    assert source['separately_credited_diagrams_excluded']['figures'] == [2, 3, 4]
    assert source['caroli_figure10_sequence_panel_correspondence_unverified'] is True
    assert {r['pmcid'] for r in source['rights_holds']} == {'PMC3292642', 'PMC9116710', 'PMC11419767'}


def test_whole_unlettered_projection_and_separate_modalities_are_not_invented_panels():
    ref = detail(Curriculum(), resolve('ra.biliary-duct-pathology'))['radiology_reference']
    images = {r['id']: r for r in ref['structure_atlas'] if r['id'].startswith('open-biliary-')}
    assert len(images) == 6
    single = images['open-biliary-pmc13476307-fig1']
    assert 'clinical_panels' not in single
    assert 'selected_panels' not in single['source_context']
    assert single['source_context']['depicted_state'] == 'normal_anatomy'
    mixed = images['open-biliary-pmc9287528-fig9']
    assert 'panel-correspondence concern' in images['open-biliary-pmc9287528-fig10']['caption']
    assert mixed['clinical_panels'] == ['b', 'd']
    assert {(a['kind'], tuple(a['panels'])) for a in mixed['ancillary_panels']} == {('CT', ('c',)), ('Ultrasound', ('a',))}
    data = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    item = next(i for i in data['investigations'] if i['investigation_id'] == 'ra.biliary-duct-pathology')
    leaf = next(r for r in requirements_for(item) if r['id'] == 'biliary.material.each_stone')
    assert 'source_context_purpose_mismatch' in inspect_binding({'kind': 'clinical_image', 'modality': 'MRI',
                                                              'source_context': single['source_context']}, leaf)


def test_licensed_biliary_candidates_have_no_structure_or_clinical_approval():
    data = json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())
    rows = [r for r in data['assets'] if r['id'].startswith('open-biliary-')]
    assert len(rows) == 6
    for row in rows:
        assert row['structure_ids'] == [] and row['requirement_coverage'] == {}
        assert row['anatomical_review']['status'] == 'pending'
        license = row['source']['license']
        assert license['commercial_use'] and license['redistribution']
        assert hashlib.sha256((ROOT / license['evidence_path']).read_bytes()).hexdigest() == license['evidence_sha256']
