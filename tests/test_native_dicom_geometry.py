import json
from pathlib import Path

import pytest

from tools.anatomy_sources.native_dicom_geometry import validate_geometry


def frames():
    # Columns run along +Y, rows along +Z, slices along +X.
    return [dict(rows=5, columns=7, orientation=[0,1,0,0,0,1],
                 pixel_spacing_mm=[0.2,0.3], position_mm=[10+k*0.7,20,30],
                 instance=100-k, slice_thickness_mm=0.5) for k in [2,0,1]]


def test_physical_order_and_anisotropic_rotated_axes_are_preserved():
    result = validate_geometry(frames())
    assert result['source_frame_order'] == [1,2,0]
    affine = result['index_to_dicom_lps_mm']
    assert [sum(x*y for x,y in zip(row,[1,2,3,1])) for row in affine] == pytest.approx([10.7,20.9,30.4,1])
    assert result['slice_step_mm'] == pytest.approx(0.7)  # Not the 0.5 mm thickness.
    assert result['shape'] == [3,5,7]
    assert not result['resampled']
    assert not result['complete_anatomical_extent_proven']


@pytest.mark.parametrize('kind', ['duplicate','gap','drift','orientation','spacing','matrix','nonfinite'])
def test_incompatible_geometry_is_rejected_instead_of_repaired(kind):
    source = frames()
    if kind == 'duplicate': source[2]['position_mm'] = source[1]['position_mm'][:]
    if kind == 'gap': source[0]['position_mm'][0] += 0.7
    if kind == 'drift': source[0]['position_mm'][1] += 0.2
    if kind == 'orientation': source[0]['orientation'] = [1,0,0,0,1,0]
    if kind == 'spacing': source[0]['pixel_spacing_mm'][0] = 0.4
    if kind == 'matrix': source[0]['rows'] = 6
    if kind == 'nonfinite': source[0]['position_mm'][0] = float('nan')
    with pytest.raises(ValueError):
        validate_geometry(source)


def test_actual_donor3_grid_does_not_turn_into_complete_anatomy():
    root = Path(__file__).resolve().parents[1]
    audit = json.loads((root/'docs/msk-leeds-spine-source-review/native-audit.json').read_text())
    result = validate_geometry(audit['frames'])
    affine = result['index_to_dicom_lps_mm']
    assert result['shape'] == [146,2508,2508]
    assert [row[3] for row in affine] == pytest.approx([9.65,10.15,37.126,1])
    assert [row[0]*145+row[3] for row in affine] == pytest.approx([9.65,10.15,44.376,1])
    assert not result['complete_anatomical_extent_proven']


def test_small_step_errors_cannot_accumulate_into_a_wrong_volume():
    template = frames()[0]
    source = []
    position = 10.0
    for index in range(101):
        frame = dict(template, position_mm=[position,20,30])
        source.append(frame)
        position += 0.7 + (0.000004 if index < 50 else -0.000004)
    with pytest.raises(ValueError, match='one native affine'):
        validate_geometry(source)


def test_rounded_direction_cosines_do_not_scale_slice_distance():
    source = [dict(rows=2, columns=3, orientation=[.707107,.707107,0,-.707107,.707107,0],
                   pixel_spacing_mm=[.2,.3], position_mm=[10,20,30+k*.5]) for k in range(200)]
    result = validate_geometry(source)
    assert result['slice_step_mm'] == pytest.approx(.5)
    assert result['index_to_dicom_lps_mm'][2][0] == pytest.approx(.5)
    assert result['index_to_dicom_lps_mm'][0][2] == pytest.approx(.707107*.3)
