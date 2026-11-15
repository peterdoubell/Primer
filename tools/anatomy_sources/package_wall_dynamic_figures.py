#!/usr/bin/env python3
"""Attach original published 2D-plus-time wall MRI without spatial-depth or outcome inference."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC13045036',2): 'Original MRI annotation workflow: A shows an axial image within a 2D-plus-time stack, B the source manual muscle-group annotations, C/E human-review stages, and D propagated annotations. The stack axis t is time, not spatial depth. Right/left rectus and grouped lateral-muscle colours are original source labels; lateral masks do not separate external/internal oblique or transversus, and annotation workflow is not independent anatomical approval.',
 ('PMC13045036',3): 'Original paired preoperative a and postoperative b dynamic MRI examples. Patient A is shown breathing, B coughing and C performing Valsalva, each at beginning, middle and end of a source cycle. Original overlays mark right lateral muscle lime green, right rectus dark green, left rectus grey and left lateral muscle purple; original red arrows locate source-described hernias. These 18 snapshots do not supply continuous cine, spatial 3D depth, calibrated defect/mesh geometry, independent registration or proof of surgical success.'
}
OBSERVATIONS = {
 ('PMC13045036',2): ['Published axial rectus and grouped lateral-muscle overlays','Original 2D-plus-time stack and annotation workflow'],
 ('PMC13045036',3): ['Paired source preoperative/postoperative axial wall views','Right/left rectus and grouped lateral-muscle overlays','Source hernia locator arrows and sampled exercise-cycle states']
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/wall-dynamic-published-source-review'
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
        name = 'wall-dynamic-' + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-wall-dynamic-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'dynamic_wall_mri_source_'+pmc.lower()+'_fig'+str(number)
        context={'depicted_state':state,'anatomical_state':'source_annotated_wall_mri',
            'selected_panels':panels,'panel_types':types,'panel_states':dict.fromkeys(panels,state),
            'third_stack_axis':'time_not_spatial_depth','spatial_3d_model_derived':False,
            'full_cine_or_raw_masks_included':False,'independent_patient_axis_registration_verified':False,
            'lateral_groups_split_into_individual_wall_layers':False,'source_annotation_is_independent_anatomical_approval':False,
            'source_annotation_pipeline':'manual subset, human corrections, propagation, human corrections',
            'source_dataset_commercial_or_redistribution_permission_granted':False,
            'source_sequence_name_verified':False,'calibrated_defect_or_mesh_geometry_granted':False,
            'surgical_success_or_causal_motion_change_verified':False}
        if number==2:
            context['MRI_bearing_panels']=['A','B','D'];context['workflow_only_panels']=['C','E']
        else:
            context['source_case_rows']={'A':'breathing','B':'coughing','C':'Valsalva'}
            context['source_operative_stages']={'a':'preoperative','b':'postoperative'}
            context['source_cycle_samples']=['beginning','mid','end'];context['source_snapshot_count']=18
            context['individual_postoperative_intervals_verified']=False
        if not types:
            for k in ['selected_panels', 'panel_types', 'panel_states']:
                context.pop(k)
        limits = ('Complete published artwork preserves original MRI, labels, overlays and schematics. The third stack axis is time, not spatial depth; no spatial wall model or interpolated continuous cine is derived. '
            'Original annotation groups combine lateral layers rather than delineating each oblique/transversus/aponeurosis. Source annotations include propagation and expert correction, not wholly independent manual labels on every frame. '
            'Paired postoperative appearances do not establish complete mesh/fixation, viability, pressure dose, registered geometry, individual follow-up interval or surgical outcome. Named acquisition sequence and calibrated source measurements remain unverified. '
            'Article figure rights do not grant commercial use or redistribution of the restricted underlying MRI/mask datasets. Original PDF RGB samples and ICC are preserved; highest-resolution acquired masters and display calibration remain unverified.')
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
        for kind in ['Radiography']:
            other = [p for p, t in types.items() if t == kind and kind != modality]
            if other:
                ancillary.append({'kind': kind, 'panels': other, 'structures_visible': ['Separate source ' + kind + ' context'],
                    'limits': 'Separate modality; cannot supply missing CT wall/depth, phase, independently registered geometry or a complete diagnostic assessment.'})
        if not types:
            row.pop('clinical_panels')
        if ancillary:
            row['ancillary_panels'] = ancillary
        row['source_background']='white'
        rows.append(row)
        assets.append({'id': ident, 'kind': 'clinical_image', 'name': article['title'] + ' Fig' + str(number),
            'local_path': local, 'sha256': source['sha256'], 'regions': ['abdomen'],
            'investigation_ids': ['ra.abdominal-wall-hernias'], 'structure_ids': [], 'requirement_coverage': {},
            'modality': modality, 'source_context': context,
            'source': {'url': article['source_article_url'], 'figure_url': row['figure_url'], 'asset_url': article['pdf_url'],
                'license': {'name': article['license'], 'url': article['license_url'], 'commercial_use': True,
                    'redistribution': True, 'review_status': 'verified', 'evidence_path': str(proof_path.relative_to(ROOT)),
                    'evidence_sha256': sha(proof_path), 'attribution': credit, 'reviewed_at': '2026-10-05'}},
            'pixel_provenance': {'source_pdf_sha256': article['pdf_sha256'], 'pdf_object_id': source['pdf_object_id'],
                'acquisition': source['acquisition'], 'decoded_pixel_sha256': source['decoded_pixel_sha256'],
                'original_encoded_stream_or_decoded_pixel_readback_verified': True,
                'source_pixels_changed': False, 'highest_resolution_acquired_master_verified': False},
            'anatomical_review': {'status': 'pending', 'reason': 'Published dynamic wall MRI examples do not independently approve complete wall layers, defect/repair geometry, source-axis registration or clinical outcomes.'},
            'visual_review': {'status': 'source_checked', 'sha256': source['sha256'], 'reviewed_at': '2026-10-05',
                'evidence_path': 'docs/wall-dynamic-published-source-review.md'}})
        records.append({'figure_number': number, 'local_path': local, 'sha256': source['sha256'],
            'width': source['width'], 'height': source['height'], 'repository_dimensions': source['repository_dimensions'], 'pmcid': pmc, 'single_unlettered_figure': not types,
            'modality': modality, 'clinical_panels': panels, 'source_panel_types': types,
            'source_pixels_changed': False})
    ids = {r['id'] for r in rows}
    images['ra.abdominal-wall-hernias'] = [r for r in images.get('ra.abdominal-wall-hernias', []) if r['id'] not in ids] + rows
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
