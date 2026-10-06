"""Original AVT labels, derived surfaces and commercial/clinical approval remain distinct."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.review_avt_r6_source import CT_SHA,MASK_SHA,META_SHA

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/avt-r6-native-source-review'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def proof():return json.loads((FOLDER/'native-source-review.json').read_text())


def test_original_case_mask_metadata_and_range_integrity_remain_exact():
    p=proof();assert p['original_ct_sha256']==CT_SHA and p['original_mask_sha256']==MASK_SHA
    raw=(FOLDER/'original-R6.seg.nrrd').read_bytes();assert sha(raw)==MASK_SHA and len(raw)==418228
    header,packed=raw.split(b'\n\n',1);decoded=gzip.decompress(packed)
    assert sha(decoded)==p['original_mask_voxel_uint8_sha256'] and len(decoded)==278921216
    assert p['mask_voxel_counts']=={'0':277646142,'1':1275074}
    assert sha((FOLDER/'source-metadata.json').read_bytes())==META_SHA
    a=json.loads((FOLDER/'original-range-acquisition.json').read_text());assert a['consistent_etag_verified']
    assert len({r['etag'] for r in a['requests']})==1
    assert {r['sha256'] for r in a['records']}=={CT_SHA,MASK_SHA}
    assert all(not r['archive_full_md5_verified'] for r in a['records'])


def test_source_grid_and_annotation_status_do_not_imply_finished_anatomical_review():
    p=proof();assert p['ct_grid_shape_zyx']==p['mask_grid_shape_zyx']==[1064,512,512]
    assert p['maximum_source_basis_difference_native_units']<1e-12 and p['maximum_source_origin_difference_native_units']<1e-12
    assert p['mask_6_connected_components']==4 and p['mask_component_voxel_counts']==[1274179,18,762,115]
    assert p['source_segment_status_tag']=='Segmentation.Status:inprogress'
    for key in ['grid_correspondence_is_independent_anatomical_validation','source_segment_status_is_independent_finished_review',
                'case_specific_annotator_or_independent_reader_verified','ct_hu_or_bolus_timing_verified',
                'highest_resolution_acquired_master_verified',
                'source_labels_separate_every_reportable_structure','clinical_approval','runtime_promoted','structure_coverage_granted']:
        assert p[key] is False
    assert not p['exact_underlying_tcia_case_version_linkage_verified']
    assert p['commercial_runtime_rights_clearance_status'].startswith('verified_current_source_')
    assert p['physical_space_units_independently_verified'] and p['ct_hu_calibration_verified'] and p['exact_underlying_series_linkage_verified']
    evidence=p['verified_original_dicom_linkage']
    assert sha((ROOT/evidence['evidence_path']).read_bytes())==evidence['evidence_sha256']
    assert p['dataset_description_inherits_upstream_collection_terms']


def test_derived_arrays_are_bound_but_do_not_replace_source_geometry_or_labels():
    s=proof()['derived_surface']
    positions=gzip.decompress((FOLDER/'mask-isosurface-positions.f64.gz').read_bytes())
    triangles=gzip.decompress((FOLDER/'mask-isosurface-triangles.u32.gz').read_bytes())
    assert len(positions)==s['positions']*24 and len(triangles)==s['triangles']*12
    assert (s['positions'],s['triangles'])==(272202,544138)
    assert sha(positions)==s['positions_sha256'] and sha(triangles)==s['triangles_sha256']
    assert s['boundary_edges']==270 and s['nonmanifold_edges']==0
    assert not s['source_padding_or_caps_added'] and not s['smoothing_or_decimation_applied']
    assert not s['mask_conversion_is_original_delivered_geometry'] and not s['branch_or_wall_anatomical_identity_independently_reviewed']
    assert s['normals_are_derived_not_original_source_samples'] and not s['clinical_approval'] and not s['runtime_promoted']
    r=json.loads((FOLDER/'render-review.json').read_text())
    assert r['native_source_review_sha256']==sha((FOLDER/'native-source-review.json').read_bytes())
    assert r['display_window_stored_values']==[800,1600] and r['view_limits_padding_fraction']==.08
    assert len(r['native_slice_indices'])==12
    for image in r['images']:assert sha((FOLDER/image['file']).read_bytes())==image['sha256']
    assert not r['ct_resampled'] and not r['mask_edited'] and not r['independent_anatomical_validation']


def test_nrrd_parser_keeps_slicer_status_and_rejects_bad_types_or_voxel_counts():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_avt_r6_source import read_nrrd
    header=b'NRRD0004\ntype: unsigned char\ndimension: 3\nspace: left-posterior-superior\nsizes: 2 2 1\nencoding: gzip\nSegment0_Tags:=Segmentation.Status:inprogress|\n\n'
    f,a=read_nrrd(header+gzip.compress(bytes([0,1,1,0])))
    assert f['Segment0_Tags']=='Segmentation.Status:inprogress|' and a.shape==(1,2,2)
    assert np.array_equal(a,[[[0,1],[1,0]]])
    with pytest.raises(ValueError,match='sample count'):read_nrrd(header+gzip.compress(bytes([0,1,1])))
    with pytest.raises(ValueError,match='sample type'):read_nrrd(header.replace(b'unsigned char',b'float')+gzip.compress(bytes([0,1,1,0])))


def test_original_ct_voxels_and_every_derived_vertex_use_source_grid_coordinates():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_avt_r6_source import read_nrrd
    from tools.anatomy_sources.review_aaa_kinematic_source import grid_transform
    ct_path=ROOT/'.research/avt-native-source-review/R6.nrrd'
    if not ct_path.exists():pytest.skip('Original research CT is not installed')
    p=proof();raw=ct_path.read_bytes();cf,ct=read_nrrd(raw)
    assert sha(raw)==CT_SHA and ct.shape==(1064,512,512) and sha(ct.tobytes())==p['original_ct_voxel_int16_sha256']
    mf,mask=read_nrrd((FOLDER/'original-R6.seg.nrrd').read_bytes());basis,origin=grid_transform(mf)
    positions=np.frombuffer(gzip.decompress((FOLDER/'mask-isosurface-positions.f64.gz').read_bytes()),'<f8').reshape(-1,3)
    ijk=(positions*[-1,-1,1]-origin)@np.linalg.inv(basis).T
    # Binary 0.5 isosurfaces lie at integer/half-integer native grid positions.
    assert np.max(np.abs(ijk*2-np.rint(ijk*2)))<1e-9
    assert np.all(ijk>=0) and np.all(ijk<=np.array(mask.shape[::-1])-1)
    assert p['stored_ct_value_range']==[-2000,4095]
