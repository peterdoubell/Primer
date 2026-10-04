#!/usr/bin/env python3
"""Attach original vascular and bowel-wall CT examples without granting complete clinical or anatomical coverage."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC10066158',2): 'Source NOMI comparison: unenhanced CT A and enhanced CT B. High baseline wall attenuation may resemble enhancement unless the actual pair is compared; exact timing and whole-bowel viability remain unverified.',
 ('PMC10066158',3): 'Source NOMI unenhanced CT A and enhanced CT B, same stated patient as Figure 2. The author describes affected nonenhancing wall and enhancing reference wall; these sections do not independently prove histological injury or full clinical viability.',
 ('PMC10066158',4): 'Source incarcerated-hernia strangulated obstruction: unenhanced CT A, enhanced CT B and unenhanced CT C repeating A. The repeated source plane is retained and is not another acquisition or patient.',
 ('PMC10066158',5): 'Source SMA embolism: venous-phase axial CT A with author-described pneumatosis, and arterial-phase oblique sagittal CT B with an occluding embolus. Phase names are source claims; the complete embolus, distal branches and injury extent are not established by this composite.',
 ('PMC10066158',6): 'Source NOMI CT A/B with author-described paper-thin bowel wall and gas in the SMV. Contrast enhancement is stated, but exact phase timing is not specified; the images do not independently establish the cause, full bowel extent or histological necrosis.',
 ('PMC10066158',7): 'Source NOMI: venous-phase axial CT A with author-described intrahepatic portal gas and arterial-phase coronal MIP B with diffuse SMA/branch spasm. A projection does not establish every branch, native 3D geometry or a complete perfusion assessment.',
 ('PMC10066158',8): 'Source mesenteric venous thrombosis CT A–D: SMV thrombi, thickened target/halo wall, mesenteric stranding and ascites. The source reports oedema/haemorrhage through all layers but necrotic changes confined to mucosa; the CT appearance does not independently prove those histological findings or transmural necrosis.',
 ('PMC10066158',9): 'Source SMA embolism: arterial-phase coronal CT A and venous-phase CT B comparing the SMV and SMA. The smaller SMV is this source observation; a vessel-size ratio alone does not establish embolism, global perfusion or bowel viability.',
}

# Labels and phase/contrast descriptions are retained as article claims, not
# calibrated acquisition metadata. Figure 8B has no separate phase statement.
PANEL_ACQUISITION = {
 2: {'A':'unenhanced', 'B':'enhanced; phase not specified'},
 3: {'A':'unenhanced', 'B':'enhanced; phase not specified'},
 4: {'A':'unenhanced', 'B':'enhanced; phase not specified', 'C':'unenhanced; source repeats A'},
 5: {'A':'venous phase', 'B':'arterial phase'},
 6: {'A':'contrast enhanced; phase not specified', 'B':'phase not separately specified'},
 7: {'A':'venous phase', 'B':'arterial phase; coronal maximum intensity projection'},
 8: {'A':'contrast enhanced; phase not specified', 'B':'phase/contrast not separately specified', 'C':'contrast enhanced; phase not specified', 'D':'contrast enhanced; phase not specified'},
 9: {'A':'arterial phase', 'B':'venous phase'},
}



SOURCE_OBSERVATIONS = {
 2: ['Source-marked bowel wall on unenhanced A and enhanced B; matching and complete extent pending review'],
 3: ['Source-marked affected and reference small-bowel wall in A/B; complete extent pending review'],
 4: ['Source-marked affected/reference bowel wall and mesenteric stranding; complete loop geometry pending review'],
 5: ['Source-marked bowel-wall gas in A', 'Source-marked occluding SMA embolus in B; distal extent pending review'],
 6: ['Source-marked thin bowel wall in A', 'Source-marked SMV gas in B; complete venous anatomy pending review'],
 7: ['Source-marked intrahepatic portal gas in A', 'Source-marked SMA/branches in MIP B; each branch identity pending review'],
 8: ['Source-marked SMV thrombi in A', 'Source-marked thickened target/halo wall in B; histological layers not proved by CT', 'Source-marked mesenteric stranding in C', 'Source-marked ascites in D'],
 9: ['Source-marked SMA embolus in A', 'Source-labelled SMV/SMA comparison in B; complete vascular extent pending review'],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/bowel-ischaemia-published-source-review'
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
        name = ('bowel-obstruction-' if number in {2, 3, 4} else 'bowel-ischaemia-') + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        destination = ROOT / local
        if destination.exists():
            if sha(destination) != source['sha256']:
                raise ValueError('An existing source figure differs; do not overwrite')
        else:
            shutil.copyfile(src, destination)
        ident = 'open-bowel-ischaemia-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'bowel_ischaemia_source_'+pmc.lower()+'_fig'+str(number)
        context = {'setting': 'in_vivo', 'laterality': side, 'population': {'life_stage': 'not_reported'},
            'depicted_state': state, 'extent': 'local', 'selected_panels': panels,
            'panel_types': types, 'panel_states': dict.fromkeys(types, state)}
        context.update({'source_case_group': 'pmc10066158-fig2-3' if number in {2,3} else 'pmc10066158-fig'+str(number),
            'panel_acquisition_claims': PANEL_ACQUISITION[number], 'independent_acquisition_metadata_verified': False})
        if not types:
            for k in ['selected_panels', 'panel_types', 'panel_states']:
                context.pop(k)
        limits = ('Complete original published figure only: no calibrated DICOM volume, independently verified acquisition timing, '
            'whole bowel-wall/mesenteric-vessel/branch extent, independently verified perfusion or patient-specific 3D model. Original source labels and diagnoses remain '
            'author descriptions; no clinical viability, histological necrosis, complete vascular continuity or histological certainty or modality feature is borrowed from other panels. '
            'The publications are imaging context, not current management guidance; use the explicitly named current clinical framework. '
            'Pixel samples are preserved, but native acquired master resolution and display/ICC colour calibration are unverified.')
        credit = (article['copyright'] + ' ' + ', '.join(article['authors']) + '. ' + article['title'] +
            '. DOI ' + article['doi'] + '. CC BY 4.0. Complete original Figure ' + str(number) +
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
            'investigation_ids': ['ra.ct-bowel-ischaemia'], 'structure_ids': [], 'requirement_coverage': {},
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
                'evidence_path': 'docs/bowel-ischaemia-published-source-review.md'}})
        records.append({'figure_number': number, 'local_path': local, 'sha256': source['sha256'],
            'width': source['width'], 'height': source['height'], 'repository_dimensions': source['repository_dimensions'], 'pmcid': pmc, 'single_unlettered_figure': not types,
            'modality': modality, 'clinical_panels': panels, 'source_panel_types': types,
            'reuses_existing_obstruction_file': number in {2,3,4}, 'panel_acquisition_claims': PANEL_ACQUISITION[number],
            'source_case_group': context['source_case_group'],
            'source_pixels_changed': False})
    ids = {r['id'] for r in rows}
    images['ra.ct-bowel-ischaemia'] = [r for r in images.get('ra.ct-bowel-ischaemia', []) if r['id'] not in ids] + rows
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
