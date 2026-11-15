"""Scientific extraction retains source samples and does not assert patient-coordinate clinical geometry."""
import pytest
np=pytest.importorskip('numpy')
pytest.importorskip('scipy')
pytest.importorskip('skimage')
from skimage.measure import marching_cubes
from tools.anatomy_sources.export_hipas_source_surfaces import source_edge_check,topology

def test_single_source_voxel_produces_closed_octahedron_without_fitting():
    source=np.zeros((3,3,3),dtype=np.uint8);source[1,1,1]=1
    vertices,faces,_,_=marching_cubes(source,.5,allow_degenerate=False)
    proof=source_edge_check(source,vertices)
    assert len(vertices)==6 and len(faces)==8
    assert proof['original_edge_midpoint_vertices']==6 and proof['active_cell_interior_ambiguity_vertices']==0
    assert proof['maximum_vertex_trilinear_level_residual']==0
    assert topology(vertices,faces)['boundary_edges']==0

def test_false_edge_and_outside_grid_vertices_are_rejected():
    source=np.zeros((3,3,3),dtype=np.uint8);source[1,1,1]=1
    with pytest.raises(ValueError):source_edge_check(source,np.array([[0,0,.5]]))
    with pytest.raises(ValueError):source_edge_check(source,np.array([[-.5,1,1]]))

def test_interior_ambiguity_sample_is_separate_from_original_edge_midpoint():
    source=np.zeros((2,2,2),dtype=np.uint8);source[0,0,0]=1
    proof=source_edge_check(source,np.array([[.5,.5,.5]]))
    assert proof['original_edge_midpoint_vertices']==0 and proof['active_cell_interior_ambiguity_vertices']==1
    assert proof['maximum_vertex_trilinear_level_residual']==.375

def test_three_faces_sharing_one_edge_are_reported_as_nonmanifold():
    vertices=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[0,-1,0]],dtype=float)
    faces=np.array([[0,1,2],[1,0,3],[0,1,4]])
    proof=topology(vertices,faces)
    assert proof['nonmanifold_edges']==1 and proof['nonmanifold_edge_source_vertices']==[[0,1]]
    assert proof['nonmanifold_edge_incident_face_counts']==[3]
