#!/usr/bin/env python3
"""Preserve original operative CT figures, including a source caption/plane disagreement."""
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[2]
IDENT = 'ra.mri-sinuses'
PREFIX = 'open-sinonasal-operative-pmc6472854-fig'
OUT = ROOT/'docs/sinonasal-operative-source-review'
SOURCE = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC6472854/'
TITLES = ['Uncinate attachment at orbital wall', 'Different bilateral uncinate attachments',
          'Uncinate attachment at turbinate/skull-base junction', 'Uncinate attachment at middle turbinate',
          'Maxillary atelectasis and uncinate apposition', 'Source olfactory-fossa depth example',
          'Olfactory-fossa asymmetry', 'Ethmoidal canal region; caption-plane disagreement',
          'Source orbital-wall defect example', 'Infraorbital ethmoid cells',
          'Frontal recess cell and agger nasi relation', 'Interfrontal cell',
          'Source Onodi cell and optic relation', 'Pterygoid recess and foraminal relations',
          'Sphenoid sellar pneumatization', 'Middle turbinate pneumatization',
          'Paradoxical turbinate and septal spur']
COMMON = (' Complete original publisher CT JPEG and annotations retained. This is a selected source-local CT example, '
          'not MRI tissue characterization or a complete native series. Effective resolution, thin-wall integrity, '
          'calibrated measurements, drainage function, all neurovascular courses and complete 3D anatomy are not '
          'independently established. Source variant/defect labels are not the current reader patient or clinical approval.')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def package(source_root):
    OUT.mkdir(parents=True, exist_ok=True)
    archive = OUT/'packaged-source-images.json'
    replaced = json.loads(archive.read_text())['replaced_investigation_images'] if archive.exists() else detail(Curriculum(), resolve(IDENT))['radiology_reference']['key_images']
    metadata = source_root/'PMC6472854.1.json'
    m = json.loads(metadata.read_text())
    if m['pmcid'] != 'PMC6472854' or m['is_retracted'] is not False:
        raise ValueError('Source identity/retraction differs')
    http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    xml = download_verified(http(m['xml_url']), source_root/'PMC6472854.1.xml')
    tree = E.fromstring(xml)
    permission = tree.find('.//article-meta/permissions')
    license_name, license_url = exact_license(permission)
    if license_name != 'CC BY 4.0':
        raise ValueError('Selected source grant differs')
    authors = [' '.join([n.findtext('given-names', ''), n.findtext('surname', '')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    rows, facts, locals_ = [], [], []
    for number, title in enumerate(TITLES, 1):
        figure = tree.find('.//fig[@id="f'+str(number)+'"]')
        caption = ' '.join(figure.find('caption').itertext())
        if figure.find('attrib') is not None or figure.find('permissions') is not None or any(w in caption.lower() for w in ['courtesy', 'reproduced', 'reprinted', 'adapted', 'modified from']):
            raise ValueError('Separate source credit requires review')
        filename = figure.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        pointers = [u for u in m['media_urls'] if '/'+filename+'?' in u]
        if len(pointers) != 1:
            raise ValueError('Original figure pointer ambiguous')
        url = http(pointers[0])
        raw = download_verified(url, source_root/filename)
        with Image.open(source_root/filename) as image:
            image.load()
            fact = {'figure_number': number, 'source_caption_full': caption, 'source_media_url': url,
                    'sha256': sha(raw), 'decoded_pixel_sha256': sha(image.tobytes()),
                    'width': image.width, 'height': image.height, 'pixel_mode': image.mode,
                    'publisher_MD5_verified': True, 'complete_original_pixels_inspected': True,
                    'source_pixels_changed': False}
        special = ''
        if number == 6:
            special = 'The source reports approximately 7.5 mm and Keros type 3; these source values are retained without independent calibration or a new risk measurement. '
        if number == 8:
            special = 'Source caption calls this sagittal, whereas the displayed original image is coronal. The mismatch is retained explicitly; no relabelling or plane-specific anatomical coverage is granted. '
        if number in [2, 4, 5, 10, 13, 14, 17]:
            special += 'Source side assignments are retained without independent native DICOM orientation/laterality verification. '
        limits = special+COMMON
        local = f'web/reference-media/radiology-open/sinonasal-operative-pmc6472854-fig{number}.jpg'
        (ROOT/local).write_bytes(raw)
        context = {'setting': 'in_vivo', 'laterality': 'not_reported', 'population': {'life_stage': 'not_reported'},
                   'extent': 'local', 'depicted_state': 'source_sinonasal_CT_variant_or_pathology_example',
                   'selected_panels': ['whole'], 'panel_types': {'whole': 'CT'},
                   'panel_states': {'whole': 'source_sinonasal_CT_variant_or_pathology_example'},
                   'native_orientation_or_measurement_independently_verified': False,
                   'full_native_anatomical_or_3D_extent_verified': False}
        if number == 8:
            context['source_caption_plane'] = 'sagittal'
            context['displayed_source_plane_review'] = 'coronal'
            context['source_caption_plane_disagreement'] = True
        credit = ', '.join(authors)+'. '+m['title']+'. DOI '+m['doi']+'. CC BY 4.0. Complete original publisher JPEG preserved. NLM/PMC dataset snapshot may not reflect latest NLM data.'
        row = {'id': PREFIX+str(number), 'kind': 'clinical-image', 'modality': 'CT', 'figure_number': number,
               'src': '/app/'+local.removeprefix('web/'), 'sha256': fact['sha256'], 'width': fact['width'], 'height': fact['height'],
               'source_url': SOURCE, 'figure_url': SOURCE+'#f'+str(number), 'asset_source_url': url,
               'clinical_panels': ['whole'], 'source_context': context,
               'image_state': context['depicted_state'], 'caption': f'Original Figure {number}: {title}. '+limits,
               'alt': f'Original Figure {number}: {title}. '+limits, 'limits': limits,
               'source_caption_full': caption, 'structures_visible': ['Source-local '+title.lower()],
               'license': license_name, 'license_url': license_url, 'attribution': credit,
               'source_background': None, 'rights_reviewed_on': '2026-10-07',
               'rights_review': 'Explicit original article grant, whole figure captions and unchanged pixels checked; no separate figure credit found.'}
        rows.append(row); facts.append(fact); locals_.append(local)
    proof = {'pmcid': m['pmcid'], 'doi': m['doi'], 'title': m['title'], 'authors': authors,
             'metadata_sha256': sha(metadata.read_bytes()), 'xml_sha256': sha(xml),
             'permissions_xml': E.tostring(permission, encoding='unicode'), 'original_license': license_name,
             'original_license_url': license_url, 'figures': facts, 'clinical_approval': False,
             'model_promoted': False, 'structure_coverage_granted': False}
    proof_path = OUT/'original-source-review.json'
    proof_path.write_text(json.dumps(proof, indent=2)+'\n')
    assets = []
    for row, local, fact in zip(rows, locals_, facts):
        assets.append({'id': row['id'], 'kind': 'clinical_image', 'name': row['caption'].split('. ')[0],
                       'local_path': local, 'sha256': row['sha256'], 'modality': 'CT', 'investigation_ids': [IDENT],
                       'structure_ids': [], 'requirement_coverage': {}, 'source_context': row['source_context'],
                       'source': {'url': SOURCE, 'figure_url': row['figure_url'], 'asset_url': row['asset_source_url'],
                                  'license': {'name': license_name, 'url': license_url, 'commercial_use': True,
                                              'redistribution': True, 'review_status': 'verified',
                                              'evidence_path': str(proof_path.relative_to(ROOT)),
                                              'evidence_sha256': sha(proof_path.read_bytes()), 'attribution': row['attribution'],
                                              'reviewed_at': '2026-10-07'}},
                       'pixel_provenance': {'source_pixels_changed': False, 'decoded_pixel_sha256': fact['decoded_pixel_sha256'],
                                            'highest_resolution_acquired_master_verified': False},
                       'anatomical_review': {'status': 'pending', 'reason': 'Selected CT stills do not establish full native bone/drainage/neurovascular geometry; source plane mismatch retained.'},
                       'visual_review': {'status': 'source_checked', 'sha256': row['sha256'],
                                         'evidence_path': 'docs/sinonasal-operative-source-review.md', 'reviewed_at': '2026-10-07'}})
    path = ROOT/'data/radiology/radiology-open-images.json'; data = json.loads(path.read_text())
    data[IDENT] = [r for r in data.get(IDENT, []) if not r['id'].startswith(PREFIX)]+rows
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json', assets, prefix=PREFIX)
    path = ROOT/'data/radiology/investigation-overrides-non-msk.json'; data = json.loads(path.read_text())
    data[IDENT]['key_images'] = []; path.write_text(json.dumps(data, indent=2)+'\n')
    path = ROOT/'data/radiology/investigation-source-images.json'; raw = path.read_text()
    if '"'+IDENT+'"' in raw:
        start = raw.index('[', raw.index('"'+IDENT+'"')); old, end = json.JSONDecoder().raw_decode(raw, start)
        path.write_text(raw[:start]+'[]'+raw[end:])
    path = ROOT/'data/radiology/reporting-steps/head-neck.json'; raw = path.read_text()
    start = raw.index('{', raw.index('"'+IDENT+'"')); node, end = json.JSONDecoder().raw_decode(raw, start)
    removed_ids = {r['id'] for r in replaced}
    node.setdefault('start', {}).update(images=[PREFIX+'5', PREFIX+'9'], module_illustrations=False)
    for index, numbers in {0: [5, 10, 11, 12, 15], 1: [1, 2, 3, 4, 5, 10, 11, 16, 17],
                           2: [6, 7, 8, 9, 13, 14, 15], 3: [5, 9], 4: [9, 13, 14]}.items():
        node['steps'][index]['images'] = list(dict.fromkeys([id for id in node['steps'][index].get('images', []) if id not in removed_ids]+[PREFIX+str(n) for n in numbers]))
    path.write_text(raw[:start]+json.dumps(node, indent=2, ensure_ascii=False).replace('\n', '\n    ')+raw[end:])
    archive.write_text(json.dumps({'figures': [{'id': r['id'], 'local_path': local, 'sha256': r['sha256']} for r, local in zip(rows, locals_)],
                                  'replaced_investigation_images': replaced, 'other_investigation_or_lesson_media_changed': False,
                                  'clinical_approval': False, 'structure_coverage_granted': False}, indent=2)+'\n')
    # Re-read mutated source registries before fingerprinting the contract.
    from primer import radiology_catalog
    for value in vars(radiology_catalog).values():
        if callable(getattr(value, "cache_clear", None)):
            value.cache_clear()
    # Only this investigation's changed source/report contract is refreshed.
    ref = detail(Curriculum(), resolve(IDENT))['radiology_reference']
    path = ROOT/'data/radiology/non-msk-structure-requirements.json'; data = json.loads(path.read_text())
    for item in data['investigations']:
        if item['investigation_id'] == IDENT:
            item['source_contract_sha256'] = digest({k: ref.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')})
    path.write_text(json.dumps(data, indent=2)+'\n')
    print('17 original operative CT figures packaged; source caption/plane mismatch retained; no anatomical coverage granted')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    package(parser.parse_args().source_root)
