"""Native mesh/label distances retain discrete-surface and coverage limits."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/spl-wall-source-review'


def test_exact_rectangle_search_matches_all_faces_brute_force_and_anisotropic_cell():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.compare_spl_wall_label_boundaries import cell_faces,closest_faces
    spacing=np.array([1.,2.,3.]);mask=np.zeros((3,3,3),bool);mask[1,1,1]=True
    centers,axes,voxels,exterior=cell_faces(mask,spacing)
    assert len(centers)==6 and not exterior.any()
    rng=np.random.default_rng(376);points=rng.uniform(-4,8,(100,3))
    points[0]=[1,2,3];points[1]=[1.5,2,3]
    rows,radius=closest_faces(points,centers,axes,spacing)
    half=np.tile(spacing*.5,(6,1));half[np.arange(6),axes]=0
    expected=np.linalg.norm(np.maximum(np.abs(points[:,None]-centers)-half,0),axis=2).min(1)
    assert np.allclose([r['distance_mm'] for r in rows],expected,rtol=0,atol=1e-12)
    assert rows[0]['distance_mm']==pytest.approx(.5) and rows[1]['distance_mm']==0
    assert radius==pytest.approx((2**2+3**2)**.5/2)
    # Adjacent native labelled cells must not create a false internal boundary.
    mask[1,1,2]=True;faces,*_=cell_faces(mask,spacing);assert len(faces)==10


def test_complete_original_vertex_accounting_and_distance_evidence():
    summary=json.loads((REVIEW/'label-boundary-comparison-summary.json').read_text())
    native=json.loads((REVIEW/'independent-wall-source-review.json').read_text())
    assert summary['source_review_sha256']==hashlib.sha256((REVIEW/'independent-wall-source-review.json').read_bytes()).hexdigest()
    assert len(summary['records'])==5 and sum(r['vertices'] for r in summary['records'])==113650
    for row in summary['records']:
        packed=(REVIEW/row['file']).read_bytes();raw=gzip.decompress(packed);e=json.loads(raw)
        assert hashlib.sha256(packed).hexdigest()==row['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest()==row['uncompressed_sha256']
        assert row['all_original_vertices_compared']
        assert [r['source_vertex_index'] for r in e['vertex_comparisons']]==list(range(row['vertices']))
        assert max(r['distance_mm'] for r in e['vertex_comparisons'])==row['maximum_vertex_distance_mm']
        assert len(e['boundary_centers_native_axis_mm'])==row['boundary_faces']
        assert len(e['boundary_normal_axis'])==len(e['boundary_source_voxel_ijk'])==row['boundary_faces']
        assert not e['continuous_anatomical_surface_is_voxel_cell_union'] and not e['source_voxels_or_geometry_changed']
        assert not row['vertex_distance_is_full_surface_hausdorff_distance']
        assert not row['anatomical_accuracy_or_acceptance_threshold_verified']
    assert not summary['source_geometry_changed'] and not summary['clinical_approval'] and not summary['runtime_promoted']
