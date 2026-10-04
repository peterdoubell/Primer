"""Source decimal polylines preserve geometry and cannot imply a solid lesion."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.export_cptac_pancreatic_contour_geometry import decimal_text


def test_original_decimal_strings_survive_without_float_reformatting():
    pydicom=pytest.importorskip('pydicom')
    for text in ['1.2300','-.400','2.50E-2','-216.875']:
        value=pydicom.valuerep.DSfloat(text)
        assert decimal_text(value)==text
        assert Decimal(decimal_text(value))==Decimal(text)


def test_actual_source_vertices_and_metadata_keep_surface_unknown():
    root=Path(__file__).resolve().parents[1]
    folder=root/'docs/cptac-pancreatic-contour-geometry'
    p=json.loads((folder/'original-contour-geometry.json').read_text())
    original_path=root/'docs/cptac-pancreatic-source-review/C3L-02112-original-geometry-review.json'
    original=json.loads(original_path.read_text())
    assert p['source_geometry_sha256']==hashlib.sha256(original_path.read_bytes()).hexdigest()
    readback=json.loads((folder/'original-coordinate-readback.json').read_text())
    assert readback['geometry_file_sha256']==hashlib.sha256((folder/'original-contour-geometry.json').read_bytes()).hexdigest()
    assert [r['original_decimal_components_compared'] for r in readback['independent_original_archive_readback']]==[11406,13341]
    assert all(r['exact_original_string_equality'] for r in readback['independent_original_archive_readback'])
    assert p['source_points_transformed_or_repaired'] is False
    assert p['solid_surface_created'] is False and p['cross_acquisition_registration'] is False
    assert p['clinical_approval'] is False and p['runtime_promoted'] is False
    assert hashlib.sha256((folder/p['figure']['file']).read_bytes()).hexdigest()==p['figure']['sha256']
    assert [sum(c['points'] for c in r['source_contours']) for r in p['records']]==[3802,4447]
    for record,source in zip(p['records'],original['records']):
        assert record['source_role']==source['source_role']
        assert record['annotation_archive_sha256']==source['annotation_archive_sha256']
        assert record['source_pixel_plane_grid_declared'] is False
        assert record['dicom_grid_specific_absent_roi_rule_applicable'] is False
        assert record['source_explicit_volume_algorithm_available'] is False
        assert all(r['csv_and_dicom_roi_volume_equal'] for r in record['source_rois'])
        assert all(not r['roi_generation_description_present'] and not r['roi_derivation_algorithm_identification_present'] for r in record['source_rois'])
        expected={c['source_contour_index']:c for c in source['contours']}
        assert len(record['source_contours'])==len(expected)
        for c in record['source_contours']:
            reference=expected[c['source_contour_index']]
            assert c['source_ct_sop']==reference['referenced_ct_sop']
            assert c['native_plane_index']==reference['native_sorted_plane_index']
            assert c['points']==reference['source_contour_points']
            raw=c['source_decimal_lps_xyz_mm']
            assert len(raw)==c['points']*3 and all(isinstance(v,str) for v in raw)
            assert all(Decimal(v).is_finite() for v in raw)
            assert {Decimal(v) for v in raw[2::3]}=={Decimal(str(reference['source_plane_position_lps'][2]))}
            assert c['contour_slab_thickness_present'] is False and c['contour_offset_vector_present'] is False
