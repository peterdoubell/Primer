#!/usr/bin/env python3
"""Attach source-preserved bowel-wall CT figures with exact CC BY 2.0 attribution and explicit clinical limits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC3999365',6): 'Source contrast-enhanced coronal CT with sigmoid diverticula, local wall thickening and disproportionately marked pericolonic fat stranding. The author diverticulitis interpretation requires the actual clinical context; complete diverticular/wall extent is not established by this section.',
 ('PMC3999365',9): 'Source contrast-enhanced CT a/b with an enlarged fluid-filled retrocaecal appendix, adjacent fat stranding and reactive ascending-colon wall thickening. The two source planes are retained together; full appendiceal/colonic extent and independent diagnosis remain unapproved.',
 ('PMC3999365',12): 'Source contrast-enhanced CT with circumferential stratified small-bowel wall in the reported lupus/vasculitis context. The pattern does not independently prove vasculitis, histological layers or complete clinical viability.',
 ('PMC3999365',13): 'Source contrast-enhanced CT with stratified small-bowel wall and a source-marked interloop fistula in a Crohn disease context. Complete fistula tract/openings and activity assessment remain unapproved from this single section.',
 ('PMC3999365',14): 'Source contrast-enhanced CT with marked ascending/descending colonic wall thickening, stratification and limited adjacent fat stranding. The author pseudomembranous-colitis suggestion is not an independent microbiological diagnosis from the image.',
 ('PMC3999365',15): 'Source contrast-enhanced CT with stratified low-lying small-bowel wall and fluid in the reported radiation-treatment context. Treatment field, temporal causation and complete injured extent cannot be established from this section alone.',
 ('PMC3999365',17): 'Source contrast-enhanced CT showing a rectal fat-halo/wall observation in a reported longstanding Crohn disease case. It is not a healthy or non-IBD example; a fat halo alone does not establish the clinical cause or every histological layer.',
 ('PMC3999365',18): 'Source contrast-enhanced CT with thickened hyperattenuating bowel, engorged mesenteric vessels and fluid in a reported severe-hypovolaemia/shock context. High wall attenuation alone does not establish that cause, phase timing or whole-bowel perfusion.',
 ('PMC3999365',20): 'Source contrast-enhanced CT a/b with a thickened stenotic ileal region, source-described hyperenhancement and upstream dilatation in a Crohn disease context. The paired planes do not establish full stricture/fistula geometry or independent activity criteria.',
 ('PMC3999365',22): 'Source contrast-enhanced CT a/b with thickened low-attenuation descending-colon and rectal wall. The source reports colonoscopy/biopsy confirmation of ischaemic colitis; the published CT sections do not independently prove those results or histological injury depth.',
}

SOURCE_OBSERVATIONS = {
 6: ['Source-marked sigmoid diverticulum/wall and adjacent pericolonic fat'],
 9: ['Source-marked retrocaecal appendix and adjacent reactive colonic wall in a/b'],
 12: ['Source-marked stratified small-bowel wall; histological layer assignment unapproved'],
 13: ['Source-marked stratified bowel wall', 'Source-marked interloop fistula; complete tract/openings unapproved'],
 14: ['Source-marked ascending and descending colonic wall/stratification'],
 15: ['Source-marked low-lying small-bowel wall and adjacent fluid'],
 17: ['Source-marked rectal fat-halo/wall observation; not a non-IBD reference'],
 18: ['Source-marked small-bowel wall and mesenteric vessels/fluid'],
 20: ['Source-marked ileal wall/stenotic region and upstream dilated bowel in a/b'],
 22: ['Source-marked descending-colon wall in a and rectal wall in b'],
}



def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/bowel-wall-published-source-review'
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
        name = 'bowel-wall-' + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-bowel-wall-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'bowel_wall_source_'+pmc.lower()+'_fig'+str(number)
        context = {'setting': 'in_vivo', 'laterality': side, 'population': {'life_stage': 'not_reported'},
            'depicted_state': state, 'extent': 'local', 'independent_patient_identity_verified': False, 'native_phase_timing_verified': False, 'selected_panels': panels,
            'panel_types': types, 'panel_states': dict.fromkeys(types, state)}
        if not types:
            for k in ['selected_panels', 'panel_types', 'panel_states']:
                context.pop(k)
        limits = ('Complete original published figure only: no calibrated DICOM volume, independently verified acquisition timing, '
            'whole wall/lumen/lesion/fistula/mesenteric-vessel extent or patient-specific 3D model. Original source labels and diagnoses remain '
            'author descriptions; no clinical viability, histological injury depth or complete fistula continuity, histological certainty or modality feature is borrowed from other panels. '
            'The publications are imaging context, not current management guidance; use the explicitly named current clinical framework. '
            'Pixel samples are preserved, but native acquired master resolution and display/ICC colour calibration are unverified.')
        credit = (article['copyright'] + ' ' + ', '.join(article['authors']) + '. ' + article['title'] +
            '. DOI ' + article['doi'] + '. CC BY 2.0. Complete original Figure ' + str(number) +
            ' preserved from the verified publication PDF without changing image samples. '
            'NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.')
        row = {'id': ident, 'kind': 'clinical-image', 'src': '/app/reference-media/radiology-open/' + name,
            'width': source['width'], 'height': source['height'], 'sha256': source['sha256'],
            'source_url': article['source_article_url'], 'figure_url': article['source_article_url'] + '#'+source['source_figure_id'],
            'figure_number': number, 'asset_source_url': article['pdf_url'], 'modality': modality,
            'clinical_panels': panels, 'image_state': state, 'source_context': context,
            'caption': caption, 'alt': caption, 'limits': limits,
            'structures_visible': SOURCE_OBSERVATIONS[number],
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
            'investigation_ids': ['ra.ct-bowel-wall'], 'structure_ids': [], 'requirement_coverage': {},
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
                'evidence_path': 'docs/bowel-wall-published-source-review.md'}})
        records.append({'figure_number': number, 'local_path': local, 'sha256': source['sha256'],
            'width': source['width'], 'height': source['height'], 'repository_dimensions': source['repository_dimensions'], 'pmcid': pmc, 'single_unlettered_figure': not types,
            'modality': modality, 'clinical_panels': panels, 'source_panel_types': types,
            'source_pixels_changed': False})
    ids = {r['id'] for r in rows}
    images['ra.ct-bowel-wall'] = [r for r in images.get('ra.ct-bowel-wall', []) if r['id'] not in ids] + rows
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
