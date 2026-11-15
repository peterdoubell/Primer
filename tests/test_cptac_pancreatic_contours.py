"""Keep missing annotations unknown and bind every displayed source contour."""
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.review_cptac_pancreatic_contours import missing_indices


def test_sparse_annotations_do_not_become_negative_or_interpolated_planes():
    assert missing_indices([3, 4, 7]) == [5, 6]
    assert missing_indices([7, 4, 3]) == [5, 6]
    assert missing_indices([3, 4, 5]) == []
    with pytest.raises(ValueError, match='combination'):
        missing_indices([3, 3, 4])
    with pytest.raises(ValueError, match='No source'):
        missing_indices([])


def test_every_actual_contour_is_bound_to_original_audit_and_rendered_once():
    root=Path(__file__).resolve().parents[1]
    folder=root/'docs/cptac-pancreatic-contour-review'
    source_path=root/'docs/cptac-pancreatic-source-review/C3L-02112-original-geometry-review.json'
    source=json.loads(source_path.read_text())
    result=json.loads((folder/'contour-raster-review.json').read_text())
    assert result['source_geometry_sha256']==hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert result['source_contour_planes_interpolated'] is False
    assert result['ends_closed'] is False and result['cross_acquisition_registration_or_roi_merging'] is False
    assert result['clinical_approval'] is False and result['runtime_promoted'] is False
    assert [len(r['source_contours']) for r in result['records']]==[43,49]
    for record, original in zip(result['records'],source['records']):
        assert record['source_role']==original['source_role']
        assert record['ct_archive_sha256']==original['ct_archive_sha256']
        assert record['annotation_archive_sha256']==original['annotation_archive_sha256']
        observed={c['source_contour_index']:(c['native_plane_index'],c['referenced_ct_sop']) for c in record['source_contours']}
        expected={c['source_contour_index']:(c['native_sorted_plane_index'],c['referenced_ct_sop']) for c in original['contours']}
        assert observed==expected
        displayed=[i for f in record['figures'] for i in f['contour_indices']]
        assert sorted(displayed)==sorted(observed) and len(displayed)==len(set(displayed))
        for f in record['figures']+record['unannotated_acquired_planes_inside_contour_span']:
            assert hashlib.sha256((folder/f['file']).read_bytes()).hexdigest()==f['sha256']
        assert record['array_is_contiguous_3d_mask'] is False
        assert record['unannotated_planes_filled'] is False
        assert record['slab_volume_is_validated_lesion_volume'] is False
        assert all(n>0 for n in record['positive_selected_pixels_on_first_and_last_contour_planes'])
        assert record['roi_volume_semantics_or_end_surface_definition_reconciled'] is False
        for c in record['source_contours']:
            for direction in ['source_to_raster_boundary','raster_to_source_boundary']:
                distance=c[direction]
                assert distance['conservative_whole_boundary_upper_bound_mm']>=distance['maximum_sample_to_segment_distance_mm']
                assert distance['maximum_arclength_sample_gap_mm']<=.125+1e-12
    assert result['records'][0]['unannotated_acquired_planes_inside_contour_span']==[]
    gaps=result['records'][1]['unannotated_acquired_planes_inside_contour_span']
    assert [g['native_plane_index'] for g in gaps]==[534,535]
    assert all(g['label_state']=='unannotated_not_negative' for g in gaps)
