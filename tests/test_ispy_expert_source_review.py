import gzip,hashlib,json,struct
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];PROOF=ROOT/'docs/breast-native-MRI-source-review/ISPY1_1002-expert'
def test_original_expert_mask_publisher_identity_and_all_source_geometry_are_bound():
    acquisition=json.loads((PROOF/'original-acquisition.json').read_text());records=acquisition['records'];assert len(records)==9 and all(r['source_MD5_verified'] for r in records)
    original=(PROOF/'original-expert-manual-mask.nii.gz').read_bytes();row=next(r for r in records if r['file'].startswith('masks_stv_manual/'));assert hashlib.md5(original).hexdigest()==row['source_MD5'] and hashlib.sha256(original).hexdigest()==row['sha256']
    proof=json.loads((PROOF/'original-source-review.json').read_text());assert proof['total_original_scalar_samples_checked']==39728640 and proof['expert_manual_mask_exactly_matches_all_three_processed_1mm_MRI_grids']
    assert not proof['computed_mask_substituted_for_expert_mask'] and not proof['clinical_approval'] and not proof['runtime_promoted']
    for r in proof['source_surfaces']:
        stem=r['file'].split('/')[0]
        for tail,key in [('positions.f64.gz','positions_sha256'),('triangles.u32.gz','triangles_sha256')]:assert hashlib.sha256(gzip.decompress((PROOF/(stem+'-'+tail)).read_bytes())).hexdigest()==r[key]
    manual=next(r for r in proof['source_surfaces'] if r['producer_role']=='expert structural tumour');assert manual['source_surface_components']==2 and manual['component_triangle_counts']==[5100,44] and manual['triangles']==5144
def test_source_qform_matches_independent_library_and_invalid_geometry_does_not_fall_back(tmp_path):
    np=pytest.importorskip('numpy');nib=pytest.importorskip('nibabel');from tools.anatomy_sources.review_ispy_expert_source import read
    original=PROOF/'original-expert-manual-mask.nii.gz';a,A,h=read(original);image=nib.load(original);assert np.array_equal(a,image.dataobj.get_unscaled()) and np.array_equal(A,image.affine) and h['qform_code']==1 and h['sform_code']==0
    assert int((a!=0).sum())==5091
    raw=bytearray(gzip.decompress(original.read_bytes()));struct.pack_into('<h',raw,252,0);bad=tmp_path/'no-source-geometry.nii.gz';bad.write_bytes(gzip.compress(raw))
    with pytest.raises(ValueError,match='geometry missing'):read(bad)
    raw=bytearray(gzip.decompress(original.read_bytes()));struct.pack_into('<h',raw,254,1);B=A.copy();B[0,3]+=.5;struct.pack_into('<12f',raw,280,*B[:3,:].ravel());bad.write_bytes(gzip.compress(raw))
    with pytest.raises(ValueError,match='sform/qform disagree'):read(bad)
def test_producer_timing_and_mask_semantics_do_not_turn_assumptions_into_clinical_truth():
    p=ROOT/'docs/breast-native-MRI-source-review/ISPY1_1001/producer-semantics-review.json';d=json.loads(p.read_text());assert d['source_label_not_every_native_breast_tissue_or_structural_tumour_model'];assert 'assumed' in d['private_timing_source']['producer_caveat'];assert not d['original_half_pixel_offset_corrected_or_fitted'] and not d['native_overlay_anatomical_or_clinical_approval'];assert d['source_mask_parameter_sequence_empty'];assert not d['source_functional_volume_results_zero_is_pathological_complete_response']
