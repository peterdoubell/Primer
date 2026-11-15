from pathlib import Path
import gzip,json,hashlib
import nibabel as nib
import numpy as np
import argparse
parser = argparse.ArgumentParser(description="Compare published liver MRI samples and region meshes with original NIfTI sources")
parser.add_argument("source_directory", type=Path)
args = parser.parse_args()
root=Path('web/anatomy/liver-regions-mri')
volume=json.loads((root/'volume.json').read_text())
mask=nib.load(args.source_directory/(volume['selectedCase']+'-labels.nii.gz'))
labels=np.asanyarray(mask.dataobj)
image=nib.load(args.source_directory/(volume['selectedCase']+'-mri.nii.gz'))
np.testing.assert_array_equal(image.affine,mask.affine)
np.testing.assert_array_equal(image.affine,np.asarray(volume['sourceAffine']))
assert image.dataobj.slope == volume['sourceScaling']['slope']
assert image.dataobj.inter == volume['sourceScaling']['intercept']
assert list(image.shape) == volume['shape']
stored=np.asanyarray(image.dataobj.get_unscaled())
for chunk in volume['chunks']:
    first=chunk['firstSlice'];last=first+chunk['slices']
    for key, original in [('mri',stored),('labels',labels)]:
        raw=gzip.decompress((root/chunk[key]['file']).read_bytes())
        assert raw==original[:,:,first:last].tobytes(order='F'), (key,first)
        assert hashlib.sha256(raw).hexdigest()==chunk[key]['sha256']
total=0
for row in json.loads((root/'surfaces.json').read_text()):
    raw=gzip.decompress((root/row['file']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==row['sha256']
    vertices=np.frombuffer(raw,'<f4',count=row['vertices']*3).reshape(-1,3)
    triangles=np.frombuffer(raw,'<u4',offset=row['vertices']*12).reshape(-1,6)
    corners=vertices[triangles[:,[0,1,2,5]]]
    inverse=np.linalg.inv(mask.affine[:3,:3])
    ijk=np.einsum('...j,kj->...k',corners.astype(float)-mask.affine[:3,3],inverse)
    grid=np.rint(2*ijk).astype(int)
    recovered=np.einsum('...j,kj->...k',grid/2,mask.affine[:3,:3])+mask.affine[:3,3]
    np.testing.assert_array_equal(corners,recovered.astype('<f4'))
    assert np.all(np.sort(np.ptp(grid,axis=1),axis=1)==[0,2,2])
    actual=set(map(tuple,(grid.max(1)+grid.min(1))//2))
    inside=labels==row['label'];expected=set()
    for axis in range(3):
        pad=[(0,0)]*3;pad[axis]=(1,1)
        centers=2*np.argwhere(np.diff(np.pad(inside,pad),axis=axis))
        centers[:,axis]-=1
        expected.update(map(tuple,centers))
    assert actual==expected and len(actual)==len(triangles)
    assert int(inside.sum())==row['sourceVoxels']
    total+=len(actual)
proof={'regions':8,'verifiedBoundaryQuads':total,'exactFloat32SourceCorners':True,
       'everyOriginalBoundaryFaceRetained':True,'sourceLabels':list(range(1,9)),
       'IVaIVbSeparatelyLabelled':False,'clinicalApproval':False}
(Path('docs/liver-regions-integration')/'geometry-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print(proof)
