"""Local development independent verification for the fixed Dryad case10 source.

Outputs stay in ignored research storage. Full publisher-archive SHA256
verification remains a separate mandatory publication gate.
"""
from pathlib import Path
import gzip,hashlib,json,struct
import nibabel as nib,numpy as np
D=Path(__file__).resolve().parents[2]/'.research/epilepsy-source-20261028';O=D/'native-package';S=D/'dryad-case10';m=json.loads((O/'manifest.json').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();packs={};samples=0;planes=0

acquisitionPath=D/'dryad-case10-acquisition.json'
assert hashlib.sha256(acquisitionPath.read_bytes()).hexdigest()=='dfab764bc92a28f6366c926cb90eae0201a20acd2c23db00bfb47893ddb5f63b'
for sourceRow in json.loads(acquisitionPath.read_bytes())['files']:
 assert hashlib.sha256((D/sourceRow['file']).read_bytes()).hexdigest()==sourceRow['sha256']

for name,row in m['packs'].items():
 b=(O/name).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'];packs[name]=b
for key,row in m['volumes'].items():
 f=S/row['sourceFile'];assert sha(f.read_bytes())==row['sourceFileSHA256'];im=nib.load(f);a=im.dataobj.get_unscaled();assert list(a.shape)==row['shape'];assert np.array_equal(im.affine,row['affine']);assert im.dataobj.slope==row['slope'] and im.dataobj.inter==row['intercept'];assert sha(np.asarray(a,dtype=row['dtype']).tobytes())==row['rawCOrderSHA256']
 for axis in range(3):
  group=row['planes'][str(axis)];other=[j for j in range(3)if j!=axis];assert group['uAxis']==other[0] and group['vAxis']==other[1];assert group['width']==a.shape[other[0]] and group['height']==a.shape[other[1]];assert [p['index']for p in group['rows']]==list(range(a.shape[axis]))
  for plane in group['rows']:
   b=packs[plane['pack']][plane['offset']:plane['offset']+plane['compressedBytes']];assert sha(b)==plane['compressedSHA256'];raw=gzip.decompress(b);assert len(raw)==plane['bytes'] and sha(raw)==plane['sha256'];decoded=np.frombuffer(raw,dtype=row['dtype']).reshape(group['height'],group['width']).T;selection=[slice(None)]*3;selection[axis]=plane['index'];original=np.asarray(a[tuple(selection)]);assert np.array_equal(decoded,original);samples+=original.size;planes+=1
 print(key,'every plane matches original source samples',flush=True)
assert planes==m['planeCount']==4944
meshProof=[]
for key,row in m['meshes'].items():
 labelsImage=nib.load(S/m['volumes'][row['rater']]['sourceFile']);labels=np.asarray(labelsImage.dataobj);mask=labels==row['code'];aff=labelsImage.affine
 blob=(O/row['file']).read_bytes();assert len(blob)==row['compressedBytes'] and sha(blob)==row['compressedSHA256'];raw=gzip.decompress(blob);assert sha(raw)==row['sha256'] and len(raw)==row['bytes'];magic,nv,nt,flags=struct.unpack('<4sIII',raw[:16]);assert magic==b'HVX1' and flags==0 and nv==row['vertices'] and nt==row['triangles'];world=np.frombuffer(raw,dtype='<f4',count=nv*3,offset=16).reshape(nv,3).astype(float);faces=np.frombuffer(raw,dtype='<u4',count=nt*3,offset=16+nv*12).reshape(nt,3);assert np.array_equal(np.unique(faces),np.arange(nv))
 recovered=nib.affines.apply_affine(np.linalg.inv(aff),world)*2;corners=np.rint(recovered).astype(np.int64);assert np.max(np.abs(recovered-corners))<1e-3;assert np.all(corners%2!=0);expectedWorld=nib.affines.apply_affine(aff,corners/2);assert np.max(np.abs(world-expectedWorld))<=row['maximumFloat32PositionErrorMm']+1e-12
 v=corners[faces];lo=v.min(1);hi=v.max(1);span=hi-lo;assert np.all(np.sort(span,axis=1)==[0,2,2]);axis=np.argmin(span,axis=1);center=(lo+hi)//2;positive=center//2;negative=positive.copy();negative[np.arange(nt),axis]+=1
 def occupied(points):
  good=np.all((points>=0)&(points<np.array(mask.shape)),axis=1);out=np.zeros(len(points),bool);out[good]=mask[tuple(points[good].T)];return out
 insideP=occupied(positive);insideN=occupied(negative);assert np.all(insideP^insideN);owners=np.where(insideP[:,None],positive,negative);sign=np.where(insideP,1,-1);records=np.column_stack([owners,axis,sign]);unique,inverse,counts=np.unique(records,axis=0,return_inverse=True,return_counts=True);assert np.all(counts==2)
 expected=[];cells=np.argwhere(mask)
 for ax in range(3):
  for sg in [-1,1]:
   neighbor=cells.copy();neighbor[:,ax]+=sg;boundary=cells[~occupied(neighbor)];expected.extend([*map(int,p),ax,sg]for p in boundary)
 assert np.array_equal(unique,np.unique(np.array(expected),axis=0))
 groups=np.argsort(inverse,kind='stable').reshape(-1,2)
 for first,second in groups:
  points,frequency=np.unique(np.concatenate([v[first],v[second]]),axis=0,return_counts=True);assert len(points)==4;diagonal=points[frequency==2];assert diagonal.shape==(2,3);assert sorted(abs(diagonal[1]-diagonal[0]))==[0,2,2]
 triangles=world[faces];normal=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);outward=np.linalg.inv(aff[:3,:3]).T[:,axis].T*sign[:,None];assert np.all(np.einsum('ij,ij->i',normal,outward)>0)
 volume=float(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6);cellVolume=int(mask.sum())*abs(np.linalg.det(aff[:3,:3]));assert abs(volume-cellVolume)<max(.001,cellVolume*1e-5)
 meshProof.append({'key':key,'sourceVoxels':int(mask.sum()),'independentlyReconstructedExposedFaces':len(expected),'triangles':nt,'allTrianglesTileOriginalFacesExactly':True,'outwardWinding':True,'signedFloat32MeshVolume':volume,'sourceCellVolume':cellVolume});print(key,'independent complete face comparison passed',flush=True)
p={'allPassed':True,'planes':planes,'sourceSamplesCompared':samples,'meshes':meshProof,'manifestSHA256':sha((O/'manifest.json').read_bytes()),'archiveSourceAuthenticationPending':True,'clinicalApproval':False,'wholeGoalComplete':False};(D/'native-package-independent-proof.json').write_text(json.dumps(p,indent=2)+'\n');print(json.dumps({'allPassed':True,'planes':planes,'samples':samples,'meshes':len(meshProof)}),flush=True)
