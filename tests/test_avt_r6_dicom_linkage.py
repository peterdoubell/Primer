"""Complete source identity/calibration does not approve mask anatomy or whole-module fidelity."""
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.verify_avt_r6_dicom_linkage import SERIES,MANIFEST_SHA,INDEX_SHA
from tools.anatomy_sources.review_avt_r6_source import CT_SHA,MASK_SHA

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/avt-r6-dicom-linkage-review'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def proof():return json.loads((FOLDER/'complete-dicom-linkage-review.json').read_text())


def test_every_source_instance_and_original_pixel_is_bound_to_the_correct_collection():
    p=proof();assert p['source_series']['SeriesInstanceUID']==SERIES
    assert p['source_series']['collection_id']=='rider_lung_pet_ct' and p['source_doi']=='10.7937/k9/tcia.2015.ofip7tvm'
    assert p['publisher_idc_index_sha256']==INDEX_SHA and p['source_object_manifest_sha256']==MANIFEST_SHA
    assert sha((FOLDER/'original-dicom-object-manifest.json').read_bytes())==MANIFEST_SHA
    assert p['original_ct_sha256']==CT_SHA and p['original_mask_sha256']==MASK_SHA
    assert p['original_dicom_instance_count']==len(p['records'])==1064 and p['verified_original_pixel_count']==278921216
    assert {r['voxel_k'] for r in p['records']}==set(range(1064)) and len({r['SOPInstanceUID'] for r in p['records']})==1064
    for r in p['records']:
        assert r['all_source_slice_pixels_equal_nrrd'] and r['dicom_etag_md5_verified']
        assert r['Rows']==r['Columns']==512 and r['PixelSpacing_mm']==[.724609,.724609]
        assert r['ImagePositionPatient_mm']==[-185.5,-185.5,-655.375+r['voxel_k']*.625]
        assert r['ImageOrientationPatient']==[1,0,0,0,1,0]
        assert (r['RescaleSlope'],r['RescaleIntercept'],r['RescaleType'],r['PixelPaddingValue'])==(1,-1024,'HU',-2000)
    assert p['source_physical_space_units_verified']=='mm_from_original_DICOM'
    assert p['original_padding_voxel_count']==57590033 and not p['original_volume_modified']


def test_current_grants_and_attribution_do_not_invent_export_version_or_clinical_approval():
    p=proof();d=json.loads((FOLDER/'original-source-doi-metadata.json').read_text())['data']['attributes']
    assert sha((FOLDER/'original-source-doi-metadata.json').read_bytes())==p['source_doi_metadata_sha256']
    assert p['creators_as_recorded_in_original_doi_metadata']==d['creators']
    assert p['source_license']=='CC BY 3.0' and p['mask_producer_license']=='CC BY 4.0'
    assert p['source_ct_and_mask_commercial_reuse_grants_verified']
    assert any(r.get('rightsIdentifier')=='cc-by-3.0' for r in d['rightsList'])
    assert sha((FOLDER/'original-collection-license-rows.json').read_bytes())==p['official_collection_license_rows_sha256']
    for key in ['original_avt_export_tcia_release_version_verified','bolus_timing_or_arterial_phase_verified',
                'highest_resolution_acquired_master_verified','case_diagnosis_independently_confirmed',
                'mask_boundary_or_branch_identity_independently_reviewed','clinical_approval','runtime_promoted','structure_coverage_granted']:
        assert p[key] is False
    assert any('RIDER Lung CT' in s and 'RIDER Lung PET-CT' in s for s in p['limits'])


def test_native_packet_inherits_only_verified_source_calibration_and_keeps_geometry_hashes():
    p=proof();n=json.loads((ROOT/'docs/avt-r6-native-source-review/native-source-review.json').read_text())
    e=n['verified_original_dicom_linkage'];assert e['SeriesInstanceUID']==SERIES
    assert sha((ROOT/e['evidence_path']).read_bytes())==e['evidence_sha256']
    assert n['ct_hu_calibration_verified'] and n['physical_space_units_independently_verified']
    assert not n['ct_hu_or_bolus_timing_verified'] and not n['ct_bolus_timing_verified']
    assert n['derived_surface']['positions_sha256']=='2e327360f32ebc59239bdd8368f4e0e9db1b75dd2652492c63c71fda0f805083'
    assert n['derived_surface']['triangles_sha256']=='01025e8163bef96d11f94a44e19c0ab7a9d42c4fd10ccca9136721891b0678af'
    assert not n['clinical_approval'] and not n['structure_coverage_granted']


def test_rejected_candidate_is_not_accepted_by_image_count_or_coarse_shape():
    candidates=json.loads((FOLDER/'original-candidate-sample-geometries.json').read_text())
    assert candidates[0]['SeriesInstanceUID']!=SERIES and candidates[1]['SeriesInstanceUID']==SERIES
    assert candidates[0]['PixelSpacing']!='[0.724609, 0.724609]'
    assert candidates[0]['ImagePositionPatient']!=candidates[1]['ImagePositionPatient']


def test_complete_cached_original_pixels_reproduce_the_recorded_slice_hashes():
    np=pytest.importorskip('numpy');pydicom=pytest.importorskip('pydicom')
    from tools.anatomy_sources.review_avt_r6_source import read_nrrd
    root=ROOT/'.research/avt-native-source-review'
    if not (root/'r6-matched-dicom').exists():pytest.skip('Original research DICOM cache is not installed')
    _,ct=read_nrrd((root/'R6.nrrd').read_bytes())
    for r in proof()['records']:
        path=root/'r6-matched-dicom'/Path(r['object_key']).name;raw=path.read_bytes()
        assert sha(raw)==r['dicom_sha256']
        pixels=pydicom.dcmread(path).pixel_array
        assert np.array_equal(pixels,ct[r['voxel_k']]) and sha(pixels.astype('<i2').tobytes())==r['stored_pixel_int16_sha256']
