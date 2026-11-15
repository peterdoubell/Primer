import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def proof():
    return json.loads((ROOT / 'docs/tinnitus-clinical-source-review/original-source-review.json').read_text())


def test_complete_original_tinnitus_masters_keep_licence_case_and_panel_boundaries():
    p = proof()
    assert p['pmcid'] == 'PMC5263210' and p['doi'] == '10.1007/s40134-017-0199-7'
    assert p['original_article_grant'] == 'CC BY 4.0' and p['publisher_original_MD5_checks_passed']
    assert p['authors'] == ['Sjoert A. H. Pegge', 'Stefan C. A. Steens', 'Henricus P. M. Kunst', 'Frederick J. A. Meijer']
    assert p['color_coded_4D_CTA_contributor_credit'] == ['Rashindra Manniesing', 'Midas Meijs', 'Diagnostic Image Analysis Group (DIAG)']
    assert [(f['figure_number'], f['source_PDF_object'], f['source_PDF_page'], f['width'], f['height']) for f in p['figures']] == [
        (1, 44, 4, 1500, 911), (2, 59, 5, 2031, 670), (3, 71, 6, 1500, 792),
        (4, 76, 7, 1500, 909), (5, 77, 7, 2031, 898), (6, 81, 8, 1500, 867), (7, 82, 8, 2031, 1053)]
    for f in p['figures']:
        c = f['source_case_context']
        assert c['age_years'] is None and c['sex'] is None and c['age_and_sex_not_reported']
        assert c['panels_established_same_patient'] is None and not c['figures_established_same_patient']
        assert c['exact_contrast_delay_seconds'] is None and not c['native_registration_or_interpanel_alignment_verified']
        assert f['explicit_original_PDF_page_binding_visually_reviewed'] and f['original_decoded_samples_and_ICC_preserved']
        assert f['PDF_master_has_more_original_samples_than_HTML']
        assert f['width'] * f['height'] > f['original_HTML_width'] * f['original_HTML_height']
        assert not f['source_pixels_resampled_or_enhanced'] and not f['panel_identifiers_are_original_letters']
        assert not f['static_figure_is_independent_shunt_timing_flow_pressure_or_symptom_cause_proof']
        assert f['structure_ids'] == [] and f['requirement_coverage'] == [] and not f['independent_structure_verification']
    assert p['figures'][1]['original_HTML_and_PDF_encoded_contrast_differ']
    assert p['figures'][1]['numbered_HTML_PDF_thumbnail_RGB_RMS'] > 5
    assert [x['modality'] for x in p['figures'][1]['panels']] == ['CT', 'CT', 'Radiography']
    assert [x['modality'] for x in p['figures'][3]['panels']] == ['CT', 'MRI']
    assert [x['modality'] for x in p['figures'][4]['panels']] == ['CT', 'MRI', 'MRI']
    assert p['figures'][6]['source_caption_spelling_preserved'] == 'Meningeoma'
    assert not p['runtime_promoted'] and not p['structure_coverage_granted']


def test_original_fistula_videos_preserve_precision_and_do_not_invent_acquisition_timing():
    p = proof()
    assert len(p['supplementary_source_videos']) == 2
    for v in p['supplementary_source_videos']:
        assert v['original_bytes_unchanged'] and v['publisher_original_MD5_verified']
        assert (v['width'], v['height'], v['original_encoded_frame_count']) == (1024, 1024, 12)
        assert v['encoded_playback_frames_per_second'] == '3/1' and v['encoded_playback_duration_seconds'] == '4.000000'
        assert v['decoded_native_pixel_format'] == 'rgb555le' and v['source_encoded_channel_precision_bits'] == 5
        assert len(v['decoded_native_rgb555le_frame_sha256']) == 12
        assert all(len(h) == 64 for h in v['decoded_native_rgb555le_frame_sha256'])
        assert not v['encoded_playback_rate_is_verified_acquisition_frame_interval']
        assert not v['pulse_ECG_or_sound_synchronization_supplied']
        assert not v['exact_bolus_relative_or_absolute_acquisition_clock_supplied']
        assert not v['producer_native_intermodal_registration_supplied']
        assert not v['source_movie_is_current_patient_evidence']
        assert v['same_Fig2_source_case_per_original_captions']
        times = v['encoded_frame_presentation_and_decode_times_seconds']
        assert len(times) == 12 and times[0]['best_effort_timestamp_time'] == '0.000000'
        assert times[-1]['best_effort_timestamp_time'] == '3.666667'
        assert all(t['duration_time'] == '0.333333' for t in times)
        assert not v['new_flow_velocity_pressure_or_shunt_grade_measurement']
        assert not v['runtime_promoted'] and not v['structure_coverage_granted']
    assert [v['modality'] for v in p['supplementary_source_videos']] == ['CT', 'Radiography']
    assert 'VR: Inverted MIP' in p['supplementary_source_videos'][0]['source_overlay_text_visually_observed']
    held = {v['pmcid']: v for v in p['held_sources']}
    assert held['PMC8917066']['figure_ids_held'] == ['F1', 'F2', 'F3', 'F4', 'F5']
    assert 'text mining' in held['PMC8917066']['permissions_XML']
    assert all(not v['commercial_reuse_grant_verified'] and not v['restricted_figure_pixels_or_full_captions_repackaged'] for v in held.values())


def test_visual_review_binds_current_source_proof_and_every_original_video_frame():
    directory = ROOT / 'docs/tinnitus-clinical-source-review'
    v = json.loads((directory / 'visual-review.json').read_text())
    assert v['original_source_review_sha256'] == hashlib.sha256((directory / 'original-source-review.json').read_bytes()).hexdigest()
    assert v['all_seven_original_masters_and_PDF_pages_visually_inspected']
    assert v['source_PDF_pages_inspected'] == [4, 5, 6, 7, 8]
    assert v['figure2_encoded_contrast_difference_retained']
    assert not v['independent_anatomical_review_complete'] and not v['native_registration_verified']
    assert not v['runtime_promoted'] and not v['structure_coverage_granted']
    for movie in v['source_videos']:
        assert movie['all_12_source_frames_visually_reviewed_in_order']
        assert not movie['original_AVI_samples_or_timing_changed']
        assert movie['display_frame_samples_verified_against_complete_ffmpeg_RGB24_decode']
        assert [f['encoded_index_1_based'] for f in movie['frames']] == list(range(1, 13))
        assert all(f['RGB24_writeback_samples_verified'] for f in movie['frames'])
