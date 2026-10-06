"""Native bilateral-SVC source evidence preserves labels, optional-zone limits and incomplete metadata."""
import csv,gzip,hashlib,json,struct
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/hvsmr2-pat7-native-source-review';SOURCE=ROOT/'.research/hvsmr2-source-review'
HASHES={'pat7_orig_seg.nii.gz':'f14020c70fac692be410cd8cd105a727005bfacdb66e7b6466bf8dc023fca785','pat7_orig_seg_endpoints.nii.gz':'5afdc3096f570cbd59fd715009b7e02a6130c3c6c764b17817b53bd53791fbf0','pat7_orig.nii.gz':'b62ad2dbca3550ed2695e4d9181d2c4e5b9ee9d264ffcc17fd7146f206ee668e'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def report():return json.loads((OUT/'native-source-review.json').read_text())
def test_actual_case_selection_rights_and_missing_case_record_are_not_inferred():
    r=report();meta=json.loads((OUT/'figshare-25226360-v2.json').read_text());clinical=list(csv.DictReader((OUT/'hvsmr_clinical.csv').read_text().splitlines()))
    assert meta['license']['name']==r['license']=='CC BY 4.0' and meta['doi']==r['source_doi']=='10.6084/m9.figshare.25226360.v2'
    assert sha((OUT/'figshare-25226360-v2.json').read_bytes())==r['dataset_metadata_sha256']
    assert r['clinical_record']['Pat']=='7' and r['clinical_record']['Age']=='27'
    assert [k for k,v in r['clinical_record'].items() if v=='X']==['BilateralSVC']
    assert next(x for x in clinical if x['Pat']=='17')['SevereDilation']=='X'
    assert r['archive_patient_image_ids']==list(range(60))
    assert r['clinical_csv_pat_count']==59 and r['technical_csv_pat_count']==60 and r['clinical_csv_missing_case_ids']==['59']
    assert r['clinical_csv_bilateral_svc_ids']==['3','7','30','35','38','47','52','56','57']
    for f in meta['files']:
        if f['name'].endswith('.csv'):assert hashlib.md5((OUT/f['name']).read_bytes()).hexdigest()==f['computed_md5']
def test_original_masks_and_all_derived_arrays_are_retained_without_cleanup():
    r=report();acq=json.loads((OUT/'pat7-acquisition.json').read_text());records={x['file']:x for x in acq['records']}
    assert {x['etag'] for x in acq['requests']}=={'"6b80c395416addd9691462a6b6ea86da-2"'}
    assert not acq['full_archive_md5_verified'] and len(records)==3
    for name,hash in HASHES.items():
        assert records[name]['sha256']==hash
        if name!='pat7_orig.nii.gz':assert sha((OUT/name).read_bytes())==hash
    assert len(r['classes'])==8 and sum(c['triangles'] for c in r['classes'])==567000
    for c in r['classes']:
        p=gzip.decompress((OUT/f'label{c["label"]}-positions.f64.gz').read_bytes());f=gzip.decompress((OUT/f'label{c["label"]}-triangles.u32.gz').read_bytes())
        assert len(p)==c['vertices']*24 and sha(p)==c['positions_sha256']
        assert len(f)==c['triangles']*12 and sha(f)==c['triangles_sha256']
        assert max(x[0] for x in struct.iter_unpack('<I',f))<c['vertices']
    c={c['label']:c for c in r['classes']};assert c[7]['component_voxels_descending']==[20178,14241]
    assert c[2]['component_voxels_descending']==[266206,13]  # retain original tiny RV island
    assert c[5]['optional_zone_outside_original_class']==3444 and c[7]['optional_zone_outside_original_class']==15001
    assert c[7]['required_voxels_after_source_optional_zone_subtraction']==27012
    assert not r['runtime_promoted'] and not r['clinical_approval'] and not r['anatomical_approval'] and not r['complete_venous_geometry_verified']
    assert not r['native_motion_acquired'] and not r['source_intensity_is_HU']
def test_independent_nifti_reader_and_actual_source_grid_match_every_voxel():
    np=pytest.importorskip('numpy');nib=pytest.importorskip('nibabel')
    from tools.anatomy_sources.review_hvsmr2_pat7_source import read_nifti
    if not (SOURCE/'pat7_orig.nii.gz').exists():pytest.skip('Original acquisition cache is unavailable')
    r=report()
    for name in HASHES:
        path=SOURCE/name;assert sha(path.read_bytes())==HASHES[name];array,affine,header=read_nifti(path);independent=nib.load(path)
        assert np.array_equal(array,independent.dataobj.get_unscaled())
        assert np.allclose(affine,independent.affine,rtol=0,atol=1e-7) and header==r['original_headers'][name]
        assert array.shape==(528,507,200)
    assert r['source_frame']==['P','I','R'] and r['all_original_grids_identical']
def test_parser_rejects_wrong_grid_or_truncated_payload(tmp_path):
    pytest.importorskip('numpy')
    from tools.anatomy_sources.review_hvsmr2_pat7_source import read_nifti
    raw=bytearray(gzip.decompress((OUT/'pat7_orig_seg.nii.gz').read_bytes()));bad=tmp_path/'bad.nii.gz'
    struct.pack_into('<h',raw,40,4);bad.write_bytes(gzip.compress(raw,mtime=0))
    with pytest.raises(ValueError,match='static 3D'):read_nifti(bad)
    raw=bytearray(gzip.decompress((OUT/'pat7_orig_seg.nii.gz').read_bytes()));bad.write_bytes(gzip.compress(raw[:-2],mtime=0))
    with pytest.raises(ValueError,match='payload length'):read_nifti(bad)
