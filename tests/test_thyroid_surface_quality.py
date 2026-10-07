import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/thyroid-native-source-review/s0358'
def test_source_components_openings_and_localised_residuals_are_not_repaired():
    r=json.loads((OUT/'surface-quality-review.json').read_text())
    assert r['native_source_review_sha256']==hashlib.sha256((OUT/'native-source-review.json').read_bytes()).hexdigest()
    assert len(r['surface_checks'])==8 and r['all_source_triangles_rendered_without_decimation']
    assert not r['display_colours_are_original_photographic_tissue_colours']
    assert not r['independent_anatomical_review_complete'] and not r['clinical_approval'] and not r['runtime_promoted']
    checks={x['file']:x for x in r['surface_checks']};gland=checks['thyroid_gland.nii.gz']
    assert gland['surface_connected_components']==2 and gland['component_triangle_counts']==[2308,4294]
    for side in ['left','right']:assert checks[f'common_carotid_artery_{side}.nii.gz']['boundary_edges']==22
    assert {x['file'] for x in r['surface_checks'] if x['vertices_with_nonzero_field_residual']}=={'thyroid_gland.nii.gz','esophagus.nii.gz','brachiocephalic_vein_left.nii.gz'}
    assert sum(len(x['vertices_with_nonzero_field_residual']) for x in r['surface_checks'])==3
    for row in r['surface_checks']:
        assert row['all_vertices_finite'] and row['all_vertices_inside_original_mask_grid']
        assert row['degenerate_triangle_count']==row['nonmanifold_edges']==0
        assert sum(row['component_triangle_counts'])==row['triangles']
        assert not row['source_components_faces_or_boundaries_repaired'] and not row['field_residual_is_geometric_distance_or_anatomical_accuracy']
        assert row['original_interpolated_binary_field_residual_max']<=.125000000001
        for vertex in row['vertices_with_nonzero_field_residual']:
            assert 0<=vertex['vertex_index']<row['vertices']
            assert len(vertex['source_voxel_coordinates'])==len(vertex['source_world_coordinates'])==3
