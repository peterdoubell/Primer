"""Analytic intersections guard the source-audit geometry independently of scans."""
from pathlib import Path
import sys

import pytest
np = pytest.importorskip('numpy')
pytest.importorskip('scipy')
pytest.importorskip('matplotlib')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/anatomy_sources'))
from audit_malaya_knee_images import section, raster_section


def subdivided_box():
    triangles = []
    # A closed 2x2x2 box with a vertex ring at z=0. At that plane, every
    # side-wall intersection is an existing edge, not a strict crossing.
    corners = [(-1,-1), (1,-1), (1,1), (-1,1)]
    for low, high in [(-1,0), (0,1)]:
        for i in range(4):
            a, b = corners[i], corners[(i+1)%4]
            p=[(*a,low),(*b,low),(*b,high),(*a,high)]
            triangles.extend([[p[0],p[1],p[2]],[p[0],p[2],p[3]]])
    for z in (-1,1):
        p=[(*c,z) for c in corners]
        triangles.extend([[p[0],p[1],p[2]],[p[0],p[2],p[3]]])
    return np.array(triangles,dtype=float)


@pytest.mark.parametrize('z', [-1, -.5, 0, .5, 1])
def test_box_section_includes_edge_and_coplanar_face_cases(z):
    contours=section(subdivided_box(),2,z,0,1)
    axis=np.array([-1.5,-.5,.5,1.5])
    actual=raster_section(contours,axis,axis)
    expected=np.zeros((4,4),dtype=bool);expected[1:3,1:3]=True
    np.testing.assert_array_equal(actual,expected)
    assert np.isfinite(contours).all()


def test_touching_a_single_vertex_does_not_create_area():
    triangles=np.array([[[0,0,0],[1,0,1],[0,1,1]]],dtype=float)
    assert section(triangles,2,0,0,1).shape==(0,2,2)


def test_outside_plane_is_empty():
    assert section(subdivided_box(),2,2,0,1).shape==(0,2,2)
