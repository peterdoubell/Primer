"""Complete reverse cell-surface bounds must not be replaced by forward-only metrics."""
from collections import defaultdict
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/spl-wall-source-review'


def test_triangle_distance_matches_analytic_plane_edge_and_vertex_cases():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.bound_spl_wall_reverse_distance import triangle_distances,mesh_oracle
    t=np.array([[[0,0,0],[2,0,0],[0,2,0]]],float)
    for point,expected in [([.5,.5,3],3),([1,1,0],0),([2,2,0],2**.5),([-1,-1,0],2**.5),([3,0,0],1)]:
        assert triangle_distances(np.asarray(point,float),t)[0]==pytest.approx(expected)
    # Independent exhaustive face scan verifies the conservative centre search.
    rng=np.random.default_rng(714);triangles=rng.normal(size=(80,3,3));points=rng.normal(size=(60,3))
    distance,_=mesh_oracle(triangles)
    assert np.allclose(distance(points),[triangle_distances(p,triangles).min() for p in points],rtol=0,atol=1e-12)


def test_native_rectangle_split_is_coplanar_complete_and_metric_preserving():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.bound_spl_wall_reverse_distance import rectangle_triangles,triangle_distances
    spacing=np.array([1.,2.,3.]);centers=np.array([[0.,0.,0.]]);cells=rectangle_triangles(centers,np.array([0]),spacing)
    assert cells.shape==(2,3,3) and np.all(cells[:,:,0]==0)
    areas=np.linalg.norm(np.cross(cells[:,1]-cells[:,0],cells[:,2]-cells[:,0]),axis=1)/2
    assert areas.sum()==pytest.approx(6)
    assert min(triangle_distances(np.array([1.,0.,0.]),cells))==pytest.approx(1)


def test_all_reverse_native_faces_have_complete_nonoverlapping_analysis_cover():
    summary=json.loads((REVIEW/'reverse-distance-bound-summary.json').read_text())
    forward=json.loads((REVIEW/'triangle-distance-bound-summary.json').read_text())
    assert summary['all_five_original_models_complete'] and len(summary['records'])==5
    assert summary['forward_summary_sha256']==hashlib.sha256((REVIEW/'triangle-distance-bound-summary.json').read_bytes()).hexdigest()
    for row in summary['records']:
        packed=(REVIEW/row['file']).read_bytes();raw=gzip.decompress(packed);e=json.loads(raw)
        assert hashlib.sha256(packed).hexdigest()==row['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest()==row['uncompressed_sha256']
        assert row['original_triangle_count']==row['native_boundary_faces']*2
        paths=defaultdict(list)
        for leaf in e['terminal_cells']:paths[leaf['original_triangle_index']].append(leaf['binary_refinement_path'])
        assert set(paths)==set(range(row['original_triangle_count']))
        for leaves in paths.values():
            ordered=sorted(leaves);assert sum(Fraction(1,2**len(p)) for p in leaves)==1
            assert len(set(leaves))==len(leaves) and all(not b.startswith(a) for a,b in zip(ordered,ordered[1:]))
        assert row['upper_bound_mm']-row['lower_bound_mm']<=.05+1e-9
        f=next(r for r in forward['records'] if r['label_value']==row['label_value'])
        assert row['bidirectional_lower_bound_mm']==max(row['lower_bound_mm'],f['lower_bound_mm'])
        assert row['bidirectional_upper_bound_mm']==max(row['upper_bound_mm'],f['upper_bound_mm'])
        assert row['bidirectional_upper_bound_mm']-row['bidirectional_lower_bound_mm']<=.05+1e-9
        assert not row['source_voxels_or_model_changed'] and not row['clinical_approval']
    assert not summary['source_geometry_changed'] and not summary['clinical_approval'] and not summary['runtime_promoted']
