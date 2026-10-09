#!/usr/bin/env python3
"""Preserve Jansen2019's complete tissue figures, never reconstruct geometry from artwork."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PMCID = 'PMC6440143'
DOI = '10.1186/s13000-019-0803-7'
INV = 'ra.mri-bladder'
PREFIX = 'bladder-histology-jansen-2019-fig'
DATE = '2026-10-09'
URL = 'https://link.springer.com/article/' + DOI
LICENSE = 'https://creativecommons.org/licenses/by/4.0/'
SELECTED = {1: (3, 44, 0), 4: (4, 62, 3), 6: (5, 68, 5)}
LIMITS = ('Formalin fixation, paraffin embedding, sectioning, mounting and staining alter the tissue. '
          'The authors aligned sections by rigid, affine and nonrigid B-spline transformations; registration was assessed qualitatively. '
          'Excluded sections could be replaced by duplicate neighbours, and only portions of tumour blocks were sectioned. '
          'Whole-slide sampling reported as 0.5 micrometres/pixel does not describe the resolution of these published bitmaps. '
          'Native slide arrays, masks and aligned volumes are not publicly supplied. No whole-wall or microscopic invasion validation, '
          'native 3D geometry, calibrated independent tissue measurement, MRI correspondence, current diagnosis or VI-RADS category is established.')
CAPTIONS = {
    1: 'Original Figure 1: right, digitized en-bloc tissue with the authors’ tumour outlines in red and muscularis propria in orange; left, the annotation workstation photograph. The specimen number is not stated. Labels are publication evidence, not a new pathology reading.',
    4: 'Original Figure 4: source specimen 1, reported papillary low-grade (grade 2) Ta tumour with muscularis propria present. Panels a/b are flat histology volume-rendering/detail displays; c shows the aligned section stack. Original 1000, 250 and 500 micrometre scale bars remain. This is processed histology, not an acquired 3D model.',
    6: 'Original Figure 6: the same source specimen 1 as Figure 4. The published segmented histology rendering shows tumour above and muscularis propria below; intervening tissue is deliberately blurred. The faded tissue is not absent anatomy, and this separated Ta example does not demonstrate muscle invasion.',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def package(source):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    from primer.radiology_catalog import _validate_source_panel_roles
    from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
    from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
    from tools.check_static_raster_inventory import inventory

    metadata_raw = (source / (PMCID + '.1.json')).read_bytes()
    metadata = json.loads(metadata_raw)
    if (metadata['pmcid'] != PMCID or metadata['doi'] != DOI or metadata['is_retracted'] is not False
            or metadata.get('license_code') != 'CC BY'):
        raise ValueError('Wrong source identity or retraction state')
    http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    xml = download_verified(http(metadata['xml_url']), source / (PMCID + '.1.xml'))
    pdf = download_verified(http(metadata['pdf_url']), source / (PMCID + '.1.pdf'))
    tree = ET.fromstring(xml)
    permissions = tree.find('.//article-meta/permissions')
    if permissions is None or LICENSE not in ET.tostring(permissions, encoding='unicode'):
        raise ValueError('Original CC BY4 grant missing')
    figures = {n: tree.find('.//fig[@id="Fig' + str(n) + '"]') for n in SELECTED}
    for figure in figures.values():
        if figure is None or figure.find('attrib') is not None or figure.find('permissions') is not None:
            raise ValueError('Unreviewed source figure or separate credit')
    visual = json.loads((source / 'visual-review.json').read_text())
    if not visual['all_selected_masters_and_original_pages_inspected'] or visual['native_slides_available']:
        raise ValueError('Complete visual source review required')
    review_root = ROOT / 'docs/bladder-histology-jansen-source-review'
    review_root.mkdir(parents=True, exist_ok=True)
    (review_root / 'original-article.xml').write_bytes(xml)
    (review_root / 'original-article.pdf').write_bytes(pdf)
    (review_root / 'publisher-metadata.json').write_bytes(metadata_raw)
    (review_root / 'visual-review.json').write_text(json.dumps(visual, indent=2) + '\n')
    authors = ', '.join(' '.join([name.findtext('given-names', ''), name.findtext('surname', '')])
                        for name in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name'))
    reader = PdfReader(io.BytesIO(pdf))
    rows, proofs, assets = [], [], []
    for number, (page, object_id, poppler_index) in SELECTED.items():
        figure = figures[number]
        original_caption = ' '.join(' '.join(figure.find('caption').itertext()).split())
        filename = figure.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        urls = [u for u in metadata['media_urls'] if u.split('?')[0].endswith('/' + filename)]
        if len(urls) != 1:
            raise ValueError('Ambiguous original media')
        media = download_verified(http(urls[0]), source / filename)
        obj = reader.get_object(IndirectObject(object_id, 0, reader))
        if object_id not in {v.idnum for v in reader.pages[page - 1]['/Resources']['/XObject'].values()}:
            raise ValueError('Original figure page binding changed')
        if obj.get('/Decode') is not None or obj['/BitsPerComponent'] != 8 or str(obj['/ColorSpace'][0]) != '/ICCBased':
            raise ValueError('Unreviewed source sample interpretation')
        profile = obj['/ColorSpace'][1].get_object()
        if profile['/N'] != 3:
            raise ValueError('Original RGB ICC interpretation required')
        icc = profile.get_data()
        if str(obj['/Filter']) == '/DCTDecode':
            original = Image.open(io.BytesIO(obj._data)); original.load()
        elif str(obj['/Filter']) == '/FlateDecode':
            original = Image.frombytes('RGB', (obj['/Width'], obj['/Height']), obj.get_data())
        else:
            raise ValueError('Unreviewed original PDF image filter')
        master_path = source / f'fig{number}-original-PDF-master.png'
        master_raw = master_path.read_bytes()
        inspected = next(r for r in visual['figures'] if r['figure_number'] == number)
        if sha(master_raw) != inspected['sha256'] or not inspected['all_original_panels_and_pdf_binding_visually_inspected']:
            raise ValueError('Inspected source master changed')
        with Image.open(master_path) as display, Image.open(source / f'poppler-image-{poppler_index:03d}.png') as independent:
            display.load(); independent.load()
            if (display.mode != 'RGB' or display.size != original.size or display.tobytes() != original.tobytes()
                    or display.info.get('icc_profile') != icc or independent.tobytes() != original.tobytes()):
                raise ValueError('Original PDF samples, independent Poppler readback or ICC differ')
        with Image.open(io.BytesIO(media)) as small:
            repository_dimensions = list(small.size)
        local = f'web/reference-media/radiology-open/{PREFIX}{number}.png'
        (ROOT / local).write_bytes(master_raw)
        context = {
            'setting': 'ex_vivo', 'laterality': 'unknown', 'population': {'life_stage': 'unknown', 'age_not_supplied': True, 'sex_not_supplied': True},
            'extent': 'local', 'depicted_state': 'source_human_en_bloc_bladder_histology',
            'selected_panels': ['right_tissue'] if number == 1 else list('abc') if number == 4 else ['full_figure'],
            'panel_types': {'left_workstation': 'Clinical photograph', 'right_tissue': 'Histology'} if number == 1 else dict.fromkeys('abc', 'Histology') if number == 4 else {'full_figure': 'Histology'},
            'panel_processing': {'left_workstation': 'workstation photograph', 'right_tissue': 'digitized tissue with original manual outlines'} if number == 1 else {'a': 'flat histology volume rendering', 'b': 'rendered histology detail', 'c': 'aligned histology stack view'} if number == 4 else {'full_figure': 'segmented histology rendering with intentionally blurred intervening tissue'},
            'source_specimen_id': 'not_stated' if number == 1 else 'Jansen2019_specimen1',
            'source_reported_pathology': None if number == 1 else {'T_stage': 'Ta', 'grade': 'low grade (grade 2)'},
            'source_case_groups': {'figure1_specimen_not_numbered': ['right_tissue']} if number == 1 else {'Jansen2019_specimen1': list('abc') if number == 4 else ['full_figure']},
            'figure1_assumed_same_specimen_as_figures4_6': False,
            'source_native_registration_verified': False, 'source_full_fine_anatomy_approved': False,
            'source_current_diagnosis_or_histology_inferred': False, 'flat_rendering_is_native_3d_geometry': False,
            'original_slide_or_volume_arrays_supplied': False,
        }
        if number != 4:
            context['panel_identifier_scheme'] = 'descriptive_source_positions'
        attribution = (authors + '. ' + metadata['title'] + '. Diagnostic Pathology14,25(2019). DOI' + DOI + '. Figure' + str(number) +
                       '. CC BY4.0. Original complete PDF image samples and embedded RGB ICC profile retained in lossless PNG, with no crop, resize, enhancement or relabelling. No endorsement implied.')
        row = {'id': PREFIX + str(number), 'kind': 'clinical-image', 'modality': 'Histology', 'figure_number': number,
               'source_tissue_evidence': True,
               'src': '/app/' + local.removeprefix('web/'), 'sha256': sha(master_raw), 'width': original.width, 'height': original.height,
               'source_url': URL, 'figure_url': URL + '/figures/' + str(number), 'asset_source_url': http(metadata['pdf_url']),
               'clinical_panels': context['selected_panels'], 'source_context': context, 'image_state': context['depicted_state'],
               'source_caption_full': original_caption, 'caption': CAPTIONS[number], 'alt': CAPTIONS[number], 'limits': LIMITS,
               'structures_visible': ['Source-local human tumour and muscularis propria relationship; complete boundaries unapproved'],
               'license': 'CC BY 4.0', 'license_url': LICENSE, 'attribution': attribution, 'source_background': 'white',
               'rights_reviewed_on': DATE, 'rights_review': 'Full original XML grant, PDF and figure captions reviewed; no separate figure restriction or credit. Original NLM publisher MD5s verified; original PDF samples and RGB ICC preserved.'}
        if number != 4:
            row['panel_identifier_scheme'] = 'descriptive_source_positions'
        if number == 1:
            row['ancillary_panels'] = [{'kind': 'Clinical photograph', 'panels': ['left_workstation'],
                'structures_visible': ['Original annotation workstation and tissue display'],
                'limits': 'Hardware photograph only; not a second native histological slide, tissue-boundary measurement or patient acquisition.'}]
        _validate_source_panel_roles(row); rows.append(row)
        proofs.append({'figure_number': number, 'pdf_page': page, 'pdf_object_id': object_id, 'pdf_filter': str(obj['/Filter']),
                       'pdf_color_space': 'ICCBased RGB', 'width': original.width, 'height': original.height, 'sha256': sha(master_raw),
                       'decoded_pixel_sha256': sha(original.tobytes()), 'original_ICC_sha256': sha(icc),
                       'repository_dimensions': repository_dimensions, 'repository_media_sha256': sha(media),
                       'publisher_media_md5_verified': True, 'independent_poppler_pixels_exact': True,
                       'source_caption_full': original_caption, 'source_pixels_changed': False, 'all_panels_preserved': True})
        assets.append({'id': row['id'], 'kind': 'clinical_image', 'name': CAPTIONS[number], 'local_path': local,
                       'sha256': row['sha256'], 'modality': 'Histology', 'investigation_ids': [INV], 'structure_ids': [],
                       'requirement_coverage': {}, 'source_context': context,
                       'source': {'url': URL, 'figure_url': row['figure_url'], 'asset_url': row['asset_source_url'], 'license': {
                           'name': 'CC BY 4.0', 'url': LICENSE, 'commercial_use': True, 'redistribution': True, 'review_status': 'verified',
                           'evidence_path': str((review_root / 'original-source-review.json').relative_to(ROOT)), 'attribution': attribution, 'reviewed_at': DATE}},
                       'pixel_provenance': {'source_pixels_changed': False, 'decoded_pixel_sha256': sha(original.tobytes()),
                           'original_ICC_sha256': sha(icc), 'pdf_object_id': object_id, 'independent_poppler_pixels_exact': True,
                           'highest_resolution_acquired_master_verified': True, 'whole_slide_resolution_available': False},
                       'anatomical_review': {'status': 'pending', 'reason': LIMITS}})
    proof = {'pmcid': PMCID, 'doi': DOI, 'original_XML_sha256': sha(xml), 'original_PDF_sha256': sha(pdf),
             'metadata_sha256': sha(metadata_raw), 'publisher_xml_pdf_md5_verified': True,
             'original_article_license': 'CC BY 4.0', 'license_url': LICENSE,
             'permissions_xml': ET.tostring(permissions, encoding='unicode'), 'figures': proofs,
             'native_slide_data_publicly_available': False, 'source_native_3d_created': False,
             'source_limits': LIMITS, 'clinical_approval': False, 'complete_reporting_anatomy_approved': False}
    proof_path = review_root / 'original-source-review.json'
    proof_path.write_text(json.dumps(proof, indent=2, ensure_ascii=False) + '\n')
    for asset in assets:
        asset['source']['license']['evidence_sha256'] = sha(proof_path.read_bytes())
    path = ROOT / 'data/radiology/radiology-open-images.json'; data = json.loads(path.read_text())
    data[INV] = [r for r in data.get(INV, []) if not r['id'].startswith(PREFIX)] + rows
    # Restore the already reviewed original tissue panel under the same narrow
    # delivery rule. Its masks remain ancillary, and its pixels/approval do not change.
    niazi = next(r for r in data[INV] if r['id'] == 'bladder-histology-niazi-2020-fig1')
    if (niazi['sha256'] != '00ce9cfef46fc35e0da612787d63738eaf859b7ab21468130aaef5157609cb60'
            or niazi['modality'] != 'Histology' or niazi['clinical_panels'] != ['a']
            or niazi['source_context']['setting'] != 'ex_vivo'
            or niazi['source_context']['panel_types'] != {
                'a': 'Histology', 'b': 'Segmentation mask', 'c': 'Segmentation mask', 'd': 'Masked histology'}):
        raise ValueError('Reviewed Niazi original tissue/processing roles changed')
    niazi['source_tissue_evidence'] = True
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    append_evidence(ROOT / 'data/radiology/radiology-asset-evidence.json', assets, prefix=PREFIX)
    (ROOT / 'data/radiology/radiology-static-rasters.json').write_text(json.dumps(inventory(), indent=2) + '\n')
    print('Three complete original human bladder tissue figures preserved; no anatomical or 3D approval granted.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    package(parser.parse_args().source_root)
