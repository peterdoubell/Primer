"""Recorded transform directions and pixel centres must remain explicit; no hidden fitting."""
import pytest
np=pytest.importorskip('numpy');pytest.importorskip('scipy')
from tools.anatomy_sources.check_openear_recorded_photo_transform import source_sampling_coordinates


def test_identity_canvas_scale_preserves_declared_pixel_centres():
    coords=source_sampling_coordinates(4,4,2,2,np.eye(3),'template_to_raw')
    assert coords.tolist()==[[[.5,.5],[2.5,.5]],[[.5,2.5],[2.5,2.5]]]


def test_forward_and_inverse_direction_do_not_silently_refit_translation():
    M=np.array([[1,0,3],[0,1,-2],[0,0,1]])
    assert source_sampling_coordinates(2,2,2,2,M,'template_to_raw')[0,0].tolist()==[3,-2]
    assert source_sampling_coordinates(2,2,2,2,M,'raw_to_template')[0,0].tolist()==[-3,2]


def test_singular_recorded_source_matrix_rejected():
    with pytest.raises(ValueError):source_sampling_coordinates(2,2,2,2,np.zeros((3,3)),'template_to_raw')
