import pytest
np=pytest.importorskip('numpy')
from tools.anatomy_sources.review_cptac_renal_contours import polygon_lines, boundary_distance_bound


def square(offset=0):
    return polygon_lines(np.array([[0,0],[2,0],[2,2],[0,2]],float)+[0,offset])


def test_closed_polygon_preserves_vertices_and_implicit_closure():
    lines=square()
    assert np.array_equal(lines[-1],[[0,2],[0,0]])
    assert len(lines)==4


def test_repeated_keyhole_vertex_is_held_instead_of_pruned():
    with pytest.raises(ValueError,match='Repeated/keyhole'):
        polygon_lines([[0,0],[2,0],[2,2],[0,0]])


def test_parallel_boundary_offset_is_exact_at_samples_and_conservatively_bounded():
    a=np.array([[[0,0],[2,0]]],float);b=np.array([[[0,.4],[2,.4]]],float)
    result=boundary_distance_bound(a,b,.125)
    assert result['maximum_sample_to_segment_distance_mm']==pytest.approx(.4)
    assert result['conservative_whole_boundary_upper_bound_mm']==pytest.approx(.4625)


def test_distance_checks_segment_interiors_not_only_endpoints():
    a=np.array([[[0,0],[2,0]]],float);b=np.array([[[0,0],[1,1]],[[1,1],[2,0]]],float)
    result=boundary_distance_bound(a,b,.125)
    assert result['maximum_sample_to_segment_distance_mm']==pytest.approx(1/np.sqrt(2))
    assert result['conservative_whole_boundary_upper_bound_mm']>=1/np.sqrt(2)


def test_identical_closed_boundaries_have_zero_sample_distance():
    result=boundary_distance_bound(square(),square())
    assert result['maximum_sample_to_segment_distance_mm']==0
    assert result['conservative_whole_boundary_upper_bound_mm']<=.0625


def test_crossing_polygon_is_held_before_area_or_raster_claim():
    with pytest.raises(ValueError,match='Self-contacting'):
        polygon_lines([[0,0],[2,2],[0,2],[2,0]])
