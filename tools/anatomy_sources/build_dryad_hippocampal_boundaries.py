"""Generate complete native source-cell boundaries for both case10 raters.

Local research output only; no publishing or clinical approval is performed.
"""
from pathlib import Path
import sys,json,gzip,hashlib
import nibabel as nib,numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.anatomy_sources.soop_stroke_native import cell_boundary
D=ROOT/'.research/epilepsy-source-20261028';F=D/'dryad-case10';O=D/'case10-boundaries';O.mkdir(exist_ok=True)
acquisitionPath=D/'dryad-case10-acquisition.json'
assert hashlib.sha256(acquisitionPath.read_bytes()).hexdigest()=='dfab764bc92a28f6366c926cb90eae0201a20acd2c23db00bfb47893ddb5f63b'
for sourceRow in json.loads(acquisitionPath.read_bytes())['files']:
 assert hashlib.sha256((D/sourceRow['file']).read_bytes()).hexdigest()==sourceRow['sha256']
rows=[]
for rater,name in [('primary','Hippocampal_Segmentation.nii'),('second','DICE_Hippocampal_Segmentation.nii')]:
 im=nib.load(F/name);labels=np.asarray(im.dataobj);aff=im.affine;unit=abs(np.linalg.det(aff[:3,:3]))
 for code in np.unique(labels):
  if code==0:continue
  mask=labels==code;N=int(mask.sum());world,faces,records,voxel=cell_boundary(mask,aff)
  pairs=0
  for axis in range(3):
   a=[slice(None)]*3;b=a.copy();a[axis]=slice(None,-1);b[axis]=slice(1,None);pairs+=int(np.count_nonzero(mask[tuple(a)]&mask[tuple(b)]))
  assert len(records)==6*N-2*pairs and len(faces)==2*len(records)
  tri=world[faces];volume=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
  assert abs(volume-N*unit)<max(1e-7,N*unit*1e-9),(rater,code,volume,N*unit)
  normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);directions=(np.linalg.inv(aff[:3,:3]).T@np.eye(3)[:,records[:,3]]).T*records[:,4,None]
  assert np.all(np.einsum('ij,ij->i',normals,np.repeat(directions,2,axis=0))>0)
  comps,n=ndimage.label(mask,structure=np.ones((3,3,3),bool));counts=np.bincount(comps.ravel())[1:];assert counts.sum()==N
  file=O/f'{rater}-{int(code)}.npz';np.savez_compressed(file,world=world,triangles=faces,voxelCorners=voxel,sourceFaces=records)
  row={'rater':rater,'code':int(code),'sourceMaskSHA256':hashlib.sha256((F/name).read_bytes()).hexdigest(),'voxels':N,'exposedFaces':len(records),'triangles':len(faces),'vertices':len(world),'components26':sorted(map(int,counts),reverse=True),'volumeMm3':N*unit,'signedMeshVolumeMm3':volume,'outwardWindingVerified':True,'allExposedFacesRetained':True,'sourceResampled':False,'sourceSmoothed':False,'file':str(file.relative_to(D)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()};rows.append(row);print(json.dumps({k:row[k]for k in ['rater','code','triangles','voxels']}),flush=True)
proof={'meshes':rows,'meshCount':len(rows),'triangles':sum(r['triangles']for r in rows),'allPassed':True,'originalArchiveFullHashVerificationPending':True,'clinicalApproval':False,'wholeGoalComplete':False}
(D/'case10-boundary-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
