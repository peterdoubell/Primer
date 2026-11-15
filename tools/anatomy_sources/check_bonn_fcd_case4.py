"""Independent exposed-face and triangle audit against original FLAIR-space ROI."""
from pathlib import Path
import hashlib,json
import nibabel as nib,numpy as np
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'.research/fcd-source-20261028'
receipt=json.loads((D/'sub-00004-acquisition.json').read_bytes());roiRow=next(r for r in receipt['files']if r['file'].endswith('_roi.nii.gz'));original=D/roiRow['file'];assert hashlib.sha256(original.read_bytes()).hexdigest()==roiRow['sha256'];image=nib.load(original);mask=np.asarray(image.dataobj)==1;assert image.header.get_xyzt_units()[0]=='mm'
mesh=D/'sub-00004-source-boundary.npz';z=np.load(mesh);world=z['world'];faces=z['triangles'];assert np.array_equal(np.unique(faces),np.arange(len(world)));inverse=np.linalg.inv(image.affine);assert np.isfinite(world).all()and np.isfinite(inverse).all();corners=np.column_stack([inverse[r,3]+sum(inverse[r,c]*world[:,c]for c in range(3))for r in range(3)])*2;rounded=np.rint(corners).astype(np.int64);assert np.max(abs(corners-rounded))<1e-9;assert np.all(rounded%2!=0)
v=rounded[faces];lo=v.min(1);hi=v.max(1);span=hi-lo;assert np.all(np.sort(span,axis=1)==[0,2,2]);axis=np.argmin(span,axis=1);positive=((lo+hi)//2)//2;negative=positive.copy();negative[np.arange(len(faces)),axis]+=1

def occupied(points):
 inside=np.all((points>=0)&(points<np.array(mask.shape)),axis=1);result=np.zeros(len(points),bool);result[inside]=mask[tuple(points[inside].T)];return result

pos,neg=occupied(positive),occupied(negative);assert np.all(pos^neg);owners=np.where(pos[:,None],positive,negative);sign=np.where(pos,1,-1);records=np.column_stack([owners,axis,sign]);unique,inverse,counts=np.unique(records,axis=0,return_inverse=True,return_counts=True);assert np.all(counts==2)
expected=[];cells=np.argwhere(mask)
for a in range(3):
 for s in [-1,1]:
  adjacent=cells.copy();adjacent[:,a]+=s;boundary=cells[~occupied(adjacent)];expected.extend([*map(int,p),a,s]for p in boundary)
assert np.array_equal(unique,np.unique(np.array(expected),axis=0))
for first,second in np.argsort(inverse,kind='stable').reshape(-1,2):
 points,frequency=np.unique(np.concatenate([v[first],v[second]]),axis=0,return_counts=True);assert len(points)==4;diagonal=points[frequency==2];assert diagonal.shape==(2,3)and sorted(abs(diagonal[1]-diagonal[0]))==[0,2,2]
tri=world[faces];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);outward=np.linalg.inv(image.affine[:3,:3]).T[:,axis].T*sign[:,None];assert np.all(np.einsum('ij,ij->i',normal,outward)>0);volume=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6);sourceVolume=int(mask.sum())*abs(np.linalg.det(image.affine[:3,:3]));assert abs(volume-sourceVolume)<1e-6
proof={'allPassed':True,'sourceROI_SHA256':roiRow['sha256'],'sourceVoxels':int(mask.sum()),'independentlyReconstructedFaces':len(expected),'triangles':len(faces),'completeFaceSetMatched':True,'twoTrianglesTileEachFace':True,'outwardWindingVerified':True,'signedMeshVolumeMm3':volume,'sourceCellVolumeMm3':sourceVolume,'meshSHA256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'checkerSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'clinicalApproval':False,'wholeGoalComplete':False};(D/'independent-boundary-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
