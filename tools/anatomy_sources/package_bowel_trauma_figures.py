#!/usr/bin/env python3
"""Attach complete original bowel/mesenteric trauma CT examples with source and compartment limits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC6780049',1): 'Complete original CT A/B showing source-marked extraluminal gas and a local gas/fluid observation. The selected source caption does not establish same-patient identity, exact phase, a complete wall defect/tract, every gas compartment or the full injury source. Gas alone is not independent proof of complete perforation geometry.',
 ('PMC6780049',2): 'Complete original CT A/B with source-described thickened/hyperaemic fluid-filled bowel in A and intraperitoneal/retroperitoneal fluid in B. The caption suggests possible bowel/mesenteric injury; these appearances do not independently establish its cause, full wall layers, perfusion/viability or every injured organ. Same-patient and phase correspondence are not established.',
 ('PMC6780049',3): 'Complete original contrast-enhanced CT A/B: the caption describes a focal mesenteric haematoma/pseudoaneurysm in A and mesenteric extravasation/infiltration in B. Exact phases, same-patient correspondence and complete vessel/branch/wall geometry are not established from the selected artwork. The source diagnoses are not independent dynamic flow or viability proof.',
 ('PMC7676803',1): 'Complete original unlettered coronal-left/axial-right CT pair in a reported delayed ascending-colon obstruction case. The source body describes an intramural collection while its caption says intraluminal; the compartment discrepancy remains unresolved. Original displayed calipers and reported 10.1 x 5.9 x 7.2 cm dimensions are retained as source measurements, not independently calibrated geometry. No initial CT was reported at the first visit two weeks earlier, so this is not a matched negative-to-positive CT comparison. No A/B letters are added to the unlettered artwork.',
}
OBSERVATIONS = {
 ('PMC6780049',1): ['Source-marked local extraluminal gas/fluid regions'],
 ('PMC6780049',2): ['Source bowel-wall/lumen observations and local fluid compartments'],
 ('PMC6780049',3): ['Source mesenteric contrast focus, adjacent haematoma and infiltration'],
 ('PMC7676803',1): ['Source ascending-colon-region collection/lumen observations and original displayed calipers; intramural/intraluminal correspondence unresolved'],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/bowel-trauma-published-source-review'
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
        name = 'bowel-trauma-' + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-bowel-trauma-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'bowel_trauma_source_'+pmc.lower()+'_fig'+str(number)
        context = {'setting': 'in_vivo', 'laterality': side, 'population': {'life_stage': 'not_reported'},
            'depicted_state': state, 'extent': 'local', 'selected_panels': panels,
            'panel_types': types, 'panel_states': dict.fromkeys(types, state)}
        context.update({'independent_patient_identity_verified': False, 'native_acquisition_phase_and_registration_verified': False,
            'source_case_relationship_verified': False, 'source_phase_specified': False})
        if pmc == 'PMC6780049':
            context['repeated_pdf_artwork_is_not_independent_case_evidence'] = True
            context['same_patient_between_panels_not_established'] = True
        else:
            context['reported_case_group'] = pmc+'-delayed-colonic-case'
            context['source_caption_compartment_claim'] = 'intraluminal'
            context['source_body_compartment_claim'] = 'intramural'
            context['source_compartment_claims_unresolved'] = True
            context['initial_ct_at_first_visit_reported'] = False
            context['source_reported_trauma_interval'] = 'two weeks'
            context['source_caliper_calibration_independently_verified'] = False
            context['source_caption_A_B_roles_without_visible_letters'] = True
            context['actual_unlettered_view_roles'] = {'left':'coronal','right':'axial'}
        if not types:
            for k in ['selected_panels', 'panel_types', 'panel_states']:
                context.pop(k)
        limits = ('Complete original published CT artwork only: no calibrated DICOM acquisition, independently verified phase/time/patient registration, full bowel/mesenteric/vessel/compartment wall or injury extent, '
            'native perfusion/viability, biological cause or patient-specific 3D model. Source observations and diagnoses remain author descriptions; unknown same-case relationships and unresolved compartment claims cannot be silently completed. '
            'Original calipers do not independently calibrate full geometry, and unavailable early imaging is not a negative baseline. The publications provide imaging examples, not current management guidance or permission to delay clinical assessment. '
            'Published RGB samples are preserved; highest-resolution acquired masters and display calibration remain unverified.')
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
            'investigation_ids': ['ra.ct-abdominal-trauma'], 'structure_ids': [], 'requirement_coverage': {},
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
                'evidence_path': 'docs/bowel-trauma-published-source-review.md'}})
        records.append({'figure_number': number, 'local_path': local, 'sha256': source['sha256'],
            'width': source['width'], 'height': source['height'], 'repository_dimensions': source['repository_dimensions'], 'pmcid': pmc, 'single_unlettered_figure': not types,
            'modality': modality, 'clinical_panels': panels, 'source_panel_types': types,
            'source_pixels_changed': False})
    ids = {r['id'] for r in rows}
    images['ra.ct-abdominal-trauma'] = [r for r in images.get('ra.ct-abdominal-trauma', []) if r['id'] not in ids] + rows
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
