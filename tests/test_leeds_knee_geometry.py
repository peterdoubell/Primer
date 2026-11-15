"""Small analytical checks; these do not certify source anatomy or mesh quality."""
import importlib.util
from itertools import permutations
from pathlib import Path

import pytest

np = pytest.importorskip('numpy')


SCRIPT = Path(__file__).resolve().parents[1] / 'tools/anatomy_sources/audit_leeds_knee_geometry.py'
SPEC = importlib.util.spec_from_file_location('leeds_knee_geometry', SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def two_tetrahedra():
    # Share the a,b,c face with reverse local order in the second cell.
    return np.array(((1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                     (1, 3, 2, 11, 7, 6, 5, 12, 13, 14)))


def test_quadratic_shared_face_adjacency():
    topology = audit.face_topology(two_tetrahedra())
    assert topology['unique_faces'] == 7
    assert topology['boundary_faces'] == 6
    assert topology['interior_faces'] == 1
    assert set((topology['interior_pairs'][0] // 4).tolist()) == {0, 1}
    boundary = topology['faces'][topology['boundary_indices']]
    assert boundary.shape == (6, 6)
    assert audit.surface_edge_topology(boundary)['open_surface_edges'] == 0
    assert audit.surface_edge_topology(boundary)['nonmanifold_surface_edges'] == 0
    assert audit.surface_edge_topology(boundary)['surface_connected_components'] == 1
    assert audit.surface_edge_topology(boundary)['surface_euler_characteristic'] == 2


def test_disconnected_closed_surfaces_remain_distinguishable():
    cells = two_tetrahedra()[:1]
    topology = audit.face_topology(np.vstack((cells, cells+20)))
    faces = topology['faces'][topology['boundary_indices']]
    stats = audit.surface_edge_topology(faces)
    assert stats['surface_connected_components'] == 2
    assert stats['surface_euler_characteristic'] == 4
    assert stats['open_surface_edges'] == stats['nonmanifold_surface_edges'] == 0


def test_shared_face_rejects_same_six_nodes_with_wrong_midside_assignment():
    cells = two_tetrahedra()
    cells[1, [4, 5]] = cells[1, [5, 4]]
    with pytest.raises(ValueError, match='edge-associated midside'):
        audit.face_topology(cells)


def test_canonical_face_is_invariant_under_every_corner_permutation():
    mids = {frozenset((1, 2)): 4, frozenset((2, 3)): 5, frozenset((3, 1)): 6}
    faces = np.array([(a, b, c, mids[frozenset((a, b))],
                       mids[frozenset((b, c))], mids[frozenset((c, a))])
                      for a, b, c in permutations((1, 2, 3))])
    np.testing.assert_array_equal(audit.canonical_faces(faces), np.tile((1, 2, 3, 4, 5, 6), (6, 1)))


def test_volume_face_incidence_above_two_rejected():
    cells = np.vstack((two_tetrahedra(), two_tetrahedra()[1]))
    with pytest.raises(ValueError, match='Nonmanifold volume face'):
        audit.face_topology(cells)


def test_triangle_interpolation_kronecker_partition_and_curved_edge():
    nodal_bary = np.array(((1, 0, 0), (0, 1, 0), (0, 0, 1),
                          (.5, .5, 0), (0, .5, .5), (.5, 0, .5)))
    np.testing.assert_allclose(audit.quadratic_triangle_shape(nodal_bary), np.eye(6))
    samples = np.array(((.2, .3, .5), (.75, .25, 0), (1/3, 1/3, 1/3)))
    np.testing.assert_allclose(audit.quadratic_triangle_shape(samples).sum(axis=1), 1)
    # Analytical curved edge: z(t)=4*t*(1-t), with middle z=1.
    points = np.array(((0, 0, 0), (1, 0, 0), (0, 1, 0),
                       (.5, 0, 1), (.5, .5, 0), (0, .5, 0)))
    at_quarter = audit.quadratic_triangle_shape((.75, .25, 0)) @ points
    np.testing.assert_allclose(at_quarter, (.25, 0, .75))


def test_tetrahedron_interpolation_preserves_ten_nodes_and_affine_geometry():
    corners = np.eye(4)
    nodal_bary = np.vstack((corners, (corners[0]+corners[1])/2,
                           (corners[1]+corners[2])/2, (corners[2]+corners[0])/2,
                           (corners[0]+corners[3])/2, (corners[1]+corners[3])/2,
                           (corners[2]+corners[3])/2))
    np.testing.assert_allclose(audit.quadratic_tetrahedron_shape(nodal_bary), np.eye(10))
    bary = np.array((.1, .2, .3, .4))
    weights = audit.quadratic_tetrahedron_shape(bary)
    np.testing.assert_allclose(weights.sum(), 1)
    np.testing.assert_allclose(weights @ nodal_bary[:, 1:], bary[1:])


def test_every_boundary_face_interpolates_the_restriction_of_c3d10():
    triangle_bary = np.array((.2, .3, .5))
    for face in audit.FACE_NODES:
        tetra_bary = np.zeros(4)
        tetra_bary[face[:3]] = triangle_bary
        restricted_weights = np.zeros(10)
        restricted_weights[face] = audit.quadratic_triangle_shape(triangle_bary)
        np.testing.assert_allclose(audit.quadratic_tetrahedron_shape(tetra_bary), restricted_weights)


def test_author_transform_translates_before_rotation():
    matrix = audit.instance_matrix(('114,166,0', '114,166,0,114,166,1,180'))
    points = np.array(((0, 0, 0), (1, 2, 3), (91.7149811, 115.121178, 140.009766)))
    expected = points * (-1, -1, 1) + (114, 166, 0)
    np.testing.assert_allclose(audit.transform_points(points, matrix), expected, atol=1e-12)
    # A rotation-first implementation about this nonorigin axis has a different offset.
    np.testing.assert_allclose(matrix[:3, 3], (114, 166, 0), atol=1e-12)
    np.testing.assert_allclose(np.linalg.det(matrix[:3, :3]), 1, atol=1e-12)


def test_preview_is_quadratic_sampled_and_includes_all_midside_nodes():
    bary, triangles = audit.preview_grid(4)
    assert bary.shape == (15, 3)
    assert triangles.shape == (16, 3)
    for middle in ((.5, .5, 0), (0, .5, .5), (.5, 0, .5)):
        assert np.any(np.all(bary == middle, axis=1))
    # Total barycentric-domain area is exactly the unit triangle's area.
    xy = bary[:, 1:]
    ab, ac = xy[triangles[:, 1]]-xy[triangles[:, 0]], xy[triangles[:, 2]]-xy[triangles[:, 0]]
    signed_double_area = ab[:, 0]*ac[:, 1]-ab[:, 1]*ac[:, 0]
    assert np.all(signed_double_area > 0)
    np.testing.assert_allclose(signed_double_area.sum()/2, .5)
    with pytest.raises(ValueError, match='even subdivision'):
        audit.preview_grid(1)


def test_midpoint_deviation_distinguishes_axial_offset_from_off_edge_bulge():
    points = np.array(((0, 0, 0), (2, 0, 0), (.75, 0, 0), (1, .5, 0)))
    _, midpoint, segment = audit.deviation_stats(points, np.array(((0, 1, 2), (0, 1, 3))))
    np.testing.assert_allclose(midpoint, (.25, .5))
    np.testing.assert_allclose(segment, (0, .5))


def test_parser_refuses_external_geometry_and_separates_reference_nodes():
    with pytest.raises(ValueError, match='Unsupported keyword'):
        list(audit.blocks('*Include, input=more.inp\n'))
    nodes = '\n'.join(f'{i},{i},0,0' for i in range(1, 11))
    source = ('*Part,name=P\n*Node\n' + nodes +
              '\n*Element,type=C3D10\n1,1,2,3,4,5,6,7,8,9,10\n*End Part\n'
              '*Assembly,name=A\n*Instance,name=I,part=P\n*End Instance\n'
              '*Node\n1,99,98,97\n*End Assembly\n').encode('ascii')
    parsed = audit.parse_input(source)
    assert parsed['node_ids'].shape == (10,)
    np.testing.assert_allclose(parsed['points'][0], (1, 0, 0))
    assert parsed['assembly_nodes'] == [(1, 99., 98., 97.)]
