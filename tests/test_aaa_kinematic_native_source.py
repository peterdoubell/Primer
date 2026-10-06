"""Native files, spatial controls and clinical coverage are separate claims."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import zipfile
import pytest
from tools.anatomy_sources.review_aaa_kinematic_source import ARCHIVE_SHA,METADATA_SHA,PAPER_SHA

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/aaa-kinematic-native-source-review'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def proof():return json.loads((FOLDER/'native-source-review.json').read_text())


def test_all_cases_frames_and_original_surface_bytes_are_preserved():
    p=proof();assert p['patient_count']==10 and p['acquired_ct_frame_count']==78
    assert p['all_delivered_ct_voxel_count']==51743358 and p['original_surface_facet_count']==199468
    assert sha((FOLDER/'source-metadata.json').read_bytes())==p['source_metadata_sha256']==METADATA_SHA
    m=json.loads((FOLDER/'source-metadata.json').read_text())
    assert m['metadata']['license']['id']=='cc-by-4.0' and m['metadata']['access_right']=='open'
    assert p['archive_sha256']==ARCHIVE_SHA and p['primary_paper_sha256']==PAPER_SHA
    assert p['publisher_md5_verified'] and p['all_archive_members_crc_verified']
    assert {r['patient_source_id'] for r in p['records']}=={f'P{i}' for i in range(1,11)}
    for row in p['records']:
        raw=gzip.decompress((FOLDER/row['preserved_surface_file']).read_bytes());g=row['geometry_controls']
        assert sha(raw)==row['surface_sha256'] and len(raw)==84+50*g['facet_count']
        count=struct.unpack_from('<I',raw,80)[0];assert count==g['facet_count']
        assert all(all(math.isfinite(x) for x in facet[:12]) for facet in struct.iter_unpack('<12fH',raw[84:]))
        assert g['boundary_edges']>0 and g['nonmanifold_edges']==0 and g['exact_position_connected_components']==1
        assert g['independent_scalar_facet_readback_verified'] and not g['analysis_position_deduplication_changes_source']
        expected={40,80} if row['patient_source_id'] in {'P2','P4'} else set(range(30,100,10)) if row['patient_source_id'] in {'P1','P8'} else set(range(10,101,10))
        assert {f['cardiac_phase_percent'] for f in row['frames']}==expected
        for f in row['frames']:
            assert f['header']['space']=='left-posterior-superior' and f['header']['type']=='short'
            assert 'space units' not in f['header'] and not f['physical_space_units_independently_verified']
            assert not f['source_voxels_changed'] and not f['ct_hu_calibration_verified']
            assert not f['geometry_phase_registration_verified']


def test_partial_processed_geometry_and_synthetic_data_cannot_grant_full_anatomy():
    p=proof();assert all(not p[k] for k in ('original_geometry_or_voxels_changed','clinical_approval','runtime_promoted','structure_coverage_granted'))
    assert len(p['synthetic_method_verification_files'])==11
    assert all(not r['is_independent_acquired_anatomy_ground_truth'] for r in p['synthetic_method_verification_files'])
    assert next(r for r in p['synthetic_method_verification_files'] if r['member'].endswith('CTA_deformed.nrrd'))['is_acquired_systolic_ct'] is False
    for row in p['records']:
        assert row['delivered_surface_is_external_only'] and not row['source_segmentation_masks_supplied']
        assert not row['clinical_approval'] and not row['runtime_promoted'] and not row['structure_coverage_granted']
        assert not row['geometry_controls']['closed_topology_is_anatomical_validation']
        assert not row['geometry_controls']['self_intersections_tested']
    assert {r['patient_source_id'] for r in p['records'] if r['paper_systolic_phase_typo_affects_case']}=={'P2','P3'}
    selected={r['patient_source_id']:next(f for f in r['frames'] if f['cardiac_phase_percent']==r['review_phase_percent']) for r in p['records']}
    assert {k for k,f in selected.items() if f['surface_corner_records_outside_voxel_cell_extent']}=={'P3','P10'}
    assert selected['P3']['surface_corner_records_outside_voxel_cell_extent']==904
    assert selected['P10']['surface_corner_records_outside_voxel_cell_extent']==1386


def test_all_rendered_contexts_bind_exact_source_files_without_fitting_or_approval():
    p=proof();r=json.loads((FOLDER/'render-review.json').read_text())
    assert r['native_source_proof_sha256']==sha((FOLDER/'native-source-review.json').read_bytes())
    assert len(r['records'])==10 and sum(len(i['native_slice_contexts']) for i in r['records'])==30
    by_id={i['patient_source_id']:i for i in p['records']}
    for row in r['records']:
        assert sha((FOLDER/row['image_file']).read_bytes())==row['image_sha256']
        assert row['surface_sha256']==by_id[row['patient_source_id']]['surface_sha256']
        assert row['ct_sha256']==next(f['nrrd_sha256'] for f in by_id[row['patient_source_id']]['frames'] if f['member']==row['ct_member'])
        assert row['display_window_stored_values']==[-200,600]
        assert not row['ct_spatial_interpolation_applied'] and not row['source_geometry_changed'] and not row['source_alignment_fitted']
        assert not row['overlay_is_independent_anatomical_boundary_validation']


def test_binary_stl_parser_preserves_normals_signed_zero_and_attributes_and_rejects_corruption():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_aaa_kinematic_source import stl
    facet=struct.pack('<12fH',0,0,1,-0.0,0,0,1,0,0,0,1,0,13)
    raw=bytes(80)+struct.pack('<I',1)+facet;rows=stl(raw)
    assert rows['normal'].tobytes()==facet[:12] and rows['vertices'].tobytes()==facet[12:48]
    assert int(rows[0]['attribute'])==13 and np.signbit(rows[0]['vertices'][0,0])
    for bad in (raw[:-1],raw+b'\x00',bytes(80)+struct.pack('<I',2)+facet):
        with pytest.raises(ValueError):stl(bad)
    bad=bytearray(raw);struct.pack_into('<f',bad,96,float('nan'))
    with pytest.raises(ValueError,match='Nonfinite'):stl(bytes(bad))


def test_lps_ras_basis_conversion_is_exact_and_no_fitted_transform_is_introduced():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_aaa_kinematic_source import ras_to_ijk,grid_transform
    fields={'space':'left-posterior-superior','space directions':'(-0.5,0,0) (0,-0.5,0) (0,0,1.25)','space origin':'(10,-20,30)'}
    assert np.array_equal(ras_to_ijk([[-8,24,32.5]],fields),[[4,8,2]])
    wrong={**fields,'space':'right-anterior-superior'}
    with pytest.raises(ValueError,match='basis'):grid_transform(wrong)
    singular={**fields,'space directions':'(0,0,0) (0,1,0) (0,0,1)'}
    with pytest.raises(ValueError,match='spatial matrix'):grid_transform(singular)


def test_native_plane_intersections_include_crossings_and_edges_without_invented_caps():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.render_aaa_kinematic_source import plane_segments
    tri=np.array([[[0,0,-1],[1,0,1],[0,1,1]],[[2,0,0],[3,0,0],[2,1,1]],
                  [[4,0,0],[5,0,0],[4,1,0]],[[6,0,0],[7,0,1],[6,1,1]]],dtype='float64')
    lines,coplanar=plane_segments(tri,0)
    assert lines.shape==(2,2,2) and coplanar==1
    assert set(map(tuple,lines[0]))=={(.5,0),(0,.5)}
    assert set(map(tuple,lines[1]))=={(2,0),(3,0)}


def test_research_archive_contains_every_reported_original_grid(tmp_path):
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_spl_wall_source import nrrd
    path=ROOT/'.research/aaa-native-source-review/4DCTA_AAA_Dataset.zip'
    if not path.exists():pytest.skip('Original research archive is not installed')
    assert sha(path.read_bytes())==ARCHIVE_SHA
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for row in proof()['records']:
            for frame in row['frames']:
                raw=z.read(frame['member']);fields,values=nrrd(raw)
                assert sha(raw)==frame['nrrd_sha256'] and values.size==frame['voxel_count']
                assert sha(values.astype('<i2').tobytes())==frame['original_voxel_int16_sha256']
                assert fields==frame['header']
