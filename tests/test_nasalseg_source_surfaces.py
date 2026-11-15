"""Acquisition-boundary truncation must survive extraction, including disconnected labels."""
import pytest
np = pytest.importorskip('numpy')
pytest.importorskip('scipy')
pytest.importorskip('skimage')
from tools.anatomy_sources.export_nasalseg_source_surfaces import surface


def test_acquisition_boundary_remains_open_with_declared_anisotropic_coordinates():
    region = np.zeros((6, 8, 9), dtype=bool)
    region[:4, 2:6, 2:7] = True
    affine = np.array([[.5, 0, 0, -10], [0, .75, 0, -20], [0, 0, 1.5, -30], [0, 0, 0, 1]])
    vertices, faces, proof = surface(region, affine)
    assert proof['boundary_edges'] > 0 and proof['surface_components'] == 1
    assert vertices[:, 2].min() == -30
    assert proof['nonmanifold_edges'] == 0
    assert proof['maximum_affine_roundtrip_error_source_indices'] < 1e-8
    assert proof['sample_edge_interface_vertices_verified'] == len(vertices)


def test_disconnected_original_regions_are_not_deleted_or_joined():
    region = np.zeros((10, 12, 14), dtype=bool)
    region[2:5, 2:5, 2:5] = True
    region[7:9, 8:10, 9:11] = True
    vertices, faces, proof = surface(region, np.eye(4))
    assert proof['surface_components'] == 2
    assert proof['boundary_edges'] == 0
    assert proof['zero_area_triangles'] == 0


def test_ambiguous_cells_retain_and_report_extractor_interior_vertices():
    region = np.zeros((4, 4, 4), dtype=bool)
    region[1:3, 1:3, 1:3] = np.array([(61 >> i) & 1 for i in range(8)]).reshape(2, 2, 2)
    vertices, faces, proof = surface(region, np.eye(4))
    assert proof['ambiguity_resolution_interior_vertices_retained'] == 1
    assert proof['maximum_trilinear_binary_field_residual'] == .125
    assert proof['sample_edge_interface_vertices_verified'] + 1 == len(vertices)
