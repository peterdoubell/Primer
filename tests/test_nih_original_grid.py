import pytest
from tools.anatomy_sources.review_nih_node_source import verify_original_grid_positions


def fixture():
    np = pytest.importorskip('numpy'); pytest.importorskip('nibabel')
    affine = np.array([[-.853515625, 0, 0, 211.5], [0, -.853515625, 0, 91.5],
                       [0, 0, 1, -437.1000061035156], [0, 0, 0, 1]])
    positions = np.array([[-211.5, -91.5, -437.1 + k] for k in range(4)])
    return affine, positions


def test_decimal_positions_are_checked_against_each_original_plane_without_fitting():
    affine, positions = fixture()
    errors = verify_original_grid_positions(positions, affine, 4)
    assert errors.max() == pytest.approx(.0000061035156)


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'physical_offset'])
def test_missing_duplicate_and_displaced_slices_cannot_pass(change):
    affine, positions = fixture()
    if change == 'missing':positions = positions[:-1]
    if change == 'duplicate':positions[2] = positions[1]
    if change == 'physical_offset':positions[2, 2] += .1
    with pytest.raises(ValueError):verify_original_grid_positions(positions, affine, 4)
