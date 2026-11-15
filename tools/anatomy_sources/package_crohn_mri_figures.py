#!/usr/bin/env python3
"""Attach complete Crohn MRI figures while preserving distinct modality, patient and sequence sources."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC12634764',1): 'Complete source figure: ultrasound a/b and MRI c/d/e in a reported terminal-ileal Crohn case. MRI c is coronal T2; d axial fat-suppressed T2; e source-described b600 diffusion. No ADC panel is supplied, so apparent DWI brightness alone does not independently verify restricted diffusion. Doppler colour in b is ultrasound, not MRI perfusion.',
 ('PMC12634764',2): 'Two different patients: ultrasound a/b depicts source-described neoterminal ileal tracts and inflammatory mass after resection in a 32-year-old man; MRI c/d depicts distal-ileal disease and adjacent abscess in a separate 41-year-old man. MRI c is axial fat-suppressed post-contrast T1; d axial T2. No cross-patient geometry, endpoints or MRI tract proof is transferred from a/b.',
 ('PMC12634764',3): 'Source-reported baseline MRI a/b/c and six-month follow-up d/e/f in the same patient: coronal T2 a/d, coronal fat-suppressed T2 b/e, axial fat-suppressed T2 c/f. The source describes reduced mural/perimural signal and improved dilation, with persistent proximal dilation near the shorter stricture. Original arrows and enterolith markers remain. These are selected corresponding views, not independently registered volumes or proof of complete remission, quantified fibrosis or treatment causality.',
 ('PMC12634764',4): 'Complete seven-panel source: MRI a/b/d, CT c/e and ultrasound f/g. MRI a/b are axial T2 with/without fat suppression; d is axial post-contrast T1. The source describes complex ileal/sigmoid fistulating disease. CT c was performed one day before MRE; ultrasound f/g one week later. CT e has persistent narrowing/obstruction in the source description, but its timing is not separately established. Cross-modality correspondence and complete tract endpoints remain unverified.',
 ('PMC12634764',6): 'MRI a shows source-described multifocal mainly chronic stricturing and dilation on coronal T2; the caption refers to fat-suppressed sequences that are not shown. CT b/c/d was obtained two months later during an acute presentation and depicts source-described perforation/free gas/fluid and a pelvic stricture. Later CT cannot supply baseline MRI signal or prove that free gas/perforation was present at the earlier MRI. Histological fibrosis fraction and complete stricture/tract geometry remain unverified.',
}
OBSERVATIONS = {
 ('PMC12634764',1): ['Source MRI terminal-ileal wall and perimural signal observations c/d; b600 DWI e without ADC'],
 ('PMC12634764',2): ['Source MRI distal ileal wall, adjacent collection and nearby fluid c/d in the separately reported MRI patient'],
 ('PMC12634764',3): ['Source baseline/follow-up MRI bowel-wall, perimural, narrowing and upstream-lumen observations'],
 ('PMC12634764',4): ['Source MRI local ileal/sigmoid wall and fistulating-region observations a/b/d'],
 ('PMC12634764',6): ['Source coronal T2 narrowing, upstream lumen and enterolith-region observations a'],
}
SEQUENCES = {
 1: {'c': 'coronal T2', 'd': 'axial T2 fat-suppressed', 'e': 'axial DWI b600; no ADC panel supplied'},
 2: {'c': 'axial post-contrast T1 fat-suppressed', 'd': 'axial T2'},
 3: {'a': 'baseline coronal T2', 'b': 'baseline coronal T2 fat-suppressed', 'c': 'baseline axial T2 fat-suppressed', 'd': 'six-month follow-up coronal T2', 'e': 'six-month follow-up coronal T2 fat-suppressed', 'f': 'six-month follow-up axial T2 fat-suppressed'},
 4: {'a': 'axial T2', 'b': 'axial T2 fat-suppressed', 'd': 'axial post-contrast T1'},
 6: {'a': 'coronal T2; referred fat-suppressed sequences are not shown'},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/crohn-mri-published-source-review'
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
        name = 'crohn-mri-' + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-crohn-mri-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'crohn_mri_source_'+pmc.lower()+'_fig'+str(number)
        context = {'setting': 'in_vivo', 'laterality': side, 'population': {'life_stage': 'not_reported'},
            'depicted_state': state, 'extent': 'local', 'selected_panels': panels,
            'panel_types': types, 'panel_states': dict.fromkeys(types, state)}
        context.update({'independent_patient_identity_verified': False, 'native_sequence_and_registration_verified': False,
            'source_mri_sequences': SEQUENCES[number], 'reported_case_group': pmc+'-figure-'+str(number)})
        if number == 1:
            context['adc_panel_supplied'] = False
        if number == 2:
            context['panel_case_groups'] = {'a': 'post-resection-ultrasound-case', 'b': 'post-resection-ultrasound-case', 'c': 'separate-mri-abscess-case', 'd': 'separate-mri-abscess-case'}
            context['multiple_reported_patients'] = True
        if number == 3:
            context['panel_timepoints'] = dict.fromkeys('abc', 'baseline') | dict.fromkeys('def', 'six-month follow-up')
            context['independent_spatial_registration_verified'] = False
        if number == 4:
            context['panel_timepoints'] = {'a': 'MRE', 'b': 'MRE', 'c': 'one day before MRE', 'd': 'MRE', 'e': 'not separately established', 'f': 'one week later', 'g': 'one week later'}
        if number == 6:
            context['panel_timepoints'] = {'a': 'baseline MRE', 'b': 'two months later CT', 'c': 'two months later CT', 'd': 'two months later CT'}
            context['referred_fat_suppressed_sequences_supplied'] = False
        if not types:
            for k in ['selected_panels', 'panel_types', 'panel_states']:
                context.pop(k)
        limits = ('Complete published figure with original lower-case panel labels and annotations only: no calibrated DICOM/MRI acquisition, full sequence stack, independently verified acquisition timing, '
            'DWI/ADC correspondence, complete bowel/tract/endpoint anatomy, histological fibrosis fraction or patient-specific 3D model. Source diagnoses and reported patient/time relationships remain author descriptions; '
            'CT, ultrasound/Doppler, other patients and later examinations do not supply missing MRI features. Selected comparison stills are not independent spatial registration, complete treatment response or motion/persistence evidence. '
            'Original published pixels are retained; highest-resolution acquired masters and display colour calibration remain unverified.')
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
            'investigation_ids': ['ra.mri-crohn'], 'structure_ids': [], 'requirement_coverage': {},
            'modality': modality, 'source_context': context,
            'source': {'url': article['source_article_url'], 'figure_url': row['figure_url'], 'asset_url': article['pdf_url'],
                'license': {'name': article['license'], 'url': article['license_url'], 'commercial_use': True,
                    'redistribution': True, 'review_status': 'verified', 'evidence_path': str(proof_path.relative_to(ROOT)),
                    'evidence_sha256': sha(proof_path), 'attribution': credit, 'reviewed_at': '2026-10-05'}},
            'pixel_provenance': {'source_pdf_sha256': article['pdf_sha256'], 'pdf_object_id': source['pdf_object_id'],
                'acquisition': source['acquisition'], 'decoded_pixel_sha256': source['decoded_pixel_sha256'],
                'original_encoded_stream_or_decoded_pixel_readback_verified': True,
                'source_pixels_changed': False, 'highest_resolution_acquired_master_verified': False},
            'anatomical_review': {'status': 'pending', 'reason': 'Local published MRI views do not establish every reporting structure, full sequence/tract geometry or independently validated clinical diagnosis.'},
            'visual_review': {'status': 'source_checked', 'sha256': source['sha256'], 'reviewed_at': '2026-10-05',
                'evidence_path': 'docs/crohn-mri-published-source-review.md'}})
        records.append({'figure_number': number, 'local_path': local, 'sha256': source['sha256'],
            'width': source['width'], 'height': source['height'], 'repository_dimensions': source['repository_dimensions'], 'pmcid': pmc, 'single_unlettered_figure': not types,
            'modality': modality, 'clinical_panels': panels, 'source_panel_types': types,
            'source_pixels_changed': False})
    ids = {r['id'] for r in rows}
    images['ra.mri-crohn'] = [r for r in images.get('ra.mri-crohn', []) if r['id'] not in ids] + rows
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
