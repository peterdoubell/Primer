#!/usr/bin/env python3
"""Attach original hernia rest/Valsalva CT comparisons without dynamic or enhancement inference."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC11449955',2): 'Complete original CT a/b versus c/d in a source-reported 58-year-old man with bilateral inguinal hernias. a is a noncontrast Valsalva source image and b its original magnified groin view. c/d are a non-Valsalva scan and magnification obtained one month later for pancreatitis. Source-described bowel/fat visibility differs, but dates/protocols are not simultaneous, independently registered or isolated pressure/reducibility evidence.',
 ('PMC11449955',3): 'Complete original CT a/b versus c/d in a source-reported 50-year-old woman after Roux-en-Y gastric bypass with bilateral femoral hernias. a/b is the noncontrast Valsalva examination; c/d is the non-Valsalva source examination three months earlier. The source describes different conspicuity and left-sided bowel protrusion; no same-session motion, complete sac/vascular geometry, reduction or viability is inferred.',
 ('PMC11449955',4): 'Complete original CT a/b versus c/d in a source-reported 40-year-old man with diastasis recti. Noncontrast Valsalva a/b shows source-described midline widening/bulging; non-Valsalva c/d was acquired two months earlier for another clinical question. Reported inter-rectus distances of 64 mm and 36 mm are caption measurements, not independently calibrated geometry. Diastasis context does not automatically supply a true fascial hernia defect or exclude a coexistent hernia.',
}
OBSERVATIONS = {
 ('PMC11449955',2): ['Source bilateral groin hernia/content observations and original same-scan magnifications'],
 ('PMC11449955',3): ['Source femoral/groin interfaces and reported left bowel protrusion, with original magnifications'],
 ('PMC11449955',4): ['Source midline/rectus separation and bulging observations; true defect geometry not granted'],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/hernia-valsalva-published-source-review'
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
        name = 'hernia-valsalva-' + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-hernia-valsalva-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'source_diastasis_recti' if number==4 else 'hernia_valsalva_source_'+pmc.lower()+'_fig'+str(number)
        context = {'setting': 'in_vivo', 'laterality': side, 'population': {'life_stage': 'not_reported'},
            'depicted_state': state, 'extent': 'local', 'selected_panels': panels,
            'panel_types': types, 'panel_states': dict.fromkeys(types, state)}
        context.update({'independent_patient_identity_verified':False,'native_acquisition_registration_or_dynamic_source_verified':False,
            'source_reported_scan_relationship':'same source patient; different dated examinations',
            'same_session_comparison':False,'source_noncontrast_Valsalva_panels':['a','b'],
            'source_nonValsalva_panels':['c','d'],'source_nonValsalva_contrast_protocol_independently_verified':False,
            'source_magnified_view_pairs':{'b':'a','d':'c'},'magnifications_are_not_independent_acquisitions':True,
            'enhancement_or_viability_evidence_granted':False,'reducibility_or_pressure_causality_verified':False})
        context['population']={'life_stage':'adult','age_years':{2:58,3:50,4:40}[number],'sex':'female' if number==3 else 'male'}
        context['source_nonValsalva_relative_date']={2:'one month after Valsalva',3:'three months before Valsalva',4:'two months before Valsalva'}[number]
        context['reported_case_group']=pmc+'-figure-'+str(number)
        if number==3:context['source_prior_Roux_en_Y_reported']=True
        if number==4:
            context['depicted_state']='source_diastasis_recti';context['panel_states']=dict.fromkeys(types,'source_diastasis_recti')
            context['source_reported_interrectus_distances_mm']={'Valsalva':64,'nonValsalva':36}
            context['independent_caliper_calibration_verified']=False
            context['true_fascial_defect_geometry_granted']=False
        if not types:
            for k in ['selected_panels', 'panel_types', 'panel_states']:
                context.pop(k)
        limits = ('Complete published CT artwork only: no calibrated DICOM series, independent rest/strain registration, continuous motion/reducibility or complete defect/sac/content/mesh/vascular geometry. '
            'The source Valsalva protocol was noncontrast; it cannot supply contrast enhancement or complete viability evidence. Non-Valsalva clinical protocols varied, and these paired examinations were months apart, not a same-session pressure experiment. '
            'Source magnified panels repeat the respective scan context, not new acquisitions. Source diagnoses/dimensions remain author descriptions; no clinical incarceration, physiological tolerance, operative outcome or independent causal pressure response is proved. '
            'Original grayscale samples and labels are retained; highest-resolution acquired masters and display calibration remain unverified.')
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
            'anatomical_review': {'status': 'pending', 'reason': 'Published bowel trauma views do not establish every wall/branch/compartment interface, full injury extent or independently validated diagnosis.'},
            'visual_review': {'status': 'source_checked', 'sha256': source['sha256'], 'reviewed_at': '2026-10-05',
                'evidence_path': 'docs/hernia-valsalva-published-source-review.md'}})
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
