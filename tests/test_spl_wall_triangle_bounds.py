"""Continuous forward certificates cover all original triangles, not just their vertices."""
from collections import defaultdict
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/spl-wall-source-review'


def test_lipschitz_certificate_detects_an_interior_peak_missed_by_vertices():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.bound_spl_wall_triangle_interiors import certify
    triangle=np.array([[[0,0,0],[2,0,0],[0,2,0]]],float)
    # Distance to the three source corners is zero at vertices, positive inside.
    def distance(points):return np.linalg.norm(points[:,None]-triangle[0],axis=2).min(1)
    result=certify(triangle,distance,error=.02)
    assert result['lower_bound_mm']>1.38
    assert result['lower_bound_mm']<=2**.5<=result['upper_bound_mm']
    assert result['bound_width_mm']<=.02+1e-10
    with pytest.raises(ValueError):certify(triangle,distance,error=0)


def test_every_original_triangle_has_a_complete_nonoverlapping_terminal_cover():
    summary=json.loads((REVIEW/'triangle-distance-bound-summary.json').read_text())
    assert summary['all_five_original_models_complete'] and len(summary['records'])==5
    assert sum(r['original_triangle_count'] for r in summary['records'])==224612
    for r in summary['records']:
        packed=(REVIEW/r['file']).read_bytes();raw=gzip.decompress(packed);proof=json.loads(raw)
        assert hashlib.sha256(packed).hexdigest()==r['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest()==r['uncompressed_sha256']
        paths=defaultdict(list)
        for leaf in proof['terminal_cells']:
            paths[leaf['original_triangle_index']].append(leaf['binary_refinement_path'])
            assert leaf['upper_bound_mm']==pytest.approx(leaf['centroid_distance_mm']+leaf['cover_radius_mm']+1e-10,abs=1e-13)
        assert set(paths)==set(range(r['original_triangle_count']))
        for leaves in paths.values():
            ordered=sorted(leaves)
            assert sum(Fraction(1,2**len(path)) for path in leaves)==1
            assert len(set(leaves))==len(leaves)
            assert all(not b.startswith(a) for a,b in zip(ordered,ordered[1:]))
        assert r['upper_bound_mm']==max(l['upper_bound_mm'] for l in proof['terminal_cells'])
        assert r['upper_bound_mm']-r['lower_bound_mm']<=.05+1e-9
        assert r['lower_bound_mm']>=r['vertex_maximum_distance_mm']
        assert not r['source_triangles_changed'] and r['analysis_subdivision_only']
        assert not r['reverse_surface_distance_verified'] and not r['clinical_approval']


def test_independent_original_strip_and_native_label_evidence_remain_pinned():
    summary=json.loads((REVIEW/'triangle-distance-bound-summary.json').read_text())
    source=json.loads((REVIEW/'independent-wall-source-review.json').read_text())
    for row in summary['records']:
        original=next(r for r in source['records'] if r['label_value']==row['label_value'])
        assert row['source_vtk_sha256']==original['source_vtk_sha256']
        assert row['original_triangle_count']==original['analysis_triangles']
        assert row['source_review_sha256']==hashlib.sha256((REVIEW/'independent-wall-source-review.json').read_bytes()).hexdigest()
        assert row['reference_is_native_label_cell_union']
    assert not summary['source_geometry_changed'] and not summary['clinical_approval'] and not summary['runtime_promoted']
