import unittest
try:
    import numpy as np
    from tools.anatomy_sources.localize_aeropath_adjacency import cube_components
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


@unittest.skipUnless(AVAILABLE,'Optional scientific adjacency dependencies')
class CubeAdjacency(unittest.TestCase):
    def test_uniform_cells_do_not_create_false_connectivity_ambiguity(self):
        foreground,background=cube_components()
        self.assertEqual((int(foreground[0]),int(background[0])),(0,1))
        self.assertEqual((int(foreground[255]),int(background[255])),(1,0))

    def test_face_neighbours_connect_but_corner_only_neighbours_do_not(self):
        foreground,_=cube_components()
        self.assertEqual(int(foreground[(1<<0)|(1<<1)]),1)
        self.assertEqual(int(foreground[(1<<0)|(1<<7)]),2)

    def test_foreground_background_complement_symmetry_for_all_configurations(self):
        foreground,background=cube_components()
        for code in range(256):self.assertEqual(int(foreground[code]),int(background[255-code]))


if __name__=='__main__':unittest.main()
