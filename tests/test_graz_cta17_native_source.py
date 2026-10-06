"""Separate source labels, native coordinates, expert provenance and full clinical coverage are distinct."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.review_graz_cta17_source import HASHES

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/graz-cta17-native-source-review'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def proof():return json.loads((FOLDER/'paired-lumen-source-review.json').read_text())

def test_original_annotations_and_mesh_bytes_preserve_label_identity_and_source_review():
    r=proof();assert r['source_case']=='cta17' and r['dataset_license']=='CC BY 4.0'
    assert r['source_publication_final_expert_checks']==['Christian Mayer','Johannes Schmid','Heinrich Mächler']
    assert r['source_table_annotator_tier']=='cardiac_surgery_resident' and r['source_table_segmentation_method']=='Interpolating'
    assert r['original_mask_overlap_voxels']==0 and r['raw_staged_ct_all_voxels_equal']
    assert r['ct_voxel_count']==120586240
    assert sha((FOLDER/'source-metadata.json').read_bytes())==HASHES['figshare-metadata.json']
    assert sha(gzip.decompress((FOLDER/'original-mesh17.stl.gz').read_bytes()))==HASHES['mesh17.stl']
    expected={'true':(1,356048,7,'Segmentation.Status:completed'),'false':(2,496428,1,'Segmentation.Status:inprogress')}
    for row in r['records']:
        kind=row['lumen'];raw=(FOLDER/(kind+'lumen17.seg.nrrd')).read_bytes()
        assert sha(raw)==row['source_mask_sha256']==HASHES[kind+'lumen17.seg.nrrd']
        assert (row['source_label_value'],row['voxel_count'],row['six_connected_component_count'],row['source_status_tag'])==expected[kind]
        assert sum(row['component_voxel_counts'])==row['voxel_count']
        assert not row['source_labels_changed'] and row['original_voxel_anisotropy_preserved']
    acquisition=json.loads((FOLDER/'original-range-acquisition.json').read_text())
    assert acquisition['consistent_archive_etags_verified'] and len(acquisition['records'])==5
    assert all(not e['archive_full_md5_verified'] for e in acquisition['records'])

def test_source_statistics_disagreements_and_original_mesh_frame_are_not_repaired():
    r=proof();rows={e['lumen']:e for e in r['records']}
    assert rows['true']['voxel_volume_if_source_mm_units_ml']==pytest.approx(255.3091688232422)
    assert rows['false']['voxel_volume_if_source_mm_units_ml']==pytest.approx(355.9705996398926)
    assert rows['true']['source_table_volume_ml']==254.1 and rows['false']['source_table_volume_ml']==358.2
    assert rows['true']['voxel_volume_minus_source_table_ml']>1 and rows['false']['voxel_volume_minus_source_table_ml']<-2
    assert not r['original_mesh_patient_frame_or_unit_transform_verified'] and not r['original_mesh_fitted_or_rescaled']
    assert not r['upstream_code_applies_to_cta17_verified']
    assert not r['clinical_approval'] and not r['runtime_promoted'] and not r['structure_coverage_granted']
    assert any('thrombosed' in s and 'excluded' in s for s in r['limits'])
    assert any('entry/re-entry' in s for s in r['limits'])

def test_derivative_arrays_and_render_bindings_preserve_separate_channels_without_coverage_grant():
    r=proof()
    for row in r['records']:
        kind=row['lumen'];positions=gzip.decompress((FOLDER/(kind+'-positions.f64.gz')).read_bytes());triangles=gzip.decompress((FOLDER/(kind+'-triangles.u32.gz')).read_bytes())
        assert sha(positions)==row['positions_sha256'] and sha(triangles)==row['triangles_sha256']
        assert len(positions)==row['positions']*24 and len(triangles)==row['triangles']*12
        assert row['boundary_edges']==row['nonmanifold_edges']==0
        assert not row['background_padding_added'] and not row['source_smoothing_decimation_fitting_or_component_removal_applied']
        assert not row['geometry_is_original_delivered_mesh'] and not row['table_statistics_are_independent_dicom_calibration']
    view=json.loads((FOLDER/'render-review.json').read_text())
    assert view['source_review_sha256']==sha((FOLDER/'paired-lumen-source-review.json').read_bytes())
    assert len(view['native_axial_plane_indices'])==6 and not view['source_masks_or_geometry_edited']
    assert not view['source_geometry_fitted_or_rescaled'] and not view['clinical_approval']
    for image in view['images']:assert sha((FOLDER/image['file']).read_bytes())==image['sha256']

def test_each_native_source_label_and_half_grid_vertex_maps_to_the_original_affine():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_avt_r6_source import read_nrrd
    from tools.anatomy_sources.review_aaa_kinematic_source import grid_transform
    for row in proof()['records']:
        f,mask=read_nrrd((FOLDER/(row['lumen']+'lumen17.seg.nrrd')).read_bytes());b,o=grid_transform(f)
        assert set(np.unique(mask))=={0,row['source_label_value']} and int(np.count_nonzero(mask==row['source_label_value']))==row['voxel_count']
        positions=np.frombuffer(gzip.decompress((FOLDER/(row['lumen']+'-positions.f64.gz')).read_bytes()),'<f8').reshape(-1,3)
        ijk=(positions*[-1,-1,1]-o)@np.linalg.inv(b).T
        assert np.abs(ijk*2-np.rint(ijk*2)).max()<1e-9
        assert np.all(ijk>=0) and np.all(ijk<=np.array(mask.shape[::-1])-1)
        triangles=np.frombuffer(gzip.decompress((FOLDER/(row['lumen']+'-triangles.u32.gz')).read_bytes()),'<u4').reshape(-1,3)
        assert triangles.max()<len(positions)

def test_original_raw_and_staged_ct_samples_are_unchanged_and_statistically_bound():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_avt_r6_source import read_nrrd
    root=ROOT/'.research/graz-dissection-source-review'
    if not (root/'raw-cta17.nrrd').exists():pytest.skip('Original research CT is not installed')
    f,ct=read_nrrd((root/'cta17s.nrrd').read_bytes());fr,raw=read_nrrd((root/'raw-cta17.nrrd').read_bytes())
    assert np.array_equal(ct,raw) and sha(ct.tobytes())==proof()['original_ct_voxel_sha256']
    for row in proof()['records']:
        _,mask=read_nrrd((FOLDER/(row['lumen']+'lumen17.seg.nrrd')).read_bytes());values=ct[mask==row['source_label_value']]
        assert float(values.mean())==row['mean_stored_ct_value_within_label']
        assert float(values.std())==row['population_sd_stored_ct_value_within_label']
