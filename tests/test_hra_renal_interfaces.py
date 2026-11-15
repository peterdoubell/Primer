import pytest
np=pytest.importorskip('numpy')
from tools.anatomy_sources.audit_hra_renal_interfaces import compare_boundaries,boundary_edges


def triangle(name,points):return {'id':name,'vertices':np.asarray(points,float),'faces':np.array([[0,1,2]],int)}


def test_adjacent_source_parts_keep_opposing_exact_edge_directions():
    a=triangle('a',[[0,0,0],[1,0,0],[0,1,0]]);b=triangle('b',[[1,0,0],[0,0,0],[1,-1,0]])
    report=compare_boundaries([a,b])
    assert report['source_boundary_edge_occurrences']==6
    assert report['exact_boundary_pair_edges']==1 and report['unmatched_boundary_edges']==4
    assert report['pairs'][0]['opposing_direction_edges']==1
    assert not report['pairs'][0]['anatomical_interface_verified']


def test_same_edge_direction_is_not_repaired():
    a=triangle('a',[[0,0,0],[1,0,0],[0,1,0]]);b=triangle('b',[[0,0,0],[1,0,0],[0,-1,0]])
    r=compare_boundaries([a,b]);assert r['pairs'][0]['same_direction_edges']==1
    assert not r['source_meshes_modified_or_fused']


def test_near_coordinates_are_not_snapped_into_an_interface():
    a=triangle('a',[[0,0,0],[1,0,0],[0,1,0]]);b=triangle('b',[[1,0,1e-7],[0,0,1e-7],[1,-1,1e-7]])
    r=compare_boundaries([a,b]);assert r['exact_boundary_pair_edges']==0 and r['unmatched_boundary_edges']==6


def test_exported_index_seam_is_analysis_only_and_not_a_cross_part_interface():
    vertices=np.array([[0,0,0],[1,0,0],[0,1,0],[1,0,0],[0,0,0],[1,-1,0]],float);faces=np.array([[0,1,2],[3,4,5]])
    old=vertices.copy();records,stats=boundary_edges(vertices,faces)
    assert len(records)==4 and stats['indexed_vertices']==6 and stats['exact_unique_positions']==4
    assert np.array_equal(vertices,old)


def test_three_source_owners_cannot_be_called_a_normal_two_part_interface():
    parts=[triangle(n,[[0,0,0],[1,0,0],[0,1,0]]) for n in ['a','b','c']]
    r=compare_boundaries(parts);assert r['multiple_owner_boundary_edges']==3 and r['exact_boundary_pair_edges']==0


def test_all_unmatched_graph_components_remain_indexed_without_anatomical_labels():
    from tools.anatomy_sources.audit_hra_renal_interfaces import boundary_components
    triangle_loop=[[[0,0,0],[1,0,0]],[[1,0,0],[0,1,0]],[[0,1,0],[0,0,0]]]
    records=[{'source_part':'part','coordinates_original_metres':e} for e in triangle_loop]
    records.append({'source_part':'part','coordinates_original_metres':[[4,0,0],[5,0,0]]})
    result=boundary_components(records)
    assert len(result)==2 and sum(r['edges'] for r in result)==4
    assert result[0]['is_closed_simple_graph_cycle']
    assert not result[1]['is_closed_simple_graph_cycle']
    assert all(not r['anatomical_role_assigned'] for r in result)
