#!/usr/bin/env python3
"""Attach complete tumour CT figures with original mixed-modality panels and clinical/source limits retained."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
CASES = {
 ('PMC12071709',2): 'Source CT A–D: appendicitis A/B and proximal jejunal intussusception C/D in the reported Peutz–Jeghers polyp case. These are distinct observations in one reported patient; full lead-point anatomy and histology are not independently established by the CT sections.',
 ('PMC12071709',3): 'Source CT A/B with ileocaecal intussusception, wall/lesion observation and nodes in a reported ileal adenocarcinoma case. Source attribution is retained; complete lesion, invaginated bowel/mesentery and histological extent remain unapproved.',
 ('PMC12071709',4): 'Source CT A/B with focal invagination and a source-described ileal polyp. The images do not independently establish complete polyp histology, luminal extent or clinical course.',
 ('PMC12071709',5): 'Source CT A–D with multiple source-described intestinal intussusceptions in metastatic melanoma. These views do not independently prove each lead point, every lesion or the complete metastatic distribution.',
 ('PMC12071709',6): 'Source CT A/B after positive oral contrast in the same reported patient as Figure 2. Partial invagination resolution and rectal contrast progression are source observations; this is not a protocol recommendation or proof of treatment causation.',
 ('PMC12071709',7): 'Source CT A/B after positive oral contrast in the same reported polyp patient as Figure 4. The caption reports clinical improvement; neither these sections nor oral-contrast progression independently establish safety, complete resolution or a universal management rule.',
 ('PMC12071709',9): 'Source CT A–C with intussusceptions, obstruction and source-described hepatic metastases in a melanoma context; identity with the Figure 5 patient is not established. Source figure registrations do not establish independent patients or complete disease extent.',
 ('PMC12071709',10): 'Source CT A/B showing bowel dilatation and a source-marked polyp in the same reported patient as Figures 4/7. Local views do not establish a complete stenosis or independent clinical outcome.',
 ('PMC12071709',11): 'Source CT A–C with a stenotic distal jejunal/wall region, mesenteric tissue and obstruction. The source reports histological adenocarcinoma/infiltration; the CT does not independently verify histology or microscopic invasion.',
 ('PMC12071709',12): 'Source CT A–C and operative photograph D in a reported jejunal neoplastic-stenosis context; patient identity with Figure 11 is not independently established. Positive oral contrast and operative findings are separate evidence types; the photograph cannot supply CT attenuation, complete tumour geometry or independent histology.',
 ('PMC12071709',14): 'Source CT A/B and operative photograph C in the same reported polyp patient as Figures 4/7/10. Free gas and operative necrotic/lacerated tissue remain source descriptions, not independent proof of the entire injury extent or a universal treatment sequence.',
 ('PMC12071709',15): 'Source CT A/B and MRI C–F in a reported ileocaecal NET case. Early enhancement, MRI sequence/DWI and histology claims remain source context; MRI observations cannot provide CT features, molecular grade or registered cross-modality geometry.',
 ('PMC12071709',16): 'Source CT A–C with abnormal jejunal wall/dilatation, adjacent collection and nodes. The source explicitly describes difficulty separating lymphoma from adenocarcinoma with inflammation; these CT appearances do not establish histology.',
 ('PMC12071709',18): 'Source CT A/B with hepatic lesions and ileocaecal/perivisceral observations. The source reports liver-biopsy attribution to intestinal carcinoid; the selected CT sections do not independently prove that origin or full metastatic extent.',
 ('PMC12071709',19): 'Source CT A/B and MRI C–F showing source-described hepatic lesions in an ileal NET context. MRI DWI/ADC observations remain separate from CT; additional MRI-visible lesions do not prove CT sensitivity, source registration or full staging.',
 ('PMC12071709',20): 'Source CT A/B and PET/CT C in a reported ileal NET case. The caption names a generic 68Ga-DOTA study; no unreported tracer subtype, grade or complete uptake distribution is assigned to the CT panels.',
}

SOURCE_OBSERVATIONS = {
 2:['Source-marked appendix/adjacent inflammation A/B','Source-marked jejunal invagination C/D'],
 3:['Source-marked ileocaecal invagination and wall/lesion region A/B','Source-marked lymphadenopathy'],
 4:['Source-marked invagination and polyp region A/B'],5:['Source-marked intestinal invagination regions A–D'],
 6:['Source-marked invagination region A','Source rectal oral-contrast observation B'],
 7:['Source-marked polyp/luminal contrast regions A/B'],9:['Source bowel invagination/obstruction A–C','Source-described hepatic observations'],
 10:['Source dilated bowel A','Source-marked polyp B'],11:['Source stenotic jejunal/wall region A','Source mesenteric tissue B','Source obstructed bowel C'],
 12:['Source CT stenotic bowel and mesenteric regions A–C'],14:['Source CT free-gas/complication regions A/B'],
 15:['Source CT ileocaecal/ileal and adjacent tissue observations A/B'],16:['Source jejunal wall/dilatation A/B','Source collection B','Source nodes C'],
 18:['Source hepatic observations A','Source ileocaecal/perivisceral observations B'],19:['Source CT hepatic lesions A/B'],
 20:['Source CT ileal lesion A','Source CT hepatic lesion B'],
}
CASE_GROUP={2:'reported-28m-polyp',6:'reported-28m-polyp',4:'reported-72f-polyp',7:'reported-72f-polyp',10:'reported-72f-polyp',14:'reported-72f-polyp',5:'reported-53f-melanoma',11:'reported-72m-jejunal-lesion'}



def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder = ROOT / 'docs/small-bowel-tumour-published-source-review'
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
        name = 'small-bowel-tumour-' + pmc.lower() + '-fig' + str(number) + src.suffix
        local = 'web/reference-media/radiology-open/' + name
        shutil.copyfile(src, ROOT / local)
        ident = 'open-small-bowel-tumour-' + pmc.lower() + '-fig' + str(number)
        types = source['source_panel_types']
        panels = [p for p, kind in types.items() if kind == modality]
        state = 'small_bowel_tumour_source_'+pmc.lower()+'_fig'+str(number)
        context = {'setting': 'in_vivo', 'laterality': side, 'population': {'life_stage': 'not_reported'},
            'depicted_state': state, 'extent': 'local', 'reported_case_group': CASE_GROUP.get(number, 'reported-figure-'+str(number)), 'independent_patient_identity_verified': False, 'native_phase_timing_verified': False, 'selected_panels': panels,
            'panel_types': types, 'panel_states': dict.fromkeys(types, state)}
        context['reported_case_group'] = CASE_GROUP.get(number, 'reported-figure-'+str(number))
        if not types:
            for k in ['selected_panels', 'panel_types', 'panel_states']:
                context.pop(k)
        limits = ('Complete original published figure only: no calibrated DICOM volume, independently verified acquisition timing, '
            'whole wall/lumen/lesion/fistula/mesenteric-vessel extent or patient-specific 3D model. Original source labels and diagnoses remain '
            'author descriptions; no clinical viability, histological injury depth or complete fistula continuity, histological certainty or modality feature is borrowed from other panels. '
            'The publications are imaging context, not current management guidance; use the explicitly named current clinical framework. '
            'Pixel samples are preserved, but native acquired master resolution and display/ICC colour calibration are unverified.')
        credit = (article['copyright'] + ' ' + ', '.join(article['authors']) + '. ' + article['title'] +
            '. DOI ' + article['doi'] + '. CC BY 4.0. Complete original Figure ' + str(number) +
            ' preserved from verified native PDF image samples/ICC interpretation or the original repository JPEG as recorded in source evidence; no source samples changed. '
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
        for kind in ['MRI', 'PET-CT', 'Clinical photograph']:
            other = [p for p, t in types.items() if t == kind and kind != modality]
            if other:
                ancillary.append({'kind': kind, 'panels': other, 'structures_visible': ['Separate source ' + kind + ' observations; actual panel identities are retained'],
                    'limits': 'Separate evidence type; cannot supply CT attenuation/phase, calibrated source registration, complete lesion/tract geometry or independent histology/grade.'})
        if not types:
            row.pop('clinical_panels')
        if ancillary:
            row['ancillary_panels'] = ancillary
        row['source_background']='white'
        rows.append(row)
        assets.append({'id': ident, 'kind': 'clinical_image', 'name': article['title'] + ' Fig' + str(number),
            'local_path': local, 'sha256': source['sha256'], 'regions': ['abdomen'],
            'investigation_ids': ['ra.ct-small-bowel-tumours'], 'structure_ids': [], 'requirement_coverage': {},
            'modality': modality, 'source_context': context,
            'source': {'url': article['source_article_url'], 'figure_url': row['figure_url'], 'asset_url': article['pdf_url'],
                'license': {'name': article['license'], 'url': article['license_url'], 'commercial_use': True,
                    'redistribution': True, 'review_status': 'verified', 'evidence_path': str(proof_path.relative_to(ROOT)),
                    'evidence_sha256': sha(proof_path), 'attribution': credit, 'reviewed_at': '2026-10-04'}},
            'pixel_provenance': {'source_pdf_sha256': article['pdf_sha256'], 'pdf_object_id': source['pdf_object_id'], 'pdf_components': source['pdf_components'],
                'acquisition': source['acquisition'], 'decoded_pixel_sha256': source['decoded_pixel_sha256'],
                'original_encoded_stream_or_decoded_pixel_readback_verified': True,
                'source_pixels_changed': False, 'highest_resolution_acquired_master_verified': False},
            'anatomical_review': {'status': 'pending', 'reason': 'Local published sections do not establish every reporting structure, full lesion geometry or independently validated clinical diagnosis.'},
            'visual_review': {'status': 'source_checked', 'sha256': source['sha256'], 'reviewed_at': '2026-10-04',
                'evidence_path': 'docs/small-bowel-tumour-published-source-review.md'}})
        records.append({'figure_number': number, 'local_path': local, 'sha256': source['sha256'],
            'width': source['width'], 'height': source['height'], 'repository_dimensions': source['repository_dimensions'], 'pmcid': pmc, 'single_unlettered_figure': not types,
            'modality': modality, 'clinical_panels': panels, 'source_panel_types': types,
            'source_pixels_changed': False})
    ids = {r['id'] for r in rows}
    images['ra.ct-small-bowel-tumours'] = [r for r in images.get('ra.ct-small-bowel-tumours', []) if r['id'] not in ids] + rows
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
