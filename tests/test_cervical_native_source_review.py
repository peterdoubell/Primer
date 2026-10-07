"""Source target-region evidence must never masquerade as individual-node coverage."""
import gzip,hashlib,json,struct
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
PROOF=ROOT/'docs/cervical-node-native-source-review'
def load(name):return json.loads((PROOF/name).read_text())
def test_dataset_grant_is_distinct_from_uncleared_repository_example():
    a=load('LNCTVSeg-original-example-acquisition.json');r=load('LNCTVSeg-original-example-volume-review.json');m=load('figshare-26793622.json')
    assert hashlib.sha256((PROOF/'figshare-26793622.json').read_bytes()).hexdigest()==a['dataset_metadata_sha256']
    assert m['license']==a['actual_dataset_grant'] and m['license']['name']=='CC BY 4.0'
    assert not a['full_dataset_archive_publisher_MD5_verified'] and not a['example_correspondence_to_full_archive_independently_verified']
    assert not r['public_repository_example_data_license_independently_cleared']
    for key in ['clinical_approval','runtime_promoted','structure_coverage_granted','original_target_regions_are_individual_node_cortex_hilum_capsule_or_ENE_geometry']:
        assert r[key] is False
def test_source_regions_preserve_combined_levels_and_sampling_limits():
    r=load('LNCTVSeg-original-example-volume-review.json')
    assert all(x['dimensions']==[512,512,200] for x in r['original_files'])
    assert r['source_frame']==['L','P','S'] and r['same_original_declared_grid_verified']
    assert not r['source_CT_arrays_are_byte_identical_samples']
    assert not r['source_CT_arrays_are_independently_raw_DICOM_registered_or_HU_calibrated']
    assert not r['source_declared_sampling_is_adequate_for_all_tiny_nodal_wall_or_neural_structures']
    t=r['source_targets'];assert [x['voxels'] for x in t]==[17317,17891,9211,10602,1546,1360]
    assert [x['triangles'] for x in t]==[18640,18952,10620,12244,2924,2764]
    assert all(x['six_neighbour_components']==1 and not x['source_components_filtered_or_repaired'] for x in t)
    assert all(x['boundary_edges']==x['nonmanifold_edges']==0 for x in t)
    assert 'II+III+Va' in t[0]['source_target_name'] and 'IV+Vb' in t[2]['source_target_name']
    semantics=r['source_semantics'];assert semantics['lower_neck_label_discrepancy']=={'repository_labels_3_4':'IV+Vb','article_table_2_labels_3_4':'IV+Vb+Vc','resolved':False}
    assert not semantics['CTV_map_is_unmodified_universal_surgical_or_2013_consensus_map']
    assert not semantics['CTV_independent_sublevels_recovered_from_combined_masks']
    plate=load('paired-native-CT-review.json');assert plate['source_k_indices']==[94,115,123]
    assert not plate['rights_cleared_for_publication'] and not plate['anatomical_review_complete'] and not plate['runtime_promoted']
def test_cached_original_samples_and_derived_geometry_when_available():
    np=pytest.importorskip('numpy');nib=pytest.importorskip('nibabel')
    from tools.anatomy_sources.review_hvsmr2_pat7_source import read_nifti
    source=ROOT.parent/'cervical-node-native-source-review'
    if not (source/'LNCTVSeg-original-example').is_dir():pytest.skip('Original acquisition cache unavailable')
    r=load('LNCTVSeg-original-example-volume-review.json')
    for row in r['original_files']:
        path=source/'LNCTVSeg-original-example'/row['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['source_file_sha256']
        values,A,h=read_nifti(path);independent=nib.load(path)
        assert np.array_equal(values,independent.dataobj.get_unscaled()) and np.allclose(A,independent.affine,atol=1e-7,rtol=0)
        assert h=={key:row[key] for key in h}
    for t in r['source_targets']:
        files=source/'public-example-derived-review'
        p=gzip.decompress((files/f'target{t["source_value"]}-positions.f64.gz').read_bytes());f=gzip.decompress((files/f'target{t["source_value"]}-triangles.u32.gz').read_bytes())
        assert hashlib.sha256(p).hexdigest()==t['positions_sha256'] and len(p)==24*t['vertices']
        assert hashlib.sha256(f).hexdigest()==t['triangles_sha256'] and len(f)==12*t['triangles']
        assert max(x[0] for x in struct.iter_unpack('<I',f))<t['vertices']
