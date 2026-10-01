import pytest

from tools.anatomy_sources.audit_lnq_surface_geometry import topology


@pytest.fixture
def tetrahedron():
    np = pytest.importorskip('numpy')
    return np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float), np.array([
        [0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]], dtype=int)


def test_closed_oriented_tetrahedron_has_single_cycle_vertex_links(tetrahedron):
    vertices, faces = tetrahedron
    report = topology(vertices, faces)
    assert report['boundary_edges'] == report['nonmanifold_edges'] == report['nonmanifold_vertex_count'] == 0
    assert report['inconsistent_closed_edge_orientation'] == 0
    assert report['mesh_components'][0]['euler_characteristic'] == 2
    assert report['mesh_components'][0]['signed_volume_mm3'] == pytest.approx(1 / 6)
    assert not report['topology_is_anatomical_accuracy']


def test_closed_edges_cannot_hide_a_pinched_vertex(tetrahedron):
    np = pytest.importorskip('numpy')
    vertices, faces = tetrahedron
    combined_vertices = np.vstack([vertices, -vertices[1:]])
    second_faces = np.array([0, 4, 5, 6])[faces][:, ::-1]
    report = topology(combined_vertices, np.vstack([faces, second_faces]))
    assert report['boundary_edges'] == report['nonmanifold_edges'] == 0
    assert report['nonmanifold_vertex_count'] == 1
    assert report['vertex_defects'][0]['link_components'] == 2


def test_component_counts_do_not_claim_individual_node_identity(tetrahedron):
    np = pytest.importorskip('numpy')
    vertices, faces = tetrahedron
    report = topology(np.vstack([vertices, vertices + 3]), np.vstack([faces, faces + 4]))
    assert len(report['mesh_components']) == 2
    assert all(not row['independent_node_identity_verified'] for row in report['mesh_components'])
    assert all(row['euler_characteristic'] == 2 for row in report['mesh_components'])


def test_reversed_face_is_detected_even_with_closed_edges(tetrahedron):
    vertices, faces = tetrahedron
    faces = faces.copy(); faces[0] = faces[0, ::-1]
    report = topology(vertices, faces)
    assert report['boundary_edges'] == 0
    assert report['inconsistent_closed_edge_orientation'] == 3
