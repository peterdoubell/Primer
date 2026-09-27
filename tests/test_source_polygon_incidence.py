from tools.anatomy_sources.compare_bone_source_topology import incidence


def test_triangulation_preserves_quad_boundary_incidence():
    points=[(0.,0.,0.),(1.,0.,0.),(1.,1.,0.),(0.,1.,0.)]
    polygon=incidence(points,[[0,1,2,3]])
    triangles=incidence(points,[[0,1,2],[0,2,3]])
    assert polygon==triangles
    assert len(polygon)==4 and set(polygon.values())=={1}


def test_duplicate_incident_faces_are_not_discarded():
    points=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
    result=incidence(points,[[0,1,2]]*4)
    assert len(result)==3 and set(result.values())=={4}
