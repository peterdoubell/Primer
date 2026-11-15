"""Source-order and metadata-disclosure boundaries for the offline MRI audit."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

np = pytest.importorskip('numpy')
pydicom = pytest.importorskip('pydicom')

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'leeds_knee_imaging', ROOT / 'tools/anatomy_sources/audit_leeds_knee_imaging.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def native_frames():
    # Column direction +P and row direction -S produce a -L cross-normal.
    # The acquired source's frame order advances +L, opposite that normal.
    return [{'ipp_mm': [.7 * k, 0, 0], 'iop': [0, 1, 0, 0, 0, -1],
             'in_stack_position': k + 1, 'dimension_index_values': [1, k + 1, 1],
             'pixel_spacing_row_column_mm': [.36, .36]} for k in range(144)]


def test_negative_normal_progression_does_not_reverse_the_source_stack():
    frames = native_frames()
    saved = copy.deepcopy(frames)
    result = audit.geometry(frames)
    assert frames == saved
    np.testing.assert_allclose(result['cross_column_row_direction'], [-1, 0, 0])
    np.testing.assert_allclose(result['mean_array_frame_step_patient_mm'], [.7, 0, 0])
    np.testing.assert_allclose(result['signed_step_along_iop_cross_normal_mm_range'], [-.7, -.7])
    assert result['resampling_applied'] is False
    assert result['image_to_fe_transform_established'] is False
    for frame in frames:
        frame['ipp_mm'][0] *= -1
    with pytest.raises(AssertionError, match='frame progression'):
        audit.geometry(frames)


def test_missing_stack_position_cannot_be_reported_as_contiguous():
    frames = native_frames()
    frames[30]['in_stack_position'] = 32
    with pytest.raises(AssertionError):
        audit.geometry(frames)


def test_deidentification_indicator_report_never_serializes_identifying_values():
    ds = pydicom.dataset.Dataset()
    ds.PatientName = 'PRIVATE^PATIENT'
    ds.PatientID = 'PRIVATE-RECORD'
    ds.OperatorsName = 'PRIVATE^OPERATOR'
    ds.DeviceSerialNumber = 'PRIVATE-DEVICE'
    ds.PatientBirthDate = '19600101'
    ds.PatientIdentityRemoved = 'NO'
    ds.BurnedInAnnotation = 'NO'
    ds.add_new((0x0011, 0x0010), 'LO', 'PRIVATE-CREATOR')
    ds.add_new((0x0011, 0x1010), 'LO', 'PRIVATE-EXTRA')
    result = audit.privacy(ds)
    encoded = json.dumps(result)
    assert 'PRIVATE' not in encoded and '19600101' not in encoded
    assert result['presence_only_no_values']['PatientName'] == 'populated'
    assert result['presence_only_no_values']['AccessionNumber'] == 'absent'
    assert result['private_elements_recursive_count'] == 2
    assert result['PatientIdentityRemoved'] == 'NO'
    assert result['release_deidentification_complete'] is False
