import pytest
from tools.anatomy_sources.check_atlantoaxial_topology import topology
V=[(0,0,0),(1,0,0),(0,1,0),(0,0,1)]
F=[(0,2,1),(0,1,3),(0,3,2),(1,2,3)]


def test_closed_tetrahedron_and_duplicated_normal_seams():
    result=topology(V,F)
    assert result['boundary_edges']==result['nonmanifold_edges']==result['inconsistent_two_face_edges']==0
    assert result['signed_volume_source_units_cubed']==pytest.approx(1/6)
    split=[V[i] for face in F for i in face]
    assert topology(split,[(i,i+1,i+2) for i in range(0,12,3)])==result


def test_open_surface_has_no_volume_claim():
    result=topology(V,F[:-1])
    assert result['boundary_edges']==3
    assert result['signed_volume_source_units_cubed'] is None


def test_extra_face_is_nonmanifold():
    result=topology(V,F+[F[0]])
    assert result['nonmanifold_edges']==3
    assert result['signed_volume_source_units_cubed'] is None


def test_reversed_face_detects_winding_conflict():
    result=topology(V,[tuple(reversed(F[0]))]+F[1:])
    assert result['inconsistent_two_face_edges']==3
    assert result['signed_volume_source_units_cubed'] is None
