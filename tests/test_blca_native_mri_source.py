"""Complete source-study accounting cannot be replaced by selected, relabelled frames."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import struct

import pytest

from tools.anatomy_sources.acquire_blca_aa6p_mri import validate_selection
from tools.anatomy_sources.review_blca_aa6p_mri import explicit_vr_pixel_bytes

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'docs/bladder-native-study-review/TCGA-DK-AA6P'


@pytest.mark.parametrize('change', ['missing_series', 'other_patient', 'other_study', 'other_modality',
                                  'noncommercial', 'duplicate', 'wrong_count', 'unsafe_uid'])
def test_original_whole_study_selection_cannot_be_narrowed_or_relabelled(change):
    rows = json.loads((PROOF / 'nbia-series.json').read_text())
    if change == 'missing_series': rows.pop()
    elif change == 'other_patient': rows[0]['PatientID'] = 'other'
    elif change == 'other_study': rows[0]['StudyInstanceUID'] = '1.2.3'
    elif change == 'other_modality': rows[0]['Modality'] = 'CT'
    elif change == 'noncommercial': rows[0]['LicenseURI'] = 'https://creativecommons.org/licenses/by-nc/3.0/'
    elif change == 'duplicate': rows[0]['SeriesInstanceUID'] = rows[1]['SeriesInstanceUID']
    elif change == 'wrong_count': rows[0]['ImageCount'] += 1
    else: rows[0]['SeriesInstanceUID'] = '../../another'
    with pytest.raises(ValueError): validate_selection(rows)


def test_explicit_reader_walks_items_not_pixel_like_patterns_inside_metadata():
    preamble = bytes(128) + b'DICM'
    pixels = struct.pack('<3h', -32768, 0, 32767)
    fake_pixels = struct.pack('<HH2s2sI', 0x7fe0, 0x0010, b'OW', bytes(2), 6) + b'IGNORE'
    sequence = struct.pack('<HH2s2sI', 0x0008, 0x1110, b'SQ', bytes(2), 0xffffffff)
    sequence += struct.pack('<HHI', 0xfffe, 0xe000, len(fake_pixels)) + fake_pixels
    sequence += struct.pack('<HHI', 0xfffe, 0xe0dd, 0)
    actual = struct.pack('<HH2s2sI', 0x7fe0, 0x0010, b'OW', bytes(2), len(pixels)) + pixels
    decoded, offset = explicit_vr_pixel_bytes(preamble + sequence + actual)
    assert decoded == pixels and (preamble + sequence + actual)[offset:] == pixels
    with pytest.raises(ValueError): explicit_vr_pixel_bytes(preamble + actual[:-1])


def test_every_original_object_and_scalar_has_complete_independent_review():
    summary = json.loads(gzip.decompress((PROOF / 'native-study-review.json.gz').read_bytes()))
    acquisition = json.loads((PROOF / 'acquisition-review.json').read_text())
    assert summary['source_series'] == acquisition['source_series'] == 22
    assert summary['source_objects'] == acquisition['source_objects'] == 1359
    assert summary['source_pixel_samples'] == 107937792
    sops = set()
    for series in summary['series']:
        number = series['series_number']
        native = json.loads(gzip.decompress((PROOF / f'series-{number:04d}-review.json.gz').read_bytes()))
        receipt = json.loads((PROOF / f'series-{number:04d}-receipt.json').read_text())
        assert native['original_frame_count'] == receipt['dicom_count'] == len(native['frames'])
        assert native['archive_sha256'] == receipt['archive_sha256']
        assert sum(g['planes'] for g in native['source_grids']) == len(native['frames'])
        assert all(not g['source_direction_cosines_orthogonalized_or_repaired'] for g in native['source_grids'])
        for frame in native['frames']:
            assert frame['sop_instance_uid'] not in sops
            sops.add(frame['sop_instance_uid'])
            assert frame['pixel_samples'] == frame['rows'] * frame['columns']
            assert len(frame['pixel_int16_le_sha256']) == 64
    assert len(sops) == 1359
    for key in ['source_sampling_equals_effective_anatomical_resolution', 'same_declared_frame_proves_anatomical_timepoint_registration',
                'duplicate_diffusion_plane_identity_verified', 'ADC_physical_units_verified_from_real_world_mapping',
                'contrast_bolus_absolute_start_time_verified', 'VI_RADS_or_histological_stage_independently_assigned',
                'complete_reported_structure_geometry_verified', 'original_source_values_changed', 'clinical_approval', 'runtime_promoted']:
        assert not summary[key]


def test_complete_transport_and_browser_frame_mapping_do_not_invent_surface_models():
    transport = json.loads((PROOF / 'transport-review.json').read_text())
    assert transport['source_frames'] == 1359 and transport['source_series'] == 22
    assert transport['source_pixel_samples'] == 107937792
    assert sum(s['decoded_bytes'] for s in transport['series_transport']) == 107937792 * 2
    assert not transport['source_values_modified_interpolated_or_averaged']
    assert not transport['native_surface_models_or_segmentations_invented']
    browser = json.loads((PROOF / 'browser-native-pixel-review.json').read_text())
    assert len(browser) == 44 and len({b['series_number'] for b in browser}) == 22
    assert all(b['pageWidth'] == b['viewport'] == 390 for b in browser)
    assert all(len(b['hash']) == 64 for b in browser)
