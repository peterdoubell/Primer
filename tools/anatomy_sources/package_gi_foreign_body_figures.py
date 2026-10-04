#!/usr/bin/env python3
"""Attach complete original CT and radiographic foreign-body examples with exact source versions and assessment limits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC7273454',1): 'Source coronal CT with a source-marked linear object in the lesser-omental region and gastric wall/inflammatory change in a reported contained-perforation case. Full object endpoints, transmural extent and clinical injury depth remain unapproved.',
 ('PMC7273454',2): 'Source sagittal CT of the same reported patient as Figures 1/3, retaining the object and adjacent gastric observations. Another plane is not an independent patient or proof of complete object/wall registration.',
 ('PMC7273454',3): 'Source axial CT of the same reported gastric/lesser-omental case as Figures 1/2. The author fish-bone/migration attribution remains source context; calibrated complete object shape and chronological migration are unverified.',
 ('PMC10880048',1): 'Source CT with a displayed 30 mm caliper and a source-described D1/gallbladder/liver relationship. The article title names pyloric perforation while the figure caption names D1; location, full wall/contact extent and measurement calibration remain source claims pending independent review.',
 ('PMC12380921',1): 'Complete source CT A/B with an original red-circle object observation in a reported small-bowel perforation case. The caption calls A oblique sagittal and B coronal, but visible presentation suggests a plane discrepancy; source-plane correspondence remains unresolved, with no relabelling or registration approval.',
 ('PMC10205967',1): 'Source AP/lateral radiographs A/B in the reported stacked-coin case. Halo/step-off appearance can mimic a battery; projected depth, material and complete injury are not independently established from these views.',
 ('PMC10205967',3): 'Source AP/lateral radiographs A/B from the separate reported button-battery case. This is not the same object/patient as Figure 1, and the apparent shape alone does not establish all material or tissue-injury details.',
 ('PMC10250127',1): 'Source AP/lateral radiographs A/B in a reported stacked-coin case. The original magnified PACS Edge Enhance insets are retained as source-processed images, not unprocessed acquired masters; halo/step-off appearance is not unique battery identification.',
}

OBSERVATIONS = {
 ('PMC7273454',1):['Source-marked linear object and gastric/inflammatory region'],
 ('PMC7273454',2):['Source-marked object and gastric wall region in another source plane'],
 ('PMC7273454',3):['Source-marked lesser-omental object region'],
 ('PMC10880048',1):['Source-displayed object caliper and local GI/adjacent-host region; independent calibration unverified'],
 ('PMC12380921',1):['Original red-circle object/host observation in source A/B; plane correspondence unresolved'],
 ('PMC10205967',1):['Source-marked round/stacked-object projection A','Source lateral object/tracheal projection B'],
 ('PMC10205967',3):['Source round-object projection A','Source lateral object projection B in the separate reported battery case'],
 ('PMC10250127',1):['Source object projections A/B and original PACS-processed insets'],
}



def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/gi-foreign-body-published-source-review'
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
        name = 'gi-foreign-body-' + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-gi-foreign-body-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'gi_foreign_body_source_'+pmc.lower()+'_fig'+str(number)
        context = {'setting': 'in_vivo', 'laterality': side, 'population': {'life_stage': 'not_reported'},
            'depicted_state': state, 'extent': 'local', 'selected_panels': panels,
            'panel_types': types, 'panel_states': dict.fromkeys(types, state)}
        context.update({'independent_patient_identity_verified': False, 'material_and_projection_depth_independently_verified': False, 'reported_case_group': pmc+'-shared-gastric-case' if pmc=='PMC7273454' else pmc+'-figure-'+str(number)})
        if pmc=='PMC12380921': context['source_plane_claims_unresolved']=True
        if pmc=='PMC10250127': context['source_processed_insets_retained']=True
        if not types:
            for k in ['selected_panels', 'panel_types', 'panel_states']:
                context.pop(k)
        limits = ('Complete original published figure only: no calibrated DICOM volume, independently verified acquisition timing, '
            'complete object/endpoints, projected-versus-CT wall/organ/vessel depth, injury/migration extent or patient-specific 3D model. Original source labels and diagnoses remain '
            'author descriptions; no complete injury depth, material identity or complete object/tissue continuity, histological certainty or modality feature is borrowed from other panels. '
            'The publications are imaging context, not current management guidance; use the explicitly named current clinical framework. '
            'Pixel samples are preserved, but native acquired master resolution and display/ICC colour calibration are unverified.')
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
            'rights_reviewed_on': '2026-10-04', 'rights_review': 'Original XML grant and complete captions reviewed; complete selected captions checked for separate credits. Publisher checksums and independent PDF stream/sample readback verified.'}
        ancillary = []
        for kind in ['CT', 'Ultrasound']:
            other = [p for p, t in types.items() if t == kind and kind != modality]
            if other:
                ancillary.append({'kind': kind, 'panels': other, 'structures_visible': ['Separate source ' + kind + ' context'],
                    'limits': 'Separate modality; cannot supply MRI signal, sequence identity, independently registered geometry or a complete diagnostic assessment.'})
        if not types:
            row.pop('clinical_panels')
        if ancillary:
            row['ancillary_panels'] = ancillary
        row['source_background']='white'
        rows.append(row)
        assets.append({'id': ident, 'kind': 'clinical_image', 'name': article['title'] + ' Fig' + str(number),
            'local_path': local, 'sha256': source['sha256'], 'regions': ['abdomen'],
            'investigation_ids': ['ra.gi-foreign-bodies'], 'structure_ids': [], 'requirement_coverage': {},
            'modality': modality, 'source_context': context,
            'source': {'url': article['source_article_url'], 'figure_url': row['figure_url'], 'asset_url': article['pdf_url'],
                'license': {'name': article['license'], 'url': article['license_url'], 'commercial_use': True,
                    'redistribution': True, 'review_status': 'verified', 'evidence_path': str(proof_path.relative_to(ROOT)),
                    'evidence_sha256': sha(proof_path), 'attribution': credit, 'reviewed_at': '2026-10-04'}},
            'pixel_provenance': {'source_pdf_sha256': article['pdf_sha256'], 'pdf_object_id': source['pdf_object_id'],
                'acquisition': source['acquisition'], 'decoded_pixel_sha256': source['decoded_pixel_sha256'],
                'original_encoded_stream_or_decoded_pixel_readback_verified': True,
                'source_pixels_changed': False, 'highest_resolution_acquired_master_verified': False},
            'anatomical_review': {'status': 'pending', 'reason': 'Local published sections do not establish every reporting structure, full lesion geometry or independently validated clinical diagnosis.'},
            'visual_review': {'status': 'source_checked', 'sha256': source['sha256'], 'reviewed_at': '2026-10-04',
                'evidence_path': 'docs/gi-foreign-body-published-source-review.md'}})
        records.append({'figure_number': number, 'local_path': local, 'sha256': source['sha256'],
            'width': source['width'], 'height': source['height'], 'repository_dimensions': source['repository_dimensions'], 'pmcid': pmc, 'single_unlettered_figure': not types,
            'modality': modality, 'clinical_panels': panels, 'source_panel_types': types,
            'source_pixels_changed': False})
    ids = {r['id'] for r in rows}
    images['ra.gi-foreign-bodies'] = [r for r in images.get('ra.gi-foreign-bodies', []) if r['id'] not in ids] + rows
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
