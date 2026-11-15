import pytest

from tools.anatomy_sources.compare_lnq_native_interpolations import restore_native_indices, voxel_audit


@pytest.mark.parametrize('axis', [None, 0, 1, 2])
def test_index_reflection_restores_native_coordinates_and_face_orientation(axis):
    np = pytest.importorskip('numpy')
    vertices = np.array([[1, 2, 3], [1, 2.5, 3], [1, 2, 3.5]], dtype=float)
    faces = np.array([[0, 1, 2]], dtype=int); original = vertices.copy()
    reflected = vertices.copy(); input_faces = faces.copy(); shape = (7, 8, 9)
    if axis is not None:
        reflected[:, axis] = shape[axis] - 1 - reflected[:, axis]
        input_faces = input_faces[:, ::-1]
    restored, restored_faces = restore_native_indices(reflected, input_faces, shape, axis)
    np.testing.assert_array_equal(restored, original)
    # Cyclic permutations preserve the same oriented triangle.
    before = np.cross(vertices[faces[0, 1]] - vertices[faces[0, 0]], vertices[faces[0, 2]] - vertices[faces[0, 0]])
    after = np.cross(restored[restored_faces[0, 1]] - restored[restored_faces[0, 0]], restored[restored_faces[0, 2]] - restored[restored_faces[0, 0]])
    np.testing.assert_array_equal(before, after)
    np.testing.assert_array_equal(vertices, original)


def test_each_body_diagonal_preserves_the_known_single_source_voxel():
    np = pytest.importorskip('numpy')
    pytest.importorskip('nibabel')
    from tools.anatomy_sources.build_massp_joint_interfaces import build_label_surfaces
    labels = np.zeros((5, 6, 7), dtype=int); labels[2, 2, 3] = 1; original = labels.copy()
    for axis in (None, 0, 1, 2):
        source = labels if axis is None else np.flip(labels, axis=axis)
        result, _ = build_label_surfaces(source, {1})
        vertices, faces = restore_native_indices(*result[1], labels.shape, axis)
        report = voxel_audit(labels, vertices, faces)
        assert report['all_source_positive_voxels_compared'] == 1
        assert report['false_positive'] == report['false_negative'] == 0
    np.testing.assert_array_equal(labels, original)
