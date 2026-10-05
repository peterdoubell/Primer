#!/usr/bin/env python3
"""Attach complete renal-trauma originals with phase, patient, reconstruction and historical-grade limits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC4376814',1): 'Two source patients: nephrographic/delayed CT a/b shows source-described contusion; c/d shows a source-described segmental infarction pattern. Delayed images are reported at eight minutes. This is not one patient or proof that every low-enhancing region has a single cause; source diagnosis, acquisition and histology remain independently unverified.',
 ('PMC4376814',2): 'Two source patients: delayed coronal CT a depicts a source-described subcapsular collection; nephrographic axial CT b depicts a source-described perirenal collection. Different views/patients cannot establish interval progression or complete source/compartment extent.',
 ('PMC4376814',3): 'Same source patient: nephrographic a and eight-minute delayed CT b show a source-marked renal cleft and adjacent haematoma. The source reports no urinary leak in this example; selected views cannot independently exclude every collecting-system injury or establish calibrated depth.',
 ('PMC4376814',4): 'Source coronal CT a and a ten-millimetre MIP b show source-described renal fragmentation, surrounding collection and vascular observations. A projection and selected views cannot prove every fragment, capsule/vessel interface, complete perfusion or current organ grade.',
 ('PMC4376814',5): 'Same source patient: nephrographic CT a and eight-minute delayed CT b depict source-marked renal clefts and urinary contrast leakage. Full collecting-system wall, leak origin/endpoints and calibrated injury geometry remain unverified.',
 ('PMC4376814',6): 'Two source patients: delayed CT a/c shows medial urinary contrast leakage; b/d are original static CT-derived volume renderings. The source describes downstream ureter opacification in b and no opacified downstream ureter in d. These rendered views do not provide a full acquired ureter/duct volume, independent disconnection proof or an interactive clinically validated 3D model.',
 ('PMC4376814',7): 'Same source patient: arterial CT a and nephrographic CT b show a source-marked contrast focus within a perirenal haematoma, described as capsular arterial bleeding with mild interval enlargement. The paired stills do not independently establish all flow, source timing, arterial branches or bleeding extent.',
 ('PMC4376814',8): 'Two source patients: CT a/b and separate DSA c depict a source-described pseudoaneurysm; CT d/e and separate DSA f depict a source-described arteriovenous fistula. CT arterial/nephrographic appearances and DSA early venous output are distinct sources. The radiographic projections cannot supply missing CT wall/depth anatomy or native dynamic acquisition.',
 ('PMC4376814',9): 'Same source patient: arterial CT a and nephrographic CT b show a source-described renal venous injury with contrast leakage visible in the later phase. Absence of the focus in a does not independently exclude bleeding; full venous wall/course and temporal correspondence remain unverified.',
 ('PMC4376814',10): 'Source arterial CT MIP a and subsequent DSA b/c depict a source-described right renal arterial dissection, followed by stenting in c. DSA post-intervention appearance is separate from CT; these stills do not supply a calibrated complete vessel wall/flow model or establish treatment causality or current management.',
 ('PMC4376814',11): 'Single source CT image with a source-marked right renal arterial contrast focus, reduced aortic calibre and reduced renal enhancement. The caption includes an a reference but no a panel label is visible in the original artwork; no label is added. Source descriptions of laceration/shock/infarction are not independent histological, physiological or complete geometry validation.',
}
OBSERVATIONS = {('PMC4376814',n):[text] for n,text in {
1:'Source-marked renal enhancement regions in two patient/phase pairs',2:'Source-marked subcapsular and perirenal collections in two patients',3:'Source-marked renal cleft and adjacent haematoma',4:'Source renal fragments, collection and vascular MIP observations',5:'Source renal clefts and delayed urinary contrast leakage',6:'Source delayed renal/urinary contrast regions a/c; b/d are static volume renderings',7:'Source contrast focus and perirenal haematoma across two phases',8:'Source CT vascular foci a/b/d/e; c/f are separate DSA projections',9:'Source renal venous-region contrast leakage and adjacent haematoma',10:'Source right renal arterial MIP observation a; b/c are separate DSA',11:'Source-marked renal arterial contrast focus and renal/aortic observations'}.items()}
PHASES = {1:{'a':'nephrographic','b':'eight-minute delayed','c':'nephrographic','d':'eight-minute delayed'},2:{'a':'delayed','b':'nephrographic'},3:{'a':'nephrographic','b':'eight-minute delayed'},4:{'a':'nephrographic MPR','b':'ten-millimetre MIP of same series'},5:{'a':'nephrographic','b':'eight-minute delayed'},6:{'a':'delayed axial CT','b':'static VRT of same patient/series as a','c':'delayed axial CT','d':'static VRT of same patient/series as c'},7:{'a':'arterial','b':'nephrographic'},8:{'a':'arterial','b':'nephrographic','c':'DSA in first patient','d':'arterial','e':'nephrographic','f':'DSA in second patient'},9:{'a':'arterial','b':'nephrographic'},10:{'a':'arterial MIP','b':'subsequent DSA before stent','c':'DSA after stent'},11:{'unlettered':'arterial'}}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/renal-trauma-published-source-review'
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
        name = 'renal-trauma-' + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-renal-trauma-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality and not (number == 6 and p in 'bd')]
        state = 'renal_trauma_source_'+pmc.lower()+'_fig'+str(number)
        context = {'setting': 'in_vivo', 'laterality': side, 'population': {'life_stage': 'not_reported'},
            'depicted_state': state, 'extent': 'local', 'selected_panels': panels,
            'panel_types': types, 'panel_states': dict.fromkeys(types, state)}
        context.update({'independent_patient_identity_verified': False, 'native_acquisition_and_registration_verified': False,
            'source_phase_or_rendering_roles': PHASES[number], 'historical_source_publication_year': 2015,
            'current_grade_reassigned': False, 'reported_case_group': pmc+'-figure-'+str(number)})
        if number in {1,6}:
            context['panel_case_groups'] = dict.fromkeys('ab','first source patient') | dict.fromkeys('cd','second source patient')
            context['multiple_reported_patients'] = True
        if number == 2:
            context['panel_case_groups'] = {'a':'first source patient','b':'second source patient'}
            context['multiple_reported_patients'] = True
        if number == 8:
            context['panel_case_groups'] = dict.fromkeys('abc','first source patient') | dict.fromkeys('def','second source patient')
            context['multiple_reported_patients'] = True
        if number == 6:
            context['static_ct_volume_rendering_panels'] = ['b','d']
            context['interactive_3d_or_complete_volume_coverage_granted'] = False
        if number in {8,10}:
            context['radiographic_panels_are_digital_subtraction_angiography'] = True
        if number == 11:
            context['caption_a_reference_without_visible_panel_label'] = True
        if not types:
            for k in ['selected_panels', 'panel_types', 'panel_states']:
                context.pop(k)
        limits = ('Complete original published artwork only: no calibrated DICOM/phase acquisition, complete organ/capsule/vessel/collecting-system wall or leak geometry, independent patient/time registration, '
            'native perfusion/viability or patient-specific 3D model. Historical diagnoses and grade labels belong to the 2015 source and are not reassigned under the current organ-specific revision. '
            'Different patients, DSA projections, post-intervention images, MIPs and static volume renderings cannot supply absent CT source anatomy, complete dynamic flow or independently validated clinical findings. '
            'Published grayscale/RGB samples and source ICC where supplied are retained; highest-resolution acquired masters and display calibration remain unverified.')
        credit = (article['copyright'] + ' ' + ', '.join(article['authors']) + '. ' + article['title'] +
            '. DOI ' + article['doi'] + '. ' + article['license'] + '. Complete original Figure ' + str(number) +
            ' preserved from the verified publication PDF without changing grayscale/RGB samples, retaining its original ICC profile where supplied. '
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
                ancillary.append({'kind': kind, 'panels': other, 'structures_visible': ['Separate source digital subtraction angiography projection'],
                    'limits': 'Separate modality; cannot supply missing CT wall/depth anatomy, native dynamic flow, independently registered geometry or a complete diagnostic assessment.'})
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
                'original_encoded_stream_or_decoded_pixel_readback_verified': True, 'original_dct_stream_sha256': source['original_dct_stream_sha256'], 'source_icc_profile_sha256': source['source_icc_profile_sha256'],
                'source_pixels_changed': False, 'highest_resolution_acquired_master_verified': False},
            'anatomical_review': {'status': 'pending', 'reason': 'Published renal views do not establish every organ/vessel/duct wall, complete injury extent or independently validated current diagnosis/grade.'},
            'visual_review': {'status': 'source_checked', 'sha256': source['sha256'], 'reviewed_at': '2026-10-05',
                'evidence_path': 'docs/renal-trauma-published-source-review.md'}})
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
