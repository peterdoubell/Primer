"""Independent source anatomy retains original grids, strips and annotation authority."""
import hashlib
import json
from pathlib import Path
import zipfile
import pytest

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/spl-wall-source-review'


def test_delivered_ct_and_labels_have_the_same_complete_native_grid():
    r=json.loads((REVIEW/'independent-wall-source-review.json').read_text())
    assert r['archive_sha256']=='1cf85dbc820767b7c3095790ff38ae150a085af713061a2f0e950e355e4dc7c8'
    assert r['archive_crc_verified'] and r['archive_bytes']==34861066
    assert r['ct_grid']==r['label_grid'] and r['ct_grid']['sizes']=='256 256 113'
    assert r['ct_grid']['space']=='left-posterior-superior'
    assert r['delivered_voxel_count']==7405568 and r['all_delivered_voxels_inspected']
    assert r['ct_value_range']==[0,3952]
    assert not r['ct_hu_calibration_or_phase_verified'] and not r['highest_resolution_acquired_ct_verified']


def test_five_independent_models_keep_strip_and_label_identity_without_missing_layer_credit():
    r=json.loads((REVIEW/'independent-wall-source-review.json').read_text())
    assert {i['label_value'] for i in r['records']}=={32,135,136,235,236}
    assert sum(i['analysis_triangles'] for i in r['records'])==224612
    assert sum(i['source_label_voxels'] for i in r['records'])==200313
    for i in r['records']:
        assert sum(int(n)*count for n,count in i['strip_lengths'].items())>=i['analysis_triangles']
        assert sum((int(n)-2)*count for n,count in i['strip_lengths'].items())==i['analysis_triangles']
        assert not i['zero_area_analysis_triangles'] and not i['model_vertices_outside_delivered_grid']
        assert i['source_label_selector']['authoritative'] and not i['source_geometry_selector']['authoritative']
        assert i['source_label_selector']['dataKey']==i['label_value']
        assert not i['source_positions_indices_normals_changed'] and not i['analysis_welding_changes_source']
        assert i['exact_position_analysis_topology']['boundary_edges']==0
    assert not r['combined_rectus_label_split_into_patient_sides']
    assert all(not values for values in r['bounded_missing_structure_queries'].values())
    assert not r['clinical_approval'] and not r['runtime_promoted']


def test_all_original_arrays_and_voxels_match_locally_retained_source():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_spl_wall_source import vtk,nrrd
    archive=ROOT/'.research/wall-independent-sources/spl-abdomen-2016-09.zip'
    if not archive.exists():pytest.skip('Independent full source is retained in ignored staging')
    r=json.loads((REVIEW/'independent-wall-source-review.json').read_text())
    with zipfile.ZipFile(archive) as z:
        for name,key in [('I.nrrd','ct_original_voxel_bytes_sha256'),('seg.nrrd','label_original_voxel_bytes_sha256')]:
            _,values=nrrd(z.read('abdomen-2016-09/Data/'+name))
            assert hashlib.sha256(values.astype('<i2').tobytes()).hexdigest()==r[key]
        for i in r['records']:
            raw=z.read(i['source_member']);v,n,f,strips,pbytes,cbytes,nbytes=vtk(raw)
            assert hashlib.sha256(raw).hexdigest()==i['source_vtk_sha256']
            assert hashlib.sha256(pbytes).hexdigest()==i['positions_big_endian_float32_sha256']
            assert hashlib.sha256(cbytes).hexdigest()==i['connectivity_big_endian_int32_sha256']
            assert hashlib.sha256(nbytes).hexdigest()==i['normals_big_endian_float32_sha256']
            cursor=0
            for strip in strips:
                for index in range(len(strip)-2):
                    expected=[strip[index],strip[index+1],strip[index+2]] if index%2==0 else [strip[index+1],strip[index],strip[index+2]]
                    assert f[cursor].tolist()==expected;cursor+=1
            assert cursor==len(f)==i['analysis_triangles']


def test_all_five_review_figures_preserve_native_source_context():
    r=json.loads((REVIEW/'source-projection-review.json').read_text())
    assert r['source_review_sha256']==hashlib.sha256((REVIEW/'independent-wall-source-review.json').read_bytes()).hexdigest()
    assert len(r['figures'])==5
    assert sum(p['all_original_strip_triangles'] for f in r['figures'] for p in f['panels'])==2*224612
    for f in r['figures']:
        assert hashlib.sha256((REVIEW/f['file']).read_bytes()).hexdigest()==f['sha256']
        assert f['native_plane_label_voxels']>0 and not f['source_voxels_or_geometry_changed']
    notice=(REVIEW/'required-part-b-notice.txt').read_text()
    assert notice.startswith('All or portions of this licensed product')
    assert 'CLINICAL APPLICATIONS ARE NEITHER RECOMMENDED NOR ADVISED' in ' '.join(notice.split())
