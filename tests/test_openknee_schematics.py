"""Analytical depth/orientation checks for source-derived scientific figures."""
import importlib.util
from pathlib import Path

import pytest

np = pytest.importorskip('numpy')

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'openknee_schematic_renderer', ROOT / 'tools/anatomy_sources/render_openknee_schematics.py')
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


def mesh(identifier, triangle, color):
    vertices = np.asarray([triangle], dtype=float)
    normals = np.cross(vertices[:, 1] - vertices[:, 0], vertices[:, 2] - vertices[:, 0])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    return {'id': identifier, 'triangles': vertices, 'normals': normals, 'color': color}


def test_per_pixel_occlusion_changes_with_depth_inside_the_same_overlapping_triangles():
    slope = mesh('a-slope', [[0, 0, -1], [8, 0, 3], [0, 8, -1]], '#b05040')
    flat = mesh('b-flat', [[0, 0, 0], [8, 0, 0], [0, 8, 0]], '#4070b0')
    projection = {'center_uv_mm': [0, 8], 'center_pixel': [0, 0], 'pixels_per_mm': 1}
    result = renderer.rasterize([slope, flat], np.eye(3), projection, (9, 9))
    reverse = renderer.rasterize([flat, slope], np.eye(3), projection, (9, 9))
    assert result[2][6, 1] == 1  # Flat is closer where slope depth is negative.
    assert result[2][6, 4] == 0  # Slope is closer farther right in the same triangle.
    assert result[1][6, 1] == 0
    assert result[1][6, 4] == pytest.approx(1.25)
    assert np.array_equal(result[0], reverse[0])
    assert np.array_equal(result[2], reverse[2])


def test_left_ras_posterior_and_superior_views_preserve_anatomical_orientation():
    posterior = renderer.camera_basis([1, 0, 0], [0, 0, 1], [0, -1, 0])
    superior = renderer.camera_basis([1, 0, 0], [0, 1, 0], [0, 0, 1])
    for basis in (posterior, superior):
        assert np.array_equal(np.array([1, 0, 0]) @ basis.T, [1, 0, 0])  # Medial -> screen right.
    assert np.array_equal(np.array([0, 0, 1]) @ posterior.T, [0, 1, 0])  # Superior -> screen up.
    assert np.array_equal(np.array([0, -1, 0]) @ posterior.T, [0, 0, 1])  # Posterior is nearer.
    assert np.array_equal(np.array([0, 1, 0]) @ superior.T, [0, 1, 0])  # Anterior -> screen up.
    assert np.array_equal(np.array([0, 0, 1]) @ superior.T, [0, 0, 1])  # Superior is nearer.
    with pytest.raises(ValueError, match='right-handed'):
        renderer.camera_basis([-1, 0, 0], [0, 1, 0], [0, 0, 1])


def test_native_mm_projection_has_uniform_scale_without_anisotropic_stretch():
    basis = renderer.camera_basis([1, 0, 0], [0, 1, 0], [0, 0, 1])
    projection = {'center_uv_mm': [10, 20], 'center_pixel': [100, 100], 'pixels_per_mm': 5}
    points = np.array([[10, 20, 0], [30, 20, 0], [10, 40, 0]], dtype=float)
    drawn = renderer.project(points.copy(), basis, projection)
    assert np.array_equal(drawn, [[100, 100, 0], [200, 100, 0], [100, 0, 0]])
    assert np.array_equal(points, [[10, 20, 0], [30, 20, 0], [10, 40, 0]])


def test_label_anchor_is_a_visible_source_triangle_point_with_reconstructable_weights():
    surface = mesh('source-object', [[0, 0, 5], [8, 0, 5], [0, 8, 5]], '#4070b0')
    projection = {'center_uv_mm': [0, 8], 'center_pixel': [0, 0], 'pixels_per_mm': 1}
    result = renderer.rasterize([surface], np.eye(3), projection, (9, 9))
    anchor = renderer.visible_anchor(
        {'part': 'source-object', 'text': 'Source object', 'preferred_uv': [2, 2]},
        [surface], result, np.eye(3), projection)
    weights = np.array(anchor['barycentric_weights'])
    assert weights.min() >= 0 and weights.sum() == pytest.approx(1)
    expected = weights @ surface['triangles'][anchor['source_triangle_index']]
    assert np.allclose(expected, anchor['world_ras_mm'])
    assert expected[2] == 5
    x, y = (int(v) for v in anchor['pixel_center'])
    assert result[2][y, x] == 0
    assert anchor['source_facet_normal_camera'][2] > 0
