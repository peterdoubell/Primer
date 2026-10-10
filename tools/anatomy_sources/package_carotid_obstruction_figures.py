#!/usr/bin/env python3
"""Preserve acquired carotid figures; distinct cases and conceptual walls never become native anatomy."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
INV = 'ra.carotid-obstruction'
PREFIX = 'open-carotid-obstruction-'
SELECTION = [('PMC7160198', 'Fig2', 2, 21, 'near-2020-001.jpg'),
             ('PMC12866240', 'fig1-23969873251355158', 2, 11, 'near-2026-001.jpg')]

def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(path, value): path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def package(source):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
    from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
    from tools.check_static_raster_inventory import inventory
    proof_dir = ROOT / 'docs/carotid-obstruction-source-review'
    proof_dir.mkdir(exist_ok=True)
    proof_path = proof_dir / 'published-source-preservation.json'
    rows, assets, articles, records = [], [], [], []
    for pmc, fig_id, page, object_id, master in SELECTION:
        meta_raw = (source / (pmc + '.1.json')).read_bytes(); meta = json.loads(meta_raw)
        if meta['pmcid'] != pmc or meta['is_retracted'] or meta['license_code'] != 'CC BY':
            raise ValueError('Source identity, retraction or grant changed')
        http = lambda url: url.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
        xml = download_verified(http(meta['xml_url']), source / (pmc + '.1.xml'))
        pdf = download_verified(http(meta['pdf_url']), source / (pmc + '.1.pdf'))
        tree = ET.fromstring(xml); permissions = tree.find('.//article-meta/permissions')
        if 'creativecommons.org/licenses/by/4.0/' not in ET.tostring(permissions, encoding='unicode'):
            raise ValueError('Explicit original CC BY4.0 grant missing')
        figure = tree.find('.//fig[@id="' + fig_id + '"]')
        caption = ' '.join(' '.join(figure.find('caption').itertext()).split())
        if figure.find('attrib') is not None or figure.find('permissions') is not None or any(
                word in caption.lower() for word in ['reproduced', 'reprinted', 'courtesy', 'adapted from']):
            raise ValueError('Separate figure rights require review')
        reader = PdfReader(source / (pmc + '.1.pdf')); obj = reader.get_object(IndirectObject(object_id, 0, reader))
        if object_id not in {r.idnum for r in reader.pages[page-1]['/Resources']['/XObject'].values()}:
            raise ValueError('Original image/page identity differs')
        raw = (source / 'pdf-masters' / master).read_bytes()
        if str(obj['/Filter']) != '/DCTDecode' or obj.get('/Decode') is not None or obj['/BitsPerComponent'] != 8 or raw != obj._data:
            raise ValueError('Complete original JPEG stream was changed')
        with Image.open(source / 'pdf-masters' / master) as image:
            image.load(); dimensions = [image.width, image.height]
            if image.mode != 'L' or dimensions != [obj['/Width'], obj['/Height']]:
                raise ValueError('Original grayscale samples/dimensions differ')
            pixel_sha = sha(image.tobytes())
        authors = ', '.join(' '.join([n.findtext('given-names',''), n.findtext('surname','')])
                            for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name'))
        url = 'https://pmc.ncbi.nlm.nih.gov/articles/' + pmc + '/'
        number = 2 if pmc == 'PMC7160198' else 1; ident = PREFIX + pmc.lower() + '-fig' + str(number)
        local = 'web/reference-media/radiology-open/carotid-obstruction-' + pmc.lower() + '-fig' + str(number) + '.jpg'
        (ROOT / local).write_bytes(raw)
        panels = list('abc') if pmc == 'PMC7160198' else list('ab')
        groups = {'one_source_case': panels} if pmc == 'PMC7160198' else {'full_collapse_case': ['a'], 'without_full_collapse_case': ['b']}
        title = ('Published distal ICA reduction without full collapse' if pmc == 'PMC7160198'
                 else 'Separate left-sided near-occlusion cases with and without full collapse')
        context = {'setting': 'in_vivo', 'laterality': 'left', 'population': {'life_stage': 'adult' if pmc == 'PMC7160198' else 'not_reported'},
                   'extent': 'local', 'depicted_state': 'source_carotid_near_occlusion_example',
                   'selected_panels': panels, 'panel_types': dict.fromkeys(panels, 'CT'),
                   'source_case_groups': groups, 'different_panels_assumed_same_patient': pmc == 'PMC7160198',
                   'different_figures_assumed_same_patient': False, 'source_panels_independently_registered': False,
                   'native_acquisition_arrays_included': False, 'independent_calibrated_measurements_verified': False,
                   'biological_3d_model_created_from_artwork': False}
        if pmc == 'PMC7160198':
            context['source_reported_diameters_mm'] = {'left_distal_ICA': 2.8, 'right_distal_ICA': 3.9, 'left_ECA': 2.7}
        limits = ('Complete original published CTA views and annotations, not the complete acquired series. '
                  'Near-occlusion interpretation and any diameters are attributed publication context, not new independent diagnosis or calibrated pixel measurements. '
                  'Panels/cases are not registered to the native CT reference, curated 3D reference or current examination. '
                  'The narrowed site or proximal ICA is not fully in every depicted plane; apparent distal calibre alone cannot establish the diagnosis. '
                  'No native wall-layer, every plaque component, complete branch, contrast timing, flow measurement or clinical/anatomical approval is supplied.')
        credit = authors + '. ' + meta['title'] + '. DOI ' + meta['doi'] + '. Figure ' + str(number) + '. CC BY4.0. Complete original JPEG stream and grayscale samples preserved; no crop, resampling, enhancement or annotation change.'
        row = {'id': ident, 'kind': 'clinical-image', 'modality': 'CT', 'figure_number': number,
               'src': '/app/' + local.removeprefix('web/'), 'sha256': sha(raw), 'width': dimensions[0], 'height': dimensions[1],
               'source_url': url, 'figure_url': url + '#' + fig_id, 'asset_source_url': http(meta['pdf_url']),
               'clinical_panels': panels, 'source_context': context, 'image_state': context['depicted_state'],
               'caption': title + '. Original source views and annotations retained.', 'alt': title + '; complete original ' + ', '.join(panels) + ' panels.',
               'source_caption_full': caption, 'limits': limits,
               'structures_visible': ['Source-displayed distal ICA, comparison ICA/ECA and supplied stenosis views; complete anatomy unapproved'],
               'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/', 'attribution': credit,
               'rights_reviewed_on': '2026-10-10',
               'rights_review': 'Original CC BY4.0 grants and complete selected captions reviewed; publisher XML/PDF MD5 and original PDF JPEG streams verified. The conflicting 2020 Figure1 caption is held; no pixel changes or inferred anatomical approval.'}
        rows.append(row)
        records.append({'id': ident, 'pmcid': pmc, 'figure_id': fig_id, 'original_PDF_page': page,
                        'original_PDF_object': object_id, 'sha256': sha(raw), 'decoded_pixel_sha256': pixel_sha,
                        'dimensions': dimensions, 'original_JPEG_stream_equal_to_Poppler_extraction': True,
                        'complete_master_visually_inspected': True, 'original_caption': caption})
        articles.append({'pmcid': pmc, 'doi': meta['doi'], 'authors': authors, 'title': meta['title'],
                         'original_XML_sha256': sha(xml), 'original_PDF_sha256': sha(pdf), 'metadata_sha256': sha(meta_raw),
                         'publisher_XML_PDF_md5_verified': True, 'permissions_xml': ET.tostring(permissions, encoding='unicode')})
        (proof_dir / (pmc + '-metadata.json')).write_bytes(meta_raw)
        assets.append({'id': ident, 'kind': 'clinical_image', 'name': title, 'local_path': local, 'sha256': sha(raw),
                       'investigation_ids': [INV], 'structure_ids': [], 'requirement_coverage': {}, 'modality': 'CT',
                       'source_context': context, 'source': {'url': url, 'license': {'name': 'CC BY 4.0',
                       'url': row['license_url'], 'commercial_use': True, 'redistribution': True, 'review_status': 'verified',
                       'reviewed_at': '2026-10-10', 'evidence_path': str(proof_path.relative_to(ROOT)), 'attribution': credit}},
                       'visual_review': {'status': 'source_checked', 'sha256': sha(raw), 'reviewed_at': '2026-10-10',
                                         'evidence_path': str(proof_path.relative_to(ROOT))},
                       'anatomical_review': {'status': 'pending', 'reason': limits}})
    data_path = ROOT / 'data/radiology/radiology-open-images.json'; data = json.loads(data_path.read_text())
    existing = {row['figure_number']: row for row in data['ra.mri-neck-spaces']}
    reuse = []
    for number in [11,12,13,14,15,16]:
        original = existing[number]; row = copy.deepcopy(original)
        row['id'] = PREFIX + 'neck-spaces-fig' + str(number)
        row['additional_reporting_use'] = 'Arterial dissection, pseudoaneurysm or source MRA vessel morphology; source diagnosis and functions remain attributed, not independently inferred.'
        row['source_context']['borrowed_case_is_current_patient'] = False
        if number == 16:
            row['source_context']['panel_processing'] = {'full_figure': 'Published MRA display; native sequence, flow calibration and full acquisition unavailable'}
        rows.append(row)
        original_asset = next(a for a in json.loads((ROOT / 'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if a['id'] == original['id'])
        asset = copy.deepcopy(original_asset); asset.update(id=row['id'], investigation_ids=[INV], structure_ids=[], requirement_coverage={})
        asset['source_context'] = row['source_context']; assets.append(asset)
        reuse.append({'new_binding_id': row['id'], 'original_binding_id': original['id'], 'same_source_file': row['src'],
                     'sha256': row['sha256'], 'case_modality_and_caption_preserved': True, 'reporting_coverage_granted': False})
    save(proof_path, {'articles': articles, 'figures': records, 'reused_original_sources': reuse,
                     'held': [{'pmcid': 'PMC7160198', 'figure': 1,
                               'reason': 'Caption comparative wording conflicts with the illustrated full-collapse example; no unverified correction or measurement is adopted.'}],
                     'clinical_approval': False, 'complete_reporting_anatomy_approved': False, 'source_pixels_modified': False})
    for a in assets:
        if a['source']['license']['evidence_path'] == str(proof_path.relative_to(ROOT)):
            a['source']['license']['evidence_sha256'] = sha(proof_path.read_bytes())
    data[INV] = rows; save(data_path, data)
    append_evidence(ROOT / 'data/radiology/radiology-asset-evidence.json', assets, prefix=PREFIX)
    save(ROOT / 'data/radiology/radiology-static-rasters.json', inventory())
    print('Eight whole licensed source figures bound; separate cases/roles retained, no anatomical approval.')

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--source-root', type=Path, required=True)
    package(p.parse_args().source_root)
