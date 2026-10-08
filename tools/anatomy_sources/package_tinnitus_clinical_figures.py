#!/usr/bin/env python3
"""Build reviewed tinnitus figure records; shared registries change only with --apply."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[2]
INV = 'ra.tinnitus'
PREFIX = 'open-tinnitus-pmc5263210-fig'
URL = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC5263210/'
PRIMARY = {1: 'MRI', 2: 'CT', 3: 'CT', 4: 'MRI', 5: 'MRI', 6: 'CT', 7: 'MRI'}
STEP_FIGURES = {1: [7], 2: [3, 4, 5, 6], 3: [1, 2, 3]}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build_records(source):
    proof_path = ROOT / 'docs/tinnitus-clinical-source-review/original-source-review.json'
    proof = json.loads(proof_path.read_text())
    visual_path = proof_path.parent / 'visual-review.json'
    visual = json.loads(visual_path.read_text())
    if (proof['pmcid'] != 'PMC5263210' or proof['original_article_grant'] != 'CC BY 4.0'
            or not proof['publisher_original_MD5_checks_passed']
            or proof['figure_or_supplement_specific_rights_exceptions_found']
            or not visual['all_seven_original_masters_and_PDF_pages_visually_inspected']
            or visual['original_source_review_sha256'] != sha(proof_path.read_bytes())):
        raise ValueError('Reviewed original source rights/layout proof differs')
    if {f['figure_number'] for f in proof['figures']} != set(range(1, 8)):
        raise ValueError('All seven reviewed complete figures required')
    rows, assets, files = [], [], []
    for figure in proof['figures']:
        n = figure['figure_number']
        identifier = PREFIX + str(n)
        path = source / 'PMC5263210/original-PDF-masters' / figure['source_master_filename']
        raw = path.read_bytes()
        if sha(raw) != figure['source_master_sha256']:
            raise ValueError('Original source figure bytes differ')
        with Image.open(path) as im:
            im.load()
            pixels, profile = im.tobytes(), im.info.get('icc_profile')
            if (im.size != (figure['width'], figure['height']) or im.mode != figure['pixel_mode']
                    or sha(pixels) != figure['decoded_pixel_sha256']
                    or (sha(profile) if profile else None) != figure['source_ICC_sha256']):
                raise ValueError('Original decoded samples, dimensions or ICC differ')
        modality = PRIMARY[n]
        types = {p['panel_id']: p['modality'] for p in figure['panels']}
        selected = [p for p, kind in types.items() if kind == modality]
        state = 'source_tinnitus_selected_pathology_example'
        case = figure['source_case_context']
        context = {
            'setting': 'in_vivo', 'laterality': case['source_laterality'] or 'not_reported',
            'population': {'life_stage': 'not_reported'}, 'extent': 'local', 'depicted_state': state,
            'selected_panels': selected, 'panel_types': types,
            'panel_states': {p: state for p in types},
            'panel_identifier_scheme': 'grid_unlettered', 'panel_grid_rows': 1, 'panel_grid_columns': len(types),
            'source_panel_acquisitions': {p['panel_id']: {'sequence_or_projection': p['source_sequence_or_projection'],
                                                        'caption_plane': p['source_caption_plane']} for p in figure['panels']},
            # Separate panel groups deliberately make no unverified patient match.
            'source_case_groups': {'source_figure_' + str(n) + '_panel_' + p: [p] for p in types},
            'source_age_and_sex_not_reported': True,
            'different_figures_assumed_same_patient': False,
            'source_panels_assumed_same_patient': False,
            'source_panels_independently_registered': False,
            'native_orientation_or_full_anatomical_extent_verified': False,
            'exact_contrast_delay_seconds_supplied': False,
            'static_figure_establishes_calibrated_flow_pressure_or_symptom_cause': False,
            'original_published_lesion_label_is_new_histology_or_diagnostic_classifier': False,
            'source_HTML_PDF_encoded_contrast_difference_preserved': figure['original_HTML_and_PDF_encoded_contrast_differ'],
        }
        if n == 2:
            context.update(source_fig2_case_also_identified_in_original_supplement_captions=True,
                           color_coded_reformat_is_native_3D_or_new_transit_measurement=False,
                           original_supplement_videos_are_displayed_by_this_static_record=False)
        if n == 6:
            context['fenestral_and_cochlear_examples_established_same_patient'] = False
        specific = {
            1: 'T2-weighted and phase-contrast MRA source views of the right temporal AVM; no calibrated velocity, complete feeder/nidus/drainage map or causal diagnosis is supplied.',
            2: 'Source right sigmoid sinus dAVF. CT panels are the lateral subtracted 4D-CTA MIP and processed color-coded 4D-CTA reformat; the DSA panel is selective external-carotid injection. These static panels do not expose the full source videos, calibrated transit clock, pressure or complete reflux grading.',
            3: 'Source thin-sliced CT labels aberrant ICA and persistent stapedial artery. Absent foramen spinosum alone is an indirect sign and cannot establish the variant in a new patient.',
            4: 'Separate axial CT and axial contrast-enhanced fat-suppressed T1 MRI source views of glomus tympanicum; enhancement alone is not histology or tinnitus causation.',
            5: 'Separate CT, axial T1 and axial contrast-enhanced fat-suppressed T1 source views of glomus jugulotympanicum. Source flow-void terminology is retained without inventing a functional flow measurement.',
            6: 'Distinct fenestral and cochlear otosclerosis CT examples; no same-patient comparison, complete otic anatomy or causal symptom attribution is established.',
            7: 'Source left cerebellopontine-angle "Meningeoma" with labelled hypoglossal canal, jugular plate and middle-ear extension. Source spelling and labels are retained; no new histology or symptom causation is established.',
        }[n]
        limits = specific + ' Age, sex, acquisition date and exact contrast delay are not supplied. Complete published figure only: no full native acquisition, matched patient 3D, every fine nerve/ossicle/labyrinth/wall/interface or physiological function is established.'
        attribution = (', '.join(proof['authors']) + '. ' + proof['article_title'] + '. DOI ' + proof['doi']
                       + '. Figure ' + str(n) + '. CC BY 4.0. Original complete PDF decoded samples and embedded ICC retained without enhancement, resampling or relabelling. '
                       + ('Color-coded 4D-CTA reformat: Rashindra Manniesing and Midas Meijs, Diagnostic Image Analysis Group (DIAG). ' if n == 2 else '')
                       + 'No endorsement implied.')
        local = f'web/reference-media/radiology-open/tinnitus-pmc5263210-fig{n}.png'
        row = {
            'id': identifier, 'kind': 'clinical-image', 'modality': modality, 'figure_number': n,
            'src': '/app/' + local.removeprefix('web/'), 'sha256': sha(raw), 'width': figure['width'], 'height': figure['height'],
            'source_url': URL, 'figure_url': URL + '#Fig' + str(n),
            'asset_source_url': 'https://pmc-oa-opendata.s3.amazonaws.com/PMC5263210.1/PMC5263210.1.pdf',
            'clinical_panels': selected, 'panel_identifier_scheme': 'grid_unlettered', 'source_context': context,
            'image_state': state, 'caption': 'Source Figure ' + str(n) + ': ' + figure['source_caption_full'].split('.')[0] + '.',
            'alt': 'Complete published tinnitus source Figure ' + str(n) + '. ' + specific,
            'limits': limits, 'source_caption_full': figure['source_caption_full'],
            'structures_visible': ['Source-local selected lesion and adjacent anatomy; complete native boundaries remain unapproved'],
            'license': proof['original_article_grant'], 'license_url': proof['license_url'], 'attribution': attribution,
            'rights_reviewed_on': '2026-10-08',
            'rights_review': 'Original explicit CC BY 4.0; complete PDF page/caption/master layout and samples reviewed; source acknowledgement credit retained. No figure-specific restrictive grant found.',
        }
        extras = {kind: [p for p, role in types.items() if role == kind]
                  for kind in dict.fromkeys(types.values()) if kind != modality}
        if extras:
            row['ancillary_panels'] = [
                {'kind': kind, 'panels': panels,
                 'structures_visible': ['Separate source ' + ('DSA projection' if kind == 'Radiography' else kind) + ' context'],
                 'limits': 'Separate source acquisition; no native registration, borrowed signal, independent tissue identity, calibrated flow/pressure or new symptom-cause proof.'}
                for kind, panels in extras.items()]
        catalog._validate_source_panel_roles(row)
        rows.append(row)
        assets.append({
            'id': identifier, 'kind': 'clinical_image', 'name': 'Original tinnitus source Figure ' + str(n),
            'local_path': local, 'sha256': sha(raw), 'modality': modality, 'investigation_ids': [INV],
            'structure_ids': [], 'requirement_coverage': {}, 'source_context': context,
            'source': {'url': URL, 'figure_url': row['figure_url'], 'asset_url': row['asset_source_url'],
                       'license': {'name': proof['original_article_grant'], 'url': proof['license_url'],
                                   'commercial_use': True, 'redistribution': True, 'review_status': 'verified',
                                   'evidence_path': str(proof_path.relative_to(ROOT)), 'evidence_sha256': sha(proof_path.read_bytes()),
                                   'attribution': attribution, 'reviewed_at': '2026-10-08'}},
            'pixel_provenance': {'source_pixels_changed': False, 'decoded_pixel_sha256': sha(pixels),
                                 'original_source_ICC_preserved': bool(profile), 'source_PDF_object': figure['source_PDF_object'],
                                 'highest_resolution_acquired_master_verified': True,
                                 'HTML_PDF_encoded_contrast_difference_preserved': figure['original_HTML_and_PDF_encoded_contrast_differ']},
            'anatomical_review': {'status': 'pending', 'reason': 'Complete published selected examples do not establish all fine native tissue/wall/nerve/lesion interfaces, registration, vascular transit or causal diagnosis.'},
            'visual_review': {'status': 'source_checked', 'sha256': sha(raw),
                              'evidence_path': str(visual_path.relative_to(ROOT)), 'reviewed_at': '2026-10-08'},
        })
        files.append((local, raw))
    return rows, assets, files


def apply_records(source):
    rows, assets, files = build_records(source)
    archive = ROOT / 'docs/tinnitus-clinical-source-review/packaged-source-images.json'
    open_path = ROOT / 'data/radiology/radiology-open-images.json'
    scoped_path = ROOT / 'data/radiology/investigation-source-images.json'
    old_open = json.loads(open_path.read_text())
    old_scoped = json.loads(scoped_path.read_text())
    replaced = (json.loads(archive.read_text())['replaced_investigation_images'] if archive.exists()
                else catalog.detail(Curriculum(), catalog.resolve(INV))['radiology_reference']['key_images'])
    original_scoped = (json.loads(archive.read_text())['replaced_scoped_source_images'] if archive.exists()
                       else old_scoped.get(INV, []))
    for local, raw in files:
        (ROOT / local).write_bytes(raw)
    old_open[INV] = [r for r in old_open.get(INV, []) if not r['id'].startswith(PREFIX)] + rows
    open_path.write_text(json.dumps(old_open, indent=2, ensure_ascii=False) + '\n')
    append_evidence(ROOT / 'data/radiology/radiology-asset-evidence.json', assets, prefix=PREFIX)
    override_path = ROOT / 'data/radiology/investigation-overrides-non-msk.json'
    overrides = json.loads(override_path.read_text())
    overrides[INV]['key_images'] = []
    override_path.write_text(json.dumps(overrides, indent=2) + '\n')
    text = scoped_path.read_text()
    if '"' + INV + '"' in text:
        start = text.index('[', text.index('"' + INV + '"'))
        _, end = json.JSONDecoder().raw_decode(text, start)
        scoped_path.write_text(text[:start] + '[]' + text[end:])
    steps_path = ROOT / 'data/radiology/reporting-steps/head-neck.json'
    text = steps_path.read_text()
    start = text.index('{', text.index('"' + INV + '"'))
    node, end = json.JSONDecoder().raw_decode(text, start)
    old_ids = {r['id'] for r in replaced}
    node['start'] = {'images': [], 'module_illustrations': False}
    for step in node['steps']:
        step['images'] = [i for i in step.get('images', []) if i not in old_ids and not i.startswith(PREFIX)]
    for index, figures in STEP_FIGURES.items():
        node['steps'][index]['images'] = list(dict.fromkeys(node['steps'][index]['images'] + [PREFIX + str(n) for n in figures]))
    steps_path.write_text(text[:start] + json.dumps(node, indent=2, ensure_ascii=False).replace('\n', '\n    ') + text[end:])
    archive.write_text(json.dumps({'replaced_investigation_images': replaced, 'replaced_scoped_source_images': original_scoped,
                                  'published_figure_ids': [r['id'] for r in rows],
                                  'clinical_approval': False, 'structure_coverage_granted': False}, indent=2) + '\n')
    for value in vars(catalog).values():
        if callable(getattr(value, 'cache_clear', None)):
            value.cache_clear()
    reference = catalog.detail(Curriculum(), catalog.resolve(INV))['radiology_reference']
    requirements_path = ROOT / 'data/radiology/non-msk-structure-requirements.json'
    requirements = json.loads(requirements_path.read_text())
    for item in requirements['investigations']:
        if item['investigation_id'] == INV:
            item['source_contract_sha256'] = digest({k: reference.get(k) for k in ['reporting', 'report_templates', 'walkthrough', 'reading']})
    requirements_path.write_text(json.dumps(requirements, indent=2) + '\n')
    print('Seven source figures applied; source videos and full anatomical coverage remain separate/pending')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.apply:
        apply_records(args.source_root)
    else:
        records, _, _ = build_records(args.source_root)
        print('Validated seven original source figures; no shared files changed:', [r['id'] for r in records])
