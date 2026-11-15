#!/usr/bin/env python3
"""Attach original gallbladder examples without claiming full anatomy or diagnostic certainty."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC5359147',3):'Source carcinoma/differential example: ultrasound A and separate CT B. Imaging appearances and source diagnosis do not independently prove histology or full wall/liver extent.',
 ('PMC5359147',5):'Source adenomyomatosis patterns on ultrasound A–E. Intramural spaces, shadowing and reverberation remain local source observations; colour-Doppler twinkling D is an artifact, not wall hypervascularity.',
 ('PMC5359147',6):'Source probe comparison: ultrasound A uses a reported 5 MHz probe, B a reported 7 MHz probe. Better visible intramural detail does not establish calibrated native resolution or complete wall layers.',
 ('PMC5359147',7):'Single source ultrasound with a polypoid component and wall change. Source cholesterol-polyp and adenomyomatosis descriptions remain unapproved diagnostic context.',
 ('PMC5359147',8):'Single source ultrasound showing echogenic intramural material without acoustic shadowing. A still frame cannot establish mobility or universal benignity.',
 ('PMC5359147',9):'Source contrast-enhanced ultrasound views A/B. The static views do not prove every phase or complete vascular response; independent acquisition timing is not verified.',
 ('PMC12181115',1):'Single source ultrasound with a striated wall and sludge in the described acalculous-cholecystitis case. Clinical diagnosis, tenderness and severity cannot be established from this frame alone.',
 ('PMC12181115',4):'Source gangrenous-cholecystitis example: ultrasound A, CT B and separate radiographic drainage image C. Membrane appearances do not establish actual movement; drainage context is not CT or independent proof of patency.',
 ('PMC12181115',6):'Source perforation example with unlettered ultrasound at left and CT at middle/right. Position identifiers describe the observed layout, not invented publication letters. Source wall defects and clinical diagnosis do not establish complete leak geometry or severity.',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/gallbladder-published-source-review'
    proof_path = folder / 'original-source-review.json'
    proof = json.loads(proof_path.read_text())
    images_path = ROOT / 'data/radiology/radiology-open-images.json'
    assets_path = ROOT / 'data/radiology/radiology-asset-evidence.json'
    images = json.loads(images_path.read_text())
    rows, assets, records = [], [], []
    for source in proof['figures']:
        number = source['figure_number']
        pmc = source['pmcid']; article = next(a for a in proof['articles'] if a['pmcid'] == pmc)
        modality, side, caption = 'Ultrasound', 'not_reported', CASES[(pmc, number)]
        src = folder / source['file']
        if sha(src) != source['sha256'] or not source['original_colour_and_mask_readback_verified']:
            raise ValueError('Original figure preservation differs')
        name = 'gallbladder-' + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-gallbladder-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_roles']; scheme = source['panel_identifier_scheme']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'gallbladder_source_'+pmc.lower()+'_fig'+str(number)
        context = {'setting':'in_vivo','laterality':side,'population':{'life_stage':'adult' if pmc=='PMC12181115' else 'not_reported'},
                   'depicted_state':state,'extent':'local','selected_panels':panels,'panel_types':types,'panel_states':dict.fromkeys(types,state)}
        if scheme == 'position_unlettered':context['panel_identifier_scheme']=scheme
        if scheme == 'whole_unlettered':
            for k in ['selected_panels','panel_types','panel_states']:context.pop(k)
        limits = ('Complete original published figure only: no calibrated DICOM volume, independently verified acquisition timing, '
            'whole gallbladder/neck/wall/material/collection extent or patient-specific 3D model. Original source labels and diagnoses remain '
            'author descriptions; no mobility, compression response, tenderness, drainage function, histological certainty or modality feature is borrowed from other panels. '
            'The publications are imaging context, not current management guidance; use the explicitly named current clinical framework. '
            'Pixel samples are preserved, but native acquired master resolution and display/ICC colour calibration are unverified.')
        credit = (article['copyright'] + ' ' + ', '.join(article['authors']) + '. ' + article['title'] +
            '. DOI ' + article['doi'] + '. CC BY 4.0. Complete original Figure ' + str(number) +
            ' preserved from the verified publication PDF without changing image samples. '
            'NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.')
        row = {'id': ident, 'kind': 'clinical-image', 'src': '/app/reference-media/radiology-open/' + name,
            'width': source['width'], 'height': source['height'], 'sha256': source['sha256'],
            'source_url': article['source_article_url'], 'figure_url': article['source_article_url'] + '#Fig' + str(number),
            'figure_number': number, 'asset_source_url': article['pdf_url'], 'modality': modality,
            'clinical_panels': panels, 'image_state': state, 'source_context': context,
            'caption': caption, 'alt': caption, 'limits': limits,
            'structures_visible': ['Source-described local gallbladder appearance; complete anatomical extent not approved'],
            'license': article['license'], 'license_url': article['license_url'], 'attribution': credit,
            'rights_reviewed_on': '2026-10-04', 'rights_review': 'Original XML grant and complete captions reviewed; separately credited diagrams and articles without sufficient grants excluded. Publisher checksums and independent PDF stream/sample readback verified.'}
        ancillary = []
        for kind in ['CT', 'Radiography']:
            other = [p for p, t in types.items() if t == kind and kind != modality]
            if other:
                ancillary.append({'kind': kind, 'panels': other, 'structures_visible': ['Separate source ' + kind + ' context'],
                    'limits': 'Separate modality; cannot supply ultrasound-specific signal, shadowing, dynamic observations, independently registered geometry or a complete diagnostic assessment.'})
        if scheme == 'whole_unlettered':
            row.pop('clinical_panels')
        if ancillary:
            row['ancillary_panels'] = ancillary
        if scheme == 'position_unlettered':row['panel_identifier_scheme']=scheme
        row['source_background']='white'
        rows.append(row)
        assets.append({'id': ident, 'kind': 'clinical_image', 'name': article['title'] + ' Fig' + str(number),
            'local_path': local, 'sha256': source['sha256'], 'regions': ['abdomen'],
            'investigation_ids': ['ra.ultrasound-gallbladder'], 'structure_ids': [], 'requirement_coverage': {},
            'modality': modality, 'source_context': context,
            'source': {'url': article['source_article_url'], 'figure_url': row['figure_url'], 'asset_url': article['pdf_url'],
                'license': {'name': article['license'], 'url': article['license_url'], 'commercial_use': True,
                    'redistribution': True, 'review_status': 'verified', 'evidence_path': str(proof_path.relative_to(ROOT)),
                    'evidence_sha256': sha(proof_path), 'attribution': credit, 'reviewed_at': '2026-10-04'}},
            'pixel_provenance': {'source_pdf_sha256': article['pdf_sha256'], 'pdf_object_id': source['pdf_object_id'],
                'acquisition': source['acquisition'], 'decoded_pixel_sha256': source['decoded_pixel_sha256'],
                'original_colour_and_mask_readback_verified': True, 'soft_mask':source['soft_mask'],
                'source_pixels_changed': False, 'highest_resolution_acquired_master_verified': False},
            'anatomical_review': {'status': 'pending', 'reason': 'Local published sections do not establish every reporting structure, full lesion geometry or independently validated clinical diagnosis.'},
            'visual_review': {'status': 'source_checked', 'sha256': source['sha256'], 'reviewed_at': '2026-10-04',
                'evidence_path': 'docs/gallbladder-published-source-review.md'}})
        records.append({'figure_number': number, 'local_path': local, 'sha256': source['sha256'],
            'width': source['width'], 'height': source['height'], 'repository_dimensions': source['repository_dimensions'], 'pmcid': pmc, 'panel_identifier_scheme':scheme,
            'modality': modality, 'clinical_panels': panels, 'source_panel_types': types,
            'source_pixels_changed': False})
    ids = {r['id'] for r in rows}
    images['ra.ultrasound-gallbladder'] = [r for r in images.get('ra.ultrasound-gallbladder', []) if r['id'] not in ids] + rows
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
        'source_figures_integrated_into_local_reader': True, 'clinical_approval': False, 'structure_coverage_granted': False, 'held_models_promoted': False}, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True)
    package(p.parse_args().source_root)
