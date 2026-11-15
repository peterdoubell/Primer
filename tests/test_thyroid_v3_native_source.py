import gzip,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/thyroid-native-source-review/s0358'
def test_current_source_case_preserves_all_channels_and_open_boundary_geometry():
    r=json.loads((OUT/'native-source-review.json').read_text());a=json.loads((OUT/'original-acquisition.json').read_text())
    assert r['case']=='s0358' and r['actual_dataset_license']['id']=='cc-by-4.0'
    assert hashlib.sha256((OUT/'original-acquisition.json').read_bytes()).hexdigest()==r['source_acquisition_sha256']
    assert len(a['records'])==len(r['original_files'])==9 and len(r['targets'])==8
    assert a['publisher_archive_size_and_checksum_unchanged_before_after']
    assert not a['archive_entity_tag_available'] and not a['source_object_immutability_independently_verified'] and not a['full_archive_MD5_verified']
    assert a['source_metadata_rows'][0]['study_type']=='ct pelvis' and a['source_metadata_rows'][0]['pathology_location']=='abdomen'
    assert all(x['all_original_samples_match_independent_reader'] and x['dimensions']==[255,255,523] for x in r['original_files'])
    assert r['all_selected_source_grids_identical'] and r['source_axes']==['R','A','S']
    targets={x['file']:x for x in r['targets']};assert targets['thyroid_gland.nii.gz']['source_volume_boundary_axes']==[]
    for side in ['left','right']:
        assert targets[f'common_carotid_artery_{side}.nii.gz']['source_volume_boundary_axes']==[2]
        assert targets[f'common_carotid_artery_{side}.nii.gz']['boundary_edges']>0
    assert sum(x['triangles'] for x in r['targets'])==52040
    for x in r['targets']:
        assert not x['source_components_deleted_or_repaired']
        stem=x['file'].removesuffix('.nii.gz');positions=gzip.decompress((OUT/(stem+'-positions.f64.gz')).read_bytes());faces=gzip.decompress((OUT/(stem+'-triangles.u32.gz')).read_bytes())
        assert len(positions)==x['vertices']*24 and hashlib.sha256(positions).hexdigest()==x['positions_sha256']
        assert len(faces)==x['triangles']*12 and hashlib.sha256(faces).hexdigest()==x['triangles_sha256']
        assert max(v[0] for v in struct.iter_unpack('<I',faces))<x['vertices']
    for key in ['clinical_approval','structure_coverage_granted','runtime_promoted','source_study_type_is_dedicated_neck_CT','single_thyroid_class_independently_identifies_lobes_isthmus_capsule_internal_nodules_or_every_interface','source_CT_annotations_supply_US_echogenicity_Doppler_or_matched_published_US_cases','native_DICOM_physical_calibration_contrast_phase_or_tiny_wall_resolution_verified']:
        assert r[key] is False
