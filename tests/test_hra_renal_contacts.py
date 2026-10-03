import pytest
np=pytest.importorskip('numpy')
from tools.anatomy_sources.audit_hra_renal_contacts import contact_arrays
from tools.anatomy_sources.audit_massp_surface_intersections import inspect


def part(name,vertices,faces):return {'id':name,'vertices':np.asarray(vertices,float),'faces':np.asarray(faces,int)}


def test_exact_shared_vertices_across_parts_are_analysis_adjacency_only():
    a=part('a',[[0,0,0],[.001,0,0],[0,.001,0]],[[0,1,2]])
    b=part('b',[[.001,0,0],[0,0,0],[.001,-.001,0]],[[0,1,2]])
    old=a['vertices'].copy();v,f,identities,report=contact_arrays([a,b]);contacts=inspect(v,f)
    assert len(v)==4 and len(f)==2 and contacts['unexpected_contact_count']==0
    assert identities[0]['source_part']=='a' and identities[1]['source_part']=='b'
    assert np.array_equal(a['vertices'],old) and report['source_positions_changed'] is False


def test_original_invalid_face_is_held_with_identity_not_repaired():
    a=part('a',[[0,0,0],[.001,0,0],[0,.001,0]],[[0,1,2],[0,0,1]])
    v,f,identities,r=contact_arrays([a])
    assert r['original_source_triangles']==2 and r['numerically_testable_triangles']==1
    assert r['invalid_source_triangles'][0]['source_face_index']==1
    assert not r['invalid_source_triangles_removed_from_model']
    assert len(a['faces'])==2 and identities[0]['source_face_index']==0


def test_cross_part_overlap_cannot_be_excused_as_shared_topology():
    a=part('a',[[0,0,0],[.002,0,0],[0,.002,0]],[[0,1,2]])
    b=part('b',[[.0005,.0005,0],[.0015,.0005,0],[.0005,.0015,0]],[[0,1,2]])
    v,f,_,_=contact_arrays([a,b]);contacts=inspect(v,f)
    assert contacts['unexpected_contact_count']==1
    assert contacts['unexpected_contacts'][0]['shared_vertex_count']==0


def test_large_combined_vertex_index_does_not_wrap_at_source_uint16_limit():
    a=np.zeros((40000,3),float);b=np.zeros((40000,3),float)
    a[-3:]=[[0,0,0],[.001,0,0],[0,.001,0]]
    b[-3:]=[[0,0,.002],[.001,0,.002],[0,.001,.002]]
    parts=[{'id':'a','vertices':a,'faces':np.array([[39997,39998,39999]],dtype=np.uint16)},
           {'id':'b','vertices':b,'faces':np.array([[39997,39998,39999]],dtype=np.uint16)}]
    v,f,ids,report=contact_arrays(parts)
    assert len(f)==2 and not report['invalid_source_triangles']
    assert np.array_equal(v[f[1]][:,2],[2,2,2])
    assert ids[1]['source_part']=='b'
