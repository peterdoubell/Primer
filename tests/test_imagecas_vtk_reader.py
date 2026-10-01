import struct
import unittest
from pathlib import Path
import tempfile

try:
    import numpy as np
    from tools.anatomy_sources.audit_imagecas_source_geometry import vtk_points,ascii_surface
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


@unittest.skipUnless(AVAILABLE,'Optional source audit scientific dependencies')
class DeclaredVTKFormats(unittest.TestCase):
    def test_ascii_points_and_vtk51_triangle_connectivity(self):
        raw=b'# vtk DataFile Version 5.1\nfixture\nASCII\nDATASET POLYDATA\nPOINTS 3 double\n0 0 0 1 0 0 0 1 0\nPOLYGONS 2 3\nOFFSETS vtktypeint64\n0 3\nCONNECTIVITY vtktypeint64\n0 1 2\n'
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.vtk';path.write_bytes(raw)
            vertices,faces=ascii_surface(path)
            np.testing.assert_array_equal(vertices,[[0,0,0],[1,0,0],[0,1,0]])
            np.testing.assert_array_equal(faces,[[0,1,2]])

    def test_binary_big_endian_float_points_are_not_read_as_ascii(self):
        raw=b'# vtk DataFile Version 5.1\nfixture\nBINARY\nDATASET POLYDATA\nPOINTS 2 float\n'+struct.pack('>6f',-20,130,400,10,150,450)+b'\n'
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.vtk';path.write_bytes(raw)
            vertices,encoding,_=vtk_points(path)
            self.assertEqual(encoding,'BINARY')
            np.testing.assert_array_equal(vertices,[[-20,130,400],[10,150,450]])

    def test_nontriangular_source_polygons_are_rejected_without_tessellation(self):
        raw=b'# vtk DataFile Version 5.1\nfixture\nASCII\nDATASET POLYDATA\nPOINTS 4 double\n0 0 0 1 0 0 1 1 0 0 1 0\nPOLYGONS 2 4\nOFFSETS vtktypeint64\n0 4\nCONNECTIVITY vtktypeint64\n0 1 2 3\n'
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.vtk';path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'complete triangle'):ascii_surface(path)


if __name__=='__main__':unittest.main()
