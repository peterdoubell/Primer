"""Original author correspondence must survive redistributed UIDs and cannot approve clinical geometry."""
import hashlib,io,json,math,zipfile
from pathlib import Path
import pytest
from tools.anatomy_sources.review_sunnybrook_source_parameters import OUT
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((OUT/name).read_text())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_original_case_members_and_geometry_are_linked_without_reusing_Uids():
    p=load('original-dicom-contour-linkage-review.json');cap={r['sop_uid']:r for r in load('native-cine-linkage-review.json')['linked_images']};assert p['original_case']=='SC-HF-I-01' and p['CAP_case']=='SCD0000101'
    archive=p['source_original_case_acquisition'];assert archive['author_archive_bytes']==208345315 and archive['publisher_full_archive_sha256']=='b0a54336316e09e801e8175edaa01a75c108bcfb87be7cacc16d5d044e01bd38' and not archive['full_archive_sha256_verified'] and archive['partial_archive_acquisition_explicit']
    assert len(p['original_images'])==240 and len({r['original_filename'] for r in p['original_images']})==240
    for row in p['original_images']:
        native=cap[row['CAP_sop_uid']];assert row['original_sop_uid']!=row['CAP_sop_uid']
        assert row['original_pixel_bytes_sha256']==native['native']['original_pixel_bytes_sha256']
        assert (row['original_filename_sequence_number']-1)%20==row['CAP_model_frame']==native['frame']
        assert row['original_and_CAP_geometry_equal']
        for key in ['image_position_patient','image_orientation_patient','pixel_spacing']:assert row[key]==native['native'][key]
    assert not p['clinical_EF_or_wall_mass_or_complete_anatomy_approved'] and not p['runtime_promoted']
def test_all_original_contours_retain_exact_original_image_and_phase_identity():
    p=load('original-dicom-contour-linkage-review.json');images={r['original_filename']:r for r in p['original_images']}
    assert p['author_contour_kind_counts']=={'icontour':18,'ocontour':9,'p1contour':3,'p2contour':3} and p['source_annotation_phases_one_based']==[8,19] and p['model_annotation_frames_zero_based']==[7,18]
    for row in p['original_contours']:
        raw=(OUT/row['file']).read_bytes();assert sha(raw)==row['sha256'];image=images[row['original_filename']]
        assert row['original_file_sha256']==image['original_file_sha256'] and row['CAP_sop_uid']==image['CAP_sop_uid'] and row['CAP_model_frame']==image['CAP_model_frame']
        assert Path(row['file']).name.split('-')[:3]==Path(row['original_filename']).stem.split('-')
        assert row['maximum_consecutive_or_closure_distance_pixels']<=math.sqrt(.5) and not row['original_contour_points_changed_or_repaired']
        if row['author_contour_kind']=='ocontour':assert row['original_phase_one_based']==19
    assert not p['exact_native_pixel_centre_offset_independently_verified']
def test_face_correspondence_is_stable_across_origins_without_clinical_approval():
    p=load('original-contour-model-correspondence-review.json');assert p['original_linkage_review_sha256']==sha((OUT/'original-dicom-contour-linkage-review.json').read_bytes()) and p['source_surface_sampling_review_sha256']==sha((OUT/'source-surface-sampling-review.json').read_bytes())
    assert len(p['comparisons'])==27
    for row in p['comparisons']:
        assert sha((OUT/row['source_contour_file']).read_bytes())==row['source_contour_sha256'];expected=0 if row['author_kind']=='icontour' else 1
        assert len(row['hypotheses'])==6 and {(h['plane_origin'],h['raw_contour_minus_offset_in_native_pixel_centre_coordinates']) for h in row['hypotheses']}=={(origin,offset) for origin in ['native_DICOM_origin','original_XML_fit_origin'] for offset in [0,.5,1]}
        for h in row['hypotheses']:
            assert h['nearest_fitted_source_face_xi3']==expected
            assert h['face_distances'][str(expected)]['mean_point_to_fitted_segment_distance_pixels']<h['face_distances'][str(1-expected)]['mean_point_to_fitted_segment_distance_pixels']
        assert not row['clinical_fit_accuracy_approved']
    for artifact in p['display_artifacts']:assert sha((OUT/artifact['file']).read_bytes())==artifact['sha256']
    for key in ['original_contours_or_model_changed','original_pixel_centre_convention_independently_calibrated','clinical_geometry_or_function_approval','papillary_contours_are_complete_3D_papillary_geometry','complete_reportable_structures_verified','runtime_promoted']:assert p[key] is False

def test_author_protocol_is_distinct_from_software_and_source_template_identity():
    p=load('original-converter-contour-protocol-review.json');assert p['published_converter_element_template_equals_original_after_explicit_focal_placeholder_substitution']
    assert p['primary_author_format_facts']['icontour_role']=='LV endocardial/inner contour' and p['primary_author_format_facts']['ocontour_role']=='LV epicardial/outer contour'
    assert p['primary_author_format_facts']['outer_contour_phase'].startswith('diastole') and '(0,0)' in p['primary_author_format_facts']['contour_coordinates']
    assert not p['original_CIM_model_inputs_available_or_conversion_replayed'] and not p['converter_revision_proven_exactly_used_for_this_case']
    assert p['evaluation_software_grant_scope']['software_license_version_ambiguity_preserved'] and p['evaluation_software_grant_scope']['source_code_inspected_not_embedded_or_executed']

def test_actual_original_and_CAP_pixel_geometry_replay_when_scientific_cache_available():
    pydicom=pytest.importorskip('pydicom');root=ROOT/'.research/native-cine-source-review';proof=load('original-dicom-contour-linkage-review.json')
    if not (root/proof['original_images'][0]['original_file']).exists():pytest.skip('Original offline case cache unavailable')
    import warnings
    with warnings.catch_warnings(),zipfile.ZipFile(root/'SCD_IMAGES_01.zip') as z:
        warnings.filterwarnings('ignore',message='Invalid value for VR UI:.*',category=UserWarning)
        for number in [48,59,88,99,108,119,128,139,208,219]:
            row=next(r for r in proof['original_images'] if r['original_filename_sequence_number']==number);original=(root/row['original_file']).read_bytes();cap=z.read(row['CAP_native_file']);assert sha(original)==row['original_file_sha256'] and sha(cap)==row['CAP_native_file_sha256'];a=pydicom.dcmread(io.BytesIO(original));b=pydicom.dcmread(io.BytesIO(cap));assert a.PixelData==b.PixelData and (a.pixel_array==b.pixel_array).all()
            assert list(a.ImagePositionPatient)==list(b.ImagePositionPatient) and list(a.ImageOrientationPatient)==list(b.ImageOrientationPatient) and list(a.PixelSpacing)==list(b.PixelSpacing)

def test_point_to_segment_distance_uses_edges_including_endpoints():
    pytest.importorskip('numpy')
    from tools.anatomy_sources.compare_sunnybrook_source_contours import distance_to_segments
    r=distance_to_segments([[1,1],[3,0]],[[[0,0],[2,0]]]);assert r['mean_point_to_fitted_segment_distance_pixels']==pytest.approx(1) and r['maximum_point_to_fitted_segment_distance_pixels']==pytest.approx(1)
