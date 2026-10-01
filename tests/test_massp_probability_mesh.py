import unittest

try:
    import numpy as np
    from tools.anatomy_sources.massp_probability_mesh import mesh_mask
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


@unittest.skipUnless(AVAILABLE, 'Optional source-mesh scientific dependencies are separate from application runtime')
class NativeMaskSurfaceTests(unittest.TestCase):
    def test_reflected_source_affine_preserves_two_components_and_world_extent(self):
        mask = np.zeros((12, 12, 12), dtype=bool)
        mask[2:5, 3:6, 4:7] = True
        mask[8:10, 8:10, 8:10] = True
        original = mask.copy()
        affine = np.diag([.5, -.5, .5, 1.])
        affine[:3, 3] = [-98., 98.5, -72.]
        vertices, faces, stats = mesh_mask(mask, affine)
        np.testing.assert_array_equal(mask, original)
        np.testing.assert_allclose(vertices.min(0), [-97.25, 93.75, -70.25])
        np.testing.assert_allclose(vertices.max(0), [-93.25, 97.25, -67.25])
        self.assertEqual(stats['native_selected_voxels'], 35)
        self.assertEqual(stats['source_components_6_connected'], 2)
        self.assertEqual(stats['removed_components'], 0)
        self.assertGreater(stats['surface_signed_volume_mm3'], 0)
        self.assertEqual(stats['boundary_edges'], 0)
        self.assertEqual(stats['nonmanifold_edges'], 0)

    def test_source_boundary_contact_cannot_be_capped(self):
        mask = np.zeros((8, 8, 8), dtype=bool)
        mask[0:3, 2:5, 2:5] = True
        with self.assertRaisesRegex(ValueError, 'source boundary'):
            mesh_mask(mask, np.eye(4))

    def test_empty_selection_and_singular_affine_are_rejected(self):
        mask = np.zeros((8, 8, 8), dtype=bool)
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            mesh_mask(mask, np.eye(4))
        mask[2:5, 2:5, 2:5] = True
        with self.assertRaisesRegex(ValueError, 'affine'):
            mesh_mask(mask, np.zeros((4, 4)))


if __name__ == '__main__':
    unittest.main()
