#!/usr/bin/env python3
"""Attach original adrenal examples without claiming full anatomy or diagnostic certainty."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
    1: ('MRI', 'left', 'Source adenoma example: unenhanced CT A and matched in-/opposed-phase MRI B/C. Published signal loss and diagnosis are source descriptions, not independent endocrine or histological proof.'),
    2: ('MRI', 'bilateral', 'Source bilateral nodular hyperplasia on MRI A–D. The original caption inconsistently labels the opposed-phase panel C and later B; this ambiguity is preserved rather than silently corrected.'),
    3: ('CT', 'right', 'Source adrenal haemorrhage: unenhanced CT A and source-described arterial CT B. High attenuation and lack of enhancement are local observations; underlying tumour exclusion requires its own clinical and temporal evidence.'),
    4: ('MRI', 'right', 'Source adrenal cyst on MRI: T2 fat-suppressed A, precontrast T1 B and postcontrast T1 C. The complete figure retains the local fluid and enhancement comparison without supplying whole cyst-wall geometry.'),
    5: ('MRI', 'left', 'Source myelolipoma: CT A and MRI B–E distinguish macroscopic fat, fat suppression and a soft-tissue component. Source diagnosis does not make every fat-containing adrenal mass a myelolipoma.'),
    6: ('MRI', 'bilateral', 'Source bilateral phaeochromocytoma in MEN2: MRI A–C retain T2 and pre-/postcontrast appearances. The clinical diagnosis and endocrine function cannot be inferred from signal or enhancement alone.'),
    7: ('CT', 'right', 'Source haemangioma: coronal CT A–C show precontrast, arterial and late contrast appearances. Actual injection timing and complete vascular anatomy are not supplied by these sections.'),
    8: ('MRI', 'right', 'Source-described cortical carcinoma: ultrasound A and MRI B–D retain heterogeneous tissue, haemorrhagic and nonenhancing components. Ultrasound is a separate adjunct; MRI does not independently prove tumour histology or full invasion extent.'),
    9: ('CT', 'left', 'Source lymphoma: adrenal CT A/B and separate lower-abdominal CT C preserve the described extra-adrenal bowel context. The source clinical diagnosis is not a diagnosis derived from adrenal morphology alone.'),
    11: ('MRI', 'left', 'Source breast-cancer adrenal metastasis: CT A/B and MRI C–F retain haemorrhagic, enhancement and diffusion comparisons. Source diagnosis, DWI/ADC labels and local findings do not establish complete metastatic or thrombus extent.'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/adrenal-published-source-review'
    proof_path = folder / 'original-source-review.json'
    proof = json.loads(proof_path.read_text())
    images_path = ROOT / 'data/radiology/radiology-open-images.json'
    assets_path = ROOT / 'data/radiology/radiology-asset-evidence.json'
    images = json.loads(images_path.read_text())
    rows, assets, records = [], [], []
    for source in proof['figures']:
        number = source['figure_number']
        modality, side, caption = CASES[number]
        src = root / source['extracted_file']
        if sha(src) != source['sha256'] or not source['original_encoded_stream_or_decoded_sample_readback_verified']:
            raise ValueError('Original figure preservation differs')
        name = 'adrenal-pmc6349247-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-adrenal-pmc6349247-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'adrenal_source_case_fig' + str(number)
        context = {'setting': 'in_vivo', 'laterality': side, 'population': {'life_stage': 'adult'},
            'depicted_state': state, 'extent': 'local', 'selected_panels': panels,
            'panel_types': types, 'panel_states': dict.fromkeys(types, state)}
        limits = ('Complete original published figure only: no calibrated DICOM volume, independently verified acquisition timing, '
            'whole gland/limb/lesion/wall/venous extent or patient-specific 3D model. Original source labels and diagnoses remain '
            'author descriptions; no endocrine function, histological certainty or modality feature is borrowed from other panels. '
            'The 2019 paper is imaging context, not current management guidance; use the explicitly named current clinical framework. '
            'Pixel samples are preserved, but native acquired master resolution and display/ICC colour calibration are unverified.')
        credit = (proof['source_copyright'] + ' ' + ', '.join(proof['authors']) + '. ' + proof['article_title'] +
            '. DOI ' + proof['doi'] + '. CC BY 4.0. Complete original Figure ' + str(number) +
            ' preserved from the verified publication PDF without changing image samples. '
            'NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.')
        row = {'id': ident, 'kind': 'clinical-image', 'src': '/app/reference-media/radiology-open/' + name,
            'width': source['width'], 'height': source['height'], 'sha256': source['sha256'],
            'source_url': proof['source_article_url'], 'figure_url': proof['source_article_url'] + '#Fig' + str(number),
            'figure_number': number, 'asset_source_url': proof['pdf_url'], 'modality': modality,
            'clinical_panels': panels, 'image_state': state, 'source_context': context,
            'caption': caption, 'alt': caption, 'limits': limits,
            'structures_visible': ['Source-described local adrenal appearance; complete anatomical extent not approved'],
            'license': proof['license'], 'license_url': proof['license_url'], 'attribution': credit,
            'rights_reviewed_on': '2026-10-04', 'rights_review': 'Original XML grant and complete captions reviewed; separately credited Figure 10 excluded. Publisher checksums and independent PDF stream/sample readback verified.'}
        ancillary = []
        for kind in ['CT', 'Ultrasound']:
            other = [p for p, t in types.items() if t == kind and kind != modality]
            if other:
                ancillary.append({'kind': kind, 'panels': other, 'structures_visible': ['Separate source ' + kind + ' context'],
                    'limits': 'Separate modality; cannot supply MRI signal, sequence identity, independently registered geometry or a complete diagnostic assessment.'})
        if ancillary:
            row['ancillary_panels'] = ancillary
        rows.append(row)
        assets.append({'id': ident, 'kind': 'clinical_image', 'name': proof['article_title'] + ' Fig' + str(number),
            'local_path': local, 'sha256': source['sha256'], 'regions': ['abdomen'],
            'investigation_ids': ['ra.adrenal-lesions'], 'structure_ids': [], 'requirement_coverage': {},
            'modality': modality, 'source_context': context,
            'source': {'url': proof['source_article_url'], 'figure_url': row['figure_url'], 'asset_url': proof['pdf_url'],
                'license': {'name': proof['license'], 'url': proof['license_url'], 'commercial_use': True,
                    'redistribution': True, 'review_status': 'verified', 'evidence_path': str(proof_path.relative_to(ROOT)),
                    'evidence_sha256': sha(proof_path), 'attribution': credit, 'reviewed_at': '2026-10-04'}},
            'pixel_provenance': {'source_pdf_sha256': proof['pdf_sha256'], 'pdf_object_id': source['pdf_object_id'],
                'acquisition': source['acquisition'], 'decoded_pixel_sha256': source['decoded_pixel_sha256'],
                'original_encoded_stream_or_decoded_sample_readback_verified': True,
                'source_pixels_changed': False, 'highest_resolution_acquired_master_verified': False},
            'anatomical_review': {'status': 'pending', 'reason': 'Local published sections do not establish every reporting structure, full lesion geometry or independently validated clinical diagnosis.'},
            'visual_review': {'status': 'source_checked', 'sha256': source['sha256'], 'reviewed_at': '2026-10-04',
                'evidence_path': 'docs/adrenal-published-source-review.md'}})
        records.append({'figure_number': number, 'local_path': local, 'sha256': source['sha256'],
            'width': source['width'], 'height': source['height'], 'repository_dimensions': source['repository_dimensions'],
            'modality': modality, 'clinical_panels': panels, 'source_panel_types': types,
            'source_pixels_changed': False})
    ids = {r['id'] for r in rows}
    images['ra.adrenal-lesions'] = [r for r in images.get('ra.adrenal-lesions', []) if r['id'] not in ids] + rows
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
