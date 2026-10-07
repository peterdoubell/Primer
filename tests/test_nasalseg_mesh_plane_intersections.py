"""Cross-sections must intersect serialized triangles rather than project off-plane geometry."""
import pytest
np = pytest.importorskip('numpy')
pytest.importorskip('scipy')
pytest.importorskip('matplotlib')
from tools.anatomy_sources.render_nasalseg_surface_alignment import plane_segments


def test_triangle_cross_section_uses_interpolated_edge_positions():
    vertices = np.array([[-1., 0, 0], [1., 4, 0], [1., 0, 6]])
    segments, coplanar = plane_segments(vertices, np.array([[0, 1, 2]]), 0, 0)
    assert coplanar == 0 and segments.shape == (1, 2, 3)
    assert {tuple(x) for x in segments[0]} == {(0., 2., 0.), (0., 0., 3.)}


def test_wholly_off_plane_and_plane_coincident_faces_are_not_projected():
    vertices = np.array([[1., 0, 0], [1., 4, 0], [1., 0, 6]])
    faces = np.array([[0, 1, 2]])
    segments, coplanar = plane_segments(vertices, faces, 0, 0)
    assert segments.shape == (0, 2, 3) and coplanar == 0
    segments, coplanar = plane_segments(vertices, faces, 0, 1)
    assert segments.shape == (0, 2, 3) and coplanar == 1
