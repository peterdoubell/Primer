"""Original source model/contour evidence cannot imply calibrated native motion or repaired anatomy."""
import hashlib,json
from pathlib import Path
import pytest
from tools.anatomy_sources.review_sunnybrook_source_parameters import parse_exnode
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/sunnybrook-native-source-review'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_source_identity_and_actual_cc0_grant_are_preserved():
    p=json.loads((OUT/'original-parameter-source-review.json').read_text());assert p['license']=='CC0 1.0 Universal'
    assert 'Sunnybrook Hospital' in (OUT/'CC0_License.htm').read_text() and 'both DICOM studies and associated contours' in (OUT/'README.txt').read_text()
    assert p['source_clinical_record']['PatientID']=='SCD0000101' and p['source_clinical_record']['OriginalID']=='SC-HF-I-1' and p['source_clinical_records']==45
    assert len(p['source_model_members'])==22 and len(p['source_manual_contours'])==33
    for row in p['source_model_members']+p['source_manual_contours']:
        assert sha((OUT/row['file']).read_bytes())==row['sha256'] and row['zip_crc_verified']
def test_all_original_parameters_and_normalized_phase_mapping_are_exact():
    p=json.loads((OUT/'original-parameter-source-review.json').read_text());data=json.loads((OUT/'original-model-parameters.json').read_text())
    assert len(data['frames'])==20 and data['coordinate_system']=='original_prolate_spheroidal' and not data['cartesian_conversion_or_mesh_generated']
    for f in data['frames']:
        raw=(OUT/'original-case-model'/f'SCD0000101_{f["source_file_phase"]}.model.exnode').read_bytes();focus,nodes=parse_exnode(raw)
        assert focus==f['focus']==35.8171 and nodes==f['nodes'] and len(nodes)==40
    assert [(r['frame'],r['file']) for r in p['source_frame_refs']]==[(n,f'SCD0000101_{n+1}.model.exnode') for n in range(20)]
    assert p['original_output_interval']=='0.05' and not p['interval_converted_to_milliseconds'] and len(p['source_image_refs'])==360
    assert not p['transform_interpretation_independently_validated'] and not p['model_motion_is_original_native_cine'] and not p['clinical_approval'] and not p['runtime_promoted']
def test_wrong_coordinate_system_or_missing_node_cannot_be_parsed_as_source():
    raw=(OUT/'original-case-model/SCD0000101_1.model.exnode').read_bytes()
    with pytest.raises(ValueError,match='coordinate system'):parse_exnode(raw.replace(b'prolate spheroidal',b'rectangular cartesian'))
    changed=raw.replace(b'Node:                           40',b'Node:                           41')
    if changed==raw:
        import re
        changed=re.sub(rb'Node:\s*40\s',b'Node: 41\n',raw,count=1)
    with pytest.raises(ValueError,match='node set'):parse_exnode(changed)

def test_original_field_layout_cannot_silently_change_derivative_meanings():
    raw=(OUT/'original-case-model/SCD0000101_1.model.exnode').read_bytes()
    with pytest.raises(ValueError,match='field layout'):
        parse_exnode(raw.replace(b'd/ds1,d/ds2,d2/ds1ds2',b'd/ds2,d/ds1,d2/ds1ds2'))

def test_native_linkage_preserves_patient_planes_timing_and_uid_defects():
    from collections import defaultdict
    p=json.loads((OUT/'native-cine-linkage-review.json').read_text());original=json.loads((OUT/'original-parameter-source-review.json').read_text())
    assert p['source_archive']['sha256']=='708ce04db1ac33948a00b9052d44e9548c6807121a4841f4c35080d6db127b72'
    assert p['source_archive']['bytes']==433585535 and p['native_case_dicom_members']==1047
    assert len(p['linked_images'])==360 and len({r['sop_uid'] for r in p['linked_images']})==360
    assert {r['sop_uid'] for r in original['source_image_refs']}=={r['sop_uid'] for r in p['linked_images']}
    groups=defaultdict(list)
    for row in p['linked_images']:
        native=row['native'];groups[(row['label'],row['slice'])].append(row)
        assert row['sop_uid']==native['sop_uid'] and row['series_uid']==native['series_uid']
        assert native['zip_crc_verified'] and native['source_pixels_independently_decoded_equal']
        assert native['rows']==native['columns']==256 and native['pixel_dtype']=='signed_int16' and native['bits_stored']==16
        assert native['photometric_interpretation']=='MONOCHROME2' and native['rescale_slope']==1 and native['rescale_intercept']==0
    assert len(groups)==18
    for rows in groups.values():
        rows.sort(key=lambda r:r['frame']);assert [r['frame'] for r in rows]==list(range(20))
        assert len({r['native']['original_pixel_bytes_sha256'] for r in rows})==20
        assert len({tuple(r['native']['image_position_patient']) for r in rows})==1
        assert len({tuple(r['native']['image_orientation_patient']) for r in rows})==1
        times=[r['native']['trigger_time_ms'] for r in rows];assert all(b>a for a,b in zip(times,times[1:]))
    assert len({v for group in p['phase_groups'] for v in group['nominal_intervals_ms']})>1
    assert not p['all_groups_are_same_simultaneous_heartbeat'] and p['source_uid_nonconformance_preserved']
    assert any({'CINESAX_300','CINELAX_301','PERF_303'}<=set(r['folders']) for r in p['series_uid_shared_across_folders'])
    for key in ['independent_scanner_phantom_calibration_verified','model_transform_basis_in_patient_frame_verified','contour_pixel_index_native_linkage_verified','clinical_quantitative_function_validated','full_anatomical_validation','clinical_approval','runtime_promoted']:
        assert p[key] is False

def test_native_pixels_replay_against_preserved_linkage_when_source_cache_is_available():
    # Replay actual original data, rather than trusting self-reported counts/hashes.
    import io,struct,zipfile
    source=ROOT/'.research/native-cine-source-review/SCD_IMAGES_01.zip'
    if not source.exists():pytest.skip('Original large offline source archive not present')
    pydicom=pytest.importorskip('pydicom')
    import warnings
    p=json.loads((OUT/'native-cine-linkage-review.json').read_text())
    with warnings.catch_warnings(),zipfile.ZipFile(source) as z:
        warnings.filterwarnings('ignore',message='Invalid value for VR UI:.*',category=UserWarning)
        for label in ['LA1','SA1','SA6','SA12']:
            for frame in [0,10,19]:
                row=next(r for r in p['linked_images'] if r['label']==label and r['frame']==frame)
                raw=z.read(row['native']['member']);assert sha(raw)==row['native']['sha256']
                ds=pydicom.dcmread(io.BytesIO(raw));assert str(ds.SOPInstanceUID)==row['sop_uid']
                assert sha(ds.PixelData)==row['native']['original_pixel_bytes_sha256']
                assert tuple(int(v) for v in ds.pixel_array.ravel())==struct.unpack('<65536h',ds.PixelData)

def test_original_element_connectivity_and_basis_are_preserved_without_surface_invention():
    from tools.anatomy_sources.review_sunnybrook_source_parameters import parse_exelem
    raw=(OUT/'original-case-model/GlobalHermiteParam.exelem').read_bytes();p=json.loads((OUT/'original-element-topology.json').read_text())
    assert parse_exelem(raw)==p['source_elements'] and len(p['source_elements'])==16
    assert {n for e in p['source_elements'] for n in e['source_node_ids']}==set(range(1,41))
    assert p['theta_modification']=='decreasing_in_xi1' and not p['source_connectivity_or_scale_factors_changed'] and not p['surface_tessellation_or_clinical_geometry_validated']
    with pytest.raises(ValueError,match='basis'):
        parse_exelem(raw.replace(b'decreasing in xi1',b'no modify'))
    with pytest.raises(ValueError,match='element set'):
        parse_exelem(raw.replace(b'Element:           16 0 0',b'Element:           17 0 0'))

def test_display_artifacts_are_bound_to_exact_native_frames_without_quantitative_claims():
    p=json.loads((OUT/'native-display-review.json').read_text());link=json.loads((OUT/'native-cine-linkage-review.json').read_text());by_sop={r['sop_uid']:r for r in link['linked_images']}
    assert not p['source_pixels_changed'] and not p['interpolated_frames_or_voxels'] and not p['model_transform_or_geometry_validated_by_display'] and not p['clinical_approval']
    for artifact in p['artifacts']:
        assert sha((OUT/artifact['file']).read_bytes())==artifact['sha256']
        for frame in artifact['native_frames']:
            native=by_sop[frame['sop_uid']];assert (frame['label'],frame['frame'])==(native['label'],native['frame'])
            assert frame['source_pixel_bytes_sha256']==native['native']['original_pixel_bytes_sha256']
    frames=p['artifacts'][0]['native_frames'];assert len(frames)==20 and {r['label'] for r in frames}=={'SA6'} and [r['frame'] for r in frames]==list(range(20))
