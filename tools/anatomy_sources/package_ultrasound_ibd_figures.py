#!/usr/bin/env python3
"""Attach complete IUS-bearing figures with separate modality, patient and dynamic-source limits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC12634764',1): 'Complete original figure: ultrasound a shows source-marked terminal-ileal wall/stratification, mesenteric fat and nodal observations; b colour Doppler shows source-described mural/perimural vascularity. MRI c/d/e are separate sequences. Doppler acquisition settings, full bowel coverage, histological depth and dynamic compression/motion are not supplied by these stills.',
 ('PMC12634764',2): 'Two different patients: ultrasound a/b shows source-described neoterminal ileal tracts and an inflammatory mass after resection in a 32-year-old man. MRI c/d depicts distal-ileal disease and abscess in a separate 41-year-old man. The MRI abscess cannot be transferred to the ultrasound patient or supply missing ultrasound endpoints, flow or full penetrating extent.',
 ('PMC12634764',4): 'Complete seven-panel source figure: ultrasound f shows source-described mid-ileal skip disease, wall/sonographic-band and mesenteric observations; g colour Doppler depicts source-described vascularity. These were obtained one week after MRE. MRI a/b/d and CT c/e are separate modalities/timepoints and do not establish full ultrasound tract endpoints, histology, Doppler calibration or observed motion.',
 ('PMC12634764',5): 'Original grayscale source figure: ultrasound a depicts source-described dilated fluid-filled small-bowel loops; CT b contains two axial portal-venous views of source-described terminal-ileal stricturing obstruction. Both CT views share the original b label; no c label is invented. CT localisation/cause is not independent ultrasound stricture proof, and still images do not demonstrate peristalsis or fixedness.',
}
OBSERVATIONS = {
 ('PMC12634764',1): ['Source ultrasound terminal-ileal wall, adjacent fat/node a and mural/perimural colour Doppler b'],
 ('PMC12634764',2): ['Source ultrasound neoterminal ileal tract/mass a and colour Doppler b in the ultrasound patient'],
 ('PMC12634764',4): ['Source ultrasound mid-ileal wall/mesentery f and Doppler g one week after MRE'],
 ('PMC12634764',5): ['Source ultrasound dilated fluid-filled bowel loop a; ultrasound transition/cause not established by the CT panels'],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/ultrasound-ibd-published-source-review'
    proof_path = folder / 'original-source-review.json'
    proof = json.loads(proof_path.read_text())
    images_path = ROOT / 'data/radiology/radiology-open-images.json'
    assets_path = ROOT / 'data/radiology/radiology-asset-evidence.json'
    images = json.loads(images_path.read_text())
    rows, assets, records = [], [], []
    for source in proof['figures']:
        number = source['figure_number']
        pmc = source['pmcid']; article = next(a for a in proof['articles'] if a['pmcid'] == pmc)
        modality, side, caption = source['source_modality'], 'not_reported', CASES[(pmc, number)]
        src = root / source['extracted_file']
        if sha(src) != source['sha256'] or not source['original_encoded_stream_or_decoded_pixel_readback_verified']:
            raise ValueError('Original figure preservation differs')
        name = ('crohn-mri-' if number in {1, 2, 4} else 'ultrasound-ibd-') + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-ultrasound-ibd-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'ultrasound_ibd_source_'+pmc.lower()+'_fig'+str(number)
        context = {'setting': 'in_vivo', 'laterality': side, 'population': {'life_stage': 'not_reported'},
            'depicted_state': state, 'extent': 'local', 'selected_panels': panels,
            'panel_types': types, 'panel_states': dict.fromkeys(types, state)}
        context.update({'independent_patient_identity_verified': False, 'native_acquisition_and_dynamic_source_verified': False,
            'doppler_settings_verified': False, 'real_time_or_cine_source_supplied': False,
            'reported_case_group': pmc+'-figure-'+str(number)})
        if number == 2:
            context['panel_case_groups'] = {'a': 'post-resection-ultrasound-case', 'b': 'post-resection-ultrasound-case', 'c': 'separate-mri-abscess-case', 'd': 'separate-mri-abscess-case'}
            context['multiple_reported_patients'] = True
        if number == 4:
            context['panel_timepoints'] = {'a': 'MRE', 'b': 'MRE', 'c': 'one day before MRE', 'd': 'MRE', 'e': 'not separately established', 'f': 'one week later', 'g': 'one week later'}
        if number == 5:
            context['ct_b_contains_two_source_views'] = True
        if not types:
            for k in ['selected_panels', 'panel_types', 'panel_states']:
                context.pop(k)
        limits = ('Complete published source artwork with original lower-case panel labels and annotations only: no raw ultrasound acquisition, calibrated Doppler settings, cine/repeated-source motion/compression, '
            'complete bowel/tract/endpoint anatomy, histological layer mapping, fibrosis fraction or patient-specific 3D model. Source observations and reported patient/time relationships remain author descriptions. '
            'MRI/CT, different patients and separate examinations cannot supply absent ultrasound features, perfusion, dynamic motion or full extent. '
            'Original published pixels are retained; highest-resolution acquired masters and display calibration remain unverified.')
        credit = (article['copyright'] + ' ' + ', '.join(article['authors']) + '. ' + article['title'] +
            '. DOI ' + article['doi'] + '. ' + article['license'] + '. Complete original Figure ' + str(number) +
            ' preserved from the verified publication PDF without changing image samples. '
            'NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.')
        row = {'id': ident, 'kind': 'clinical-image', 'src': '/app/reference-media/radiology-open/' + name,
            'width': source['width'], 'height': source['height'], 'sha256': source['sha256'],
            'source_url': article['source_article_url'], 'figure_url': article['source_article_url'] + '#'+source['source_figure_id'],
            'figure_number': number, 'asset_source_url': article['pdf_url'], 'modality': modality,
            'clinical_panels': panels, 'image_state': state, 'source_context': context,
            'caption': caption, 'alt': caption, 'limits': limits,
            'structures_visible': OBSERVATIONS[(pmc,number)],
            'license': article['license'], 'license_url': article['license_url'], 'attribution': credit,
            'rights_reviewed_on': '2026-10-05', 'rights_review': 'Original XML grant and complete captions reviewed; complete selected captions checked for separate credits. Publisher checksums and independent PDF stream/sample readback verified.'}
        ancillary = []
        for kind in ['CT', 'MRI']:
            other = [p for p, t in types.items() if t == kind and kind != modality]
            if other:
                ancillary.append({'kind': kind, 'panels': other, 'structures_visible': ['Separate source ' + kind + ' context'],
                    'limits': 'Separate modality; cannot supply ultrasound signal, Doppler settings, motion, independently registered geometry or a complete diagnostic assessment.'})
        if not types:
            row.pop('clinical_panels')
        if ancillary:
            row['ancillary_panels'] = ancillary
        row['source_background']='white'
        rows.append(row)
        assets.append({'id': ident, 'kind': 'clinical_image', 'name': article['title'] + ' Fig' + str(number),
            'local_path': local, 'sha256': source['sha256'], 'regions': ['abdomen'],
            'investigation_ids': ['ra.ultrasound-ibd'], 'structure_ids': [], 'requirement_coverage': {},
            'modality': modality, 'source_context': context,
            'source': {'url': article['source_article_url'], 'figure_url': row['figure_url'], 'asset_url': article['pdf_url'],
                'license': {'name': article['license'], 'url': article['license_url'], 'commercial_use': True,
                    'redistribution': True, 'review_status': 'verified', 'evidence_path': str(proof_path.relative_to(ROOT)),
                    'evidence_sha256': sha(proof_path), 'attribution': credit, 'reviewed_at': '2026-10-05'}},
            'pixel_provenance': {'source_pdf_sha256': article['pdf_sha256'], 'pdf_object_id': source['pdf_object_id'],
                'acquisition': source['acquisition'], 'decoded_pixel_sha256': source['decoded_pixel_sha256'],
                'original_encoded_stream_or_decoded_pixel_readback_verified': True,
                'source_pixels_changed': False, 'highest_resolution_acquired_master_verified': False},
            'anatomical_review': {'status': 'pending', 'reason': 'Local published ultrasound stills do not establish every reporting structure, full dynamic/tract evidence or independently validated clinical diagnosis.'},
            'visual_review': {'status': 'source_checked', 'sha256': source['sha256'], 'reviewed_at': '2026-10-05',
                'evidence_path': 'docs/ultrasound-ibd-published-source-review.md'}})
        records.append({'figure_number': number, 'local_path': local, 'sha256': source['sha256'],
            'width': source['width'], 'height': source['height'], 'repository_dimensions': source['repository_dimensions'], 'pmcid': pmc, 'single_unlettered_figure': not types,
            'modality': modality, 'clinical_panels': panels, 'source_panel_types': types,
            'source_pixels_changed': False})
    ids = {r['id'] for r in rows}
    images['ra.ultrasound-ibd'] = [r for r in images.get('ra.ultrasound-ibd', []) if r['id'] not in ids] + rows
    images_path.write_text(json.dumps(images, indent=2, ensure_ascii=False) + '\n')
    # Retain unrelated evidence record text exactly.
    raw = assets_path.read_text()
    start = raw.index('[', raw.index('"assets"')) + 1
    cursor, retained, decoder = start, [], json.JSONDecoder()
    while True:
        cursor += len(re.match(r'\s*', raw[cursor:]).group())
        if raw[cursor] == ']':
            break
        record, end = decoder.raw_decode(raw, cursor)
        if record['id'] not in ids:
            retained.append(raw[cursor:end])
        cursor = end + len(re.match(r'\s*', raw[end:]).group())
        if raw[cursor] == ',':
            cursor += 1
    retained += [json.dumps(r, indent=2, ensure_ascii=False).replace('\n', '\n    ') for r in assets]
    assets_path.write_text(raw[:start] + '\n    ' + ',\n    '.join(retained) + '\n  ' + raw[cursor:])
    (folder / 'packaged-source-images.json').write_text(json.dumps({'figures': records,
        'clinical_approval': False, 'structure_coverage_granted': False, 'held_models_promoted': False}, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True)
    package(p.parse_args().source_root)
