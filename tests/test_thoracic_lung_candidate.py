"""Same-case CT and all lobe labels remain original; no anatomical approval is inferred."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy import ndimage
from skimage.measure import marching_cubes
from tools.anatomy_sources.review_hvsmr2_pat7_source import read_nifti
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/thoracic-lung-source-review-s0028'


def test_complete_original_arrays_and_source_grids_agree_across_readers():
    proof=json.loads((REVIEW/'source-review.json').read_text())
    assert len(proof['records'])==6 and proof['source_case']=='s0028'
    assert not proof['clinical_approval'] and not proof['normal_anatomical_atlas_approval']
    assert not proof['structure_coverage_granted'] and not proof['runtime_promoted']
    for row in proof['records']:
        path=REVIEW/row['file'];raw=path.read_bytes()
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
        array,affine,_=read_nifti(path);other=nib.load(path)
        assert np.array_equal(array,other.dataobj.get_unscaled())
        assert np.array_equal(affine,other.affine)
        assert list(array.shape)==row['shape']==[299,299,394]
        assert affine.tolist()==row['affine']


def test_all_original_lobe_voxels_and_exact_derived_surfaces_are_preserved():
    proof=json.loads((REVIEW/'source-review.json').read_text());masks=[];total=0
    for row in proof['records'][1:]:
        image=nib.load(REVIEW/row['file']);mask=np.asarray(image.dataobj.get_unscaled());masks.append(mask.astype(bool))
        assert int(mask.sum())==row['foreground_voxels']
        _,components=ndimage.label(mask,ndimage.generate_binary_structure(3,1))
        assert components==row['components_6']==1 and not row['touches_scan_boundary']
        v,f,_,_=marching_cubes(mask,level=.5,allow_degenerate=True);v=v.astype(np.float64);a=image.affine
        expected=np.column_stack([v[:,0]*a[i,0]+v[:,1]*a[i,1]+v[:,2]*a[i,2]+a[i,3] for i in range(3)]).astype('<f8')
        for suffix,body in [('positions.f64.gz',expected.tobytes()),('triangles.u32.gz',f.astype('<u4').tobytes())]:
            item=row['surfaces'][suffix];encoded=(REVIEW/item['file']).read_bytes()
            assert hashlib.sha256(encoded).hexdigest()==item['sha256']
            assert gzip.decompress(encoded)==body
            assert hashlib.sha256(body).hexdigest()==item['decoded_sha256']
        total+=len(f)
    assert total==351784
    assert all(not np.logical_and(masks[i],masks[j]).any() for i in range(5) for j in range(i+1,5))
    assert proof['pairwise_lobe_overlap_voxels']==[0]*10
