import unittest

try:
    import numpy as np
    from tools.anatomy_sources.audit_massp_mesh_voxels import section, raster_section
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


@unittest.skipUnless(AVAILABLE, 'Optional scientific source-audit dependencies')
class AnalyticalSurfaceSections(unittest.TestCase):
    def cube(self):
        vertices = np.array([[.5,.5,.5],[2.5,.5,.5],[2.5,2.5,.5],[.5,2.5,.5],
                             [.5,.5,2.5],[2.5,.5,2.5],[2.5,2.5,2.5],[.5,2.5,2.5]])
        faces = np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],
                          [1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
        return vertices[faces]

    def test_every_voxel_centre_of_an_analytical_cube(self):
        cube = self.cube()
        grid = np.arange(4)
        expected = np.zeros((4,4),dtype=bool); expected[1:3,1:3]=True
        for z in range(4):
            result = raster_section(section(cube,2,z,0,1),grid,grid)
            np.testing.assert_array_equal(result, expected if z in (1,2) else np.zeros_like(expected))

    def test_coplanar_face_and_shared_edges_do_not_erase_the_section(self):
        lines = section(self.cube(),2,.5,0,1)
        result = raster_section(lines,np.arange(4),np.arange(4))
        expected = np.zeros((4,4),dtype=bool);expected[1:3,1:3]=True
        np.testing.assert_array_equal(result,expected)

    def test_disconnected_complete_components_are_preserved(self):
        cube = self.cube()
        two = np.concatenate([cube,cube+np.array([4,0,0])])
        result = raster_section(section(two,2,1,0,1),np.arange(8),np.arange(4))
        expected = np.zeros((4,8),dtype=bool);expected[1:3,1:3]=True;expected[1:3,5:7]=True
        np.testing.assert_array_equal(result,expected)


if __name__=='__main__':
    unittest.main()
