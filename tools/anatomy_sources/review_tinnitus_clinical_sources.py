#!/usr/bin/env python3
"""Review original tinnitus clinical figures; preserve missing case and timing facts."""
import argparse
import hashlib
import json
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image
from tools.anatomy_sources.review_trigeminal_published_sources import review

IDENT = 'PMC5263210'
# Original pages and complete image objects were inspected, including both figures
# sharing pages 7 and 8. Object order alone does not establish this binding.
BINDINGS = {'Fig1': (44, 4), 'Fig2': (59, 5), 'Fig3': (71, 6),
            'Fig4': (76, 7), 'Fig5': (77, 7), 'Fig6': (81, 8), 'Fig7': (82, 8)}
PANELS = {
    '1': [('r1c1', 'MRI', 'T2-weighted', 'Plane not specified in caption'),
          ('r1c2', 'MRI', 'Phase-contrast MRA', 'Projection not specified in caption')],
    '2': [('r1c1', 'CT', '4D-CTA lateral subtracted MIP', 'Lateral projection'),
          ('r1c2', 'CT', 'Color-coded processed 4D-CTA reformat', 'Projection not specified in caption'),
          ('r1c3', 'Radiography', 'DSA; selective external carotid injection', 'Projection not specified in caption')],
    '3': [('r1c1', 'CT', 'Thin-sliced CT', 'Plane not specified in caption'),
          ('r1c2', 'CT', 'Thin-sliced CT', 'Plane not specified in caption')],
    '4': [('r1c1', 'CT', 'CT', 'Axial'),
          ('r1c2', 'MRI', 'Contrast-enhanced T1-weighted with fat suppression', 'Axial')],
    '5': [('r1c1', 'CT', 'CT', 'Plane not specified in caption'),
          ('r1c2', 'MRI', 'T1-weighted', 'Axial'),
          ('r1c3', 'MRI', 'Contrast-enhanced T1-weighted with fat suppression', 'Axial')],
    '6': [('r1c1', 'CT', 'Thin-sliced CT: source fenestral otosclerosis example', 'Axial'),
          ('r1c2', 'CT', 'Thin-sliced CT: source cochlear otosclerosis example', 'Axial')],
    '7': [('r1c1', 'MRI', 'Contrast-enhanced T1-weighted', 'Axial'),
          ('r1c2', 'MRI', 'Contrast-enhanced T1-weighted', 'Axial'),
          ('r1c3', 'MRI', 'Contrast-enhanced T1-weighted', 'Axial')],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def obtain(url, path):
    http = url.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    if not path.exists():
        path.write_bytes(urllib.request.urlopen(http, timeout=60).read())
    expected = urllib.parse.parse_qs(urllib.parse.urlparse(http).query).get('md5')
    if expected and hashlib.md5(path.read_bytes()).hexdigest() != expected[0]:
        raise ValueError('Publisher original checksum differs: ' + path.name)
    return path.read_bytes()


def run(root, output):
    root.mkdir(parents=True, exist_ok=True)
    metadata_path = root / (IDENT + '.1.json')
    obtain('https://pmc-oa-opendata.s3.amazonaws.com/' + IDENT + '.1/' + metadata_path.name, metadata_path)
    metadata = json.loads(metadata_path.read_text())
    if metadata['pmcid'] != IDENT or metadata['is_retracted'] is not False:
        raise ValueError('Source identity/retraction status differs')
    xml = obtain(metadata['xml_url'], root / (IDENT + '.1.xml'))
    tree = ET.fromstring(xml)
    destination = root / IDENT
    destination.mkdir(exist_ok=True)
    obtain(metadata['pdf_url'], destination / (IDENT + '.1.pdf'))
    for url in metadata['media_urls']:
        obtain(url, destination / Path(urllib.parse.urlparse(url).path).name)
    # Complete source figures, not the small HTML JPEGs, are the output masters.
    review(root, output, ident=IDENT, selection=list(BINDINGS),
           object_ids=[v[0] for v in BINDINGS.values()], reviewed_bindings=BINDINGS)
    proof_path = output / 'original-source-review.json'
    proof = json.loads(proof_path.read_text())
    proof['article_title'] = metadata['title']
    proof['authors'] = [' '.join([n.findtext('given-names', ''), n.findtext('surname', '')])
                        for n in tree.findall('.//article-meta/contrib-group/contrib/name')]
    proof['source_copyright'] = tree.findtext('.//article-meta/permissions/copyright-statement')
    proof['source_acknowledgements'] = [' '.join(a.itertext()) for a in tree.findall('.//ack')]
    proof['color_coded_4D_CTA_contributor_credit'] = ['Rashindra Manniesing', 'Midas Meijs',
                                                    'Diagnostic Image Analysis Group (DIAG)']
    proof['figure_or_supplement_specific_rights_exceptions_found'] = False
    for node in tree.findall('.//fig') + tree.findall('.//supplementary-material'):
        if node.find('.//permissions') is not None or node.find('.//attrib') is not None:
            raise ValueError('Separate figure/supplement rights require review')
    for row in proof['figures']:
        number = str(row['figure_number'])
        with Image.open(destination / row['original_HTML_filename']) as html_image:
            row['original_HTML_width'], row['original_HTML_height'] = html_image.size
        row['PDF_master_has_more_original_samples_than_HTML'] = (
            row['width'] * row['height'] > row['original_HTML_width'] * row['original_HTML_height'])
        if not row['PDF_master_has_more_original_samples_than_HTML']:
            raise ValueError('Expected highest acquired PDF master differs')
        row['panels'] = [{'panel_id': panel, 'modality': modality, 'source_sequence_or_projection': sequence,
                          'source_caption_plane': plane} for panel, modality, sequence, plane in PANELS[number]]
        row['panel_identifiers_are_original_letters'] = False
        row['panel_identifier_convention'] = 'Unlettered original panels indexed left to right in one row; original pixels unchanged.'
        row['source_case_context'] = {
            'age_years': None, 'sex': None, 'age_and_sex_not_reported': True,
            'source_laterality': {'1': 'right', '2': 'right', '7': 'left'}.get(number),
            'laterality_not_independently_established_from_new_DICOM': True,
            'panels_established_same_patient': None,
            'figures_established_same_patient': False,
            'native_registration_or_interpanel_alignment_verified': False,
            'source_acquisition_datetime': None, 'exact_contrast_delay_seconds': None,
            'native_3D_grid_or_complete_DICOM_acquisition_available': False,
        }
        row['static_figure_is_independent_shunt_timing_flow_pressure_or_symptom_cause_proof'] = False
        row['source_visible_annotations_and_crop_retained'] = True
        row['independent_structure_verification'] = False
        row['structure_ids'] = []
        row['requirement_coverage'] = []
        if number == '2':
            row['source_processing_context'] = 'Source color-coded 4D-CTA uses early red-orange and delayed yellow-green contrast enhancement; no new processing or calibrated interval inferred.'
            row['source_case_association'] = 'Both article supplements explicitly identify the right sigmoid sinus dAVF shown in Figure 2.'
        if number == '3':
            row['source_diagnostic_limit'] = 'Source labels aberrant ICA and persistent stapedial artery. Absent foramen spinosum alone is an indirect sign and does not establish persistence in a new case.'
        if number == '6':
            row['source_diagnostic_limit'] = 'Fenestral and cochlear examples are separate source panels; no same-patient comparison, complete cochlea or stapes anatomy, or new causal attribution established.'
        if number == '7':
            row['source_caption_spelling_preserved'] = 'Meningeoma'
    proof['supplementary_source_videos'] = []
    for number in [1, 2]:
        node = tree.find('.//supplementary-material[@id="MOESM' + str(number) + '"]')
        media = node.find('media')
        filename = media.attrib['{http://www.w3.org/1999/xlink}href']
        path = destination / filename
        raw = path.read_bytes()
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-print_format', 'json', str(path)]))
        if len(probe['streams']) != 1:
            raise ValueError('Unexpected original video streams')
        s = probe['streams'][0]
        frame_times = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries',
            'frame=best_effort_timestamp_time,pkt_dts_time,pkt_duration_time,duration_time',
            '-of', 'json', str(path)]))['frames']
        if len(frame_times) != int(s['nb_frames']):
            raise ValueError('Original AVI frame timing/count differs')
        native = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
                                         '-f', 'rawvideo', '-pix_fmt', 'rgb555le', 'pipe:1'])
        frame_bytes = s['width'] * s['height'] * 2
        if s['pix_fmt'] != 'rgb555le' or len(native) != int(s['nb_frames']) * frame_bytes:
            raise ValueError('Original video precision/frame count differs')
        native_path = destination / ('video' + str(number) + '-original-decoded.rgb555le')
        if not native_path.exists():
            native_path.write_bytes(native)
        if native_path.read_bytes() != native:
            raise ValueError('Native decoded video writeback differs')
        frame_hashes = [sha(native[start:start + frame_bytes])
                        for start in range(0, len(native), frame_bytes)]
        proof['supplementary_source_videos'].append({
            'source_supplement_id': node.attrib['id'], 'source_filename': filename,
            'source_caption': ' '.join(media.find('caption').itertext()),
            'original_sha256': sha(raw), 'bytes': len(raw), 'publisher_original_MD5_verified': True,
            'source_figure_case_association': 'Fig2: right sigmoid sinus dAVF',
            'modality': 'CT' if number == 1 else 'Radiography',
            'source_display_type': 'Processed segmented inverted CT angiographic MIP sequence' if number == 1 else 'DSA projection sequence',
            'source_injection_context': '4D-CTA; exact injection dose/rate/delay not supplied' if number == 1 else 'Fig2 DSA legend supplies selective external-carotid injection; exact dose/rate/frame clock not supplied',
            'source_overlay_text_visually_observed': ['MIP Segmented', '7 of 12', 'VR: Inverted MIP', 'LAO105 CRA12'] if number == 1 else [],
            'original_encoded_frame_count': int(s['nb_frames']), 'width': s['width'], 'height': s['height'],
            'codec': s['codec_name'], 'decoded_native_pixel_format': s['pix_fmt'],
            'decoded_native_rgb555le_frame_sha256': frame_hashes,
            'decoded_native_rgb555le_complete_sequence_sha256': sha(native),
            'decoded_native_rgb555le_cache_filename': native_path.name,
            'decoded_native_rgb555le_writeback_verified': True,
            'source_encoded_channel_precision_bits': 5,
            'encoded_playback_frames_per_second': s['r_frame_rate'], 'encoded_playback_duration_seconds': s['duration'],
            'encoded_frame_presentation_and_decode_times_seconds': frame_times,
            'encoded_playback_rate_is_verified_acquisition_frame_interval': False,
            'pulse_ECG_or_sound_synchronization_supplied': False,
            'producer_native_intermodal_registration_supplied': False,
            'exact_bolus_relative_or_absolute_acquisition_clock_supplied': False,
            'original_12_display_frames_are_all_independent_acquired_timepoints_verified': False,
            'same_Fig2_source_case_per_original_captions': True,
            'source_movie_is_current_patient_evidence': False,
            'source_3D_grid_calibration_full_DICOM_or_absolute_bolus_clock_available': False,
            'new_flow_velocity_pressure_or_shunt_grade_measurement': False,
            'original_bytes_unchanged': True,
            'all_frames_visual_review_evidence_path': 'docs/tinnitus-clinical-source-review/visual-review.json',
            'runtime_promoted': False, 'structure_coverage_granted': False,
        })
    restricted_metadata_path = root / 'PMC8917066.1.json'
    obtain('https://pmc-oa-opendata.s3.amazonaws.com/PMC8917066.1/PMC8917066.1.json', restricted_metadata_path)
    restricted_metadata = json.loads(restricted_metadata_path.read_text())
    obtain(restricted_metadata['xml_url'], root / 'PMC8917066.1.xml')
    restricted = ET.fromstring((root / 'PMC8917066.1.xml').read_bytes())
    if hashlib.md5((root / 'PMC8917066.1.xml').read_bytes()).hexdigest() != urllib.parse.parse_qs(urllib.parse.urlparse(restricted_metadata['xml_url']).query)['md5'][0]:
        raise ValueError('Held source identity differs')
    proof['held_sources'] = [
        {'pmcid': 'PMC8917066', 'doi': restricted_metadata['doi'],
         'original_XML_sha256': sha((root / 'PMC8917066.1.xml').read_bytes()),
         'permissions_XML': ET.tostring(restricted.find('.//article-meta/permissions'), encoding='unicode'),
         'figure_ids_held': [f.attrib['id'] for f in restricted.findall('.//fig')],
         'commercial_reuse_grant_verified': False, 'reason': 'Original grant permits text mining and fair use; no reusable commercial image grant.',
         'restricted_figure_pixels_or_full_captions_repackaged': False},
        {'pmcid': 'PMC3719451', 'commercial_reuse_grant_verified': False,
         'reason': 'PMC OA S3 metadata returned 404; OA utility returned 404; Europe PMC fullTextXML returned 500. These retrieval failures do not establish a license.',
         'restricted_figure_pixels_or_full_captions_repackaged': False},
    ]
    proof['clinical_limits'] = [
        'Original publishing rights do not establish anatomical fidelity or clinical correctness.',
        'The complete published figures retain the publisher original field of view, annotations and encoded pixel precision; no full patient acquisition is implied.',
        'All seven figure cases have unreported age and sex; cross-figure and unconfirmed within-figure same-patient identity is not inferred.',
        'The static color-coded or MIP representations do not supply a native interactive volume or calibrated flow/pressure/bolus interval.',
        'Source lesion labels remain source context, not a classifier, histology confirmation, causal tinnitus diagnosis or treatment decision for a new patient.',
    ]
    proof_path.write_text(json.dumps(proof, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--proof-dir', type=Path, required=True)
    args = parser.parse_args()
    run(args.source_root, args.proof_dir)
