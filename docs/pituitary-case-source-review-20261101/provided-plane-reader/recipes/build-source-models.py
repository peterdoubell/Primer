from pathlib import Path
import json,gzip,struct,hashlib,itertools
import nibabel as nib
import numpy as np
D=Path.cwd()/'.research/pituitary-case-source-20261101';O=D/'source-models';O.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest();rows=[]
for filename,meaning in [('1_tumor_f.nii.gz','source tumour-gland complex'),('1_carotids_f.nii.gz','source combined carotid annotation')]:
 image=nib.load(D/'case-1'/filename);array=np.asanyarray(image.dataobj);assert np.array_equal(np.unique(array),[0,1]);mask=array!=0;cells=np.argwhere(mask);S=image.get_sform();Q=image.get_qform();cellset=set(map(tuple,cells));corners=[];lookup={};triangles=[];faces=[]
 for cell in cells:
  for axis,sign in itertools.product(range(3),[-1,1]):
   other=cell.copy();other[axis]+=sign
   if tuple(other)in cellset:continue
   axes=[i for i in range(3)if i!=axis];quad=[]
   for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:
    p=2*cell.copy();p[axis]+=sign;p[axes[0]]+=a;p[axes[1]]+=b;key=tuple(map(int,p))
    if key not in lookup:lookup[key]=len(corners);corners.append(p)
    quad.append(lookup[key])
   native=np.asarray([corners[i]for i in quad])*.5;xyz=np.einsum('ij,kj->ki',S[:3,:3],native)+S[:3,3]
   if np.dot(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]),S[:3,axis]*sign)<0:quad=[quad[0],quad[3],quad[2],quad[1]]
   triangles.extend([quad[:3],[quad[0],quad[2],quad[3]]]);faces.append([*map(int,cell),axis,sign])
 native=np.asarray(corners)*.5;world=np.einsum('ij,kj->ki',S[:3,:3],native)+S[:3,3];alternative=np.einsum('ij,kj->ki',Q[:3,:3],native)+Q[:3,3];positions=world.astype('<f4');indices=np.asarray(triangles,dtype='<u4');assert np.array_equal(positions.astype(float),world)
 oracle=set()
 for axis,sign in itertools.product(range(3),[-1,1]):
  adjacent=np.zeros_like(mask);target=[slice(None)]*3;neighbour=target.copy();target[axis]=slice(None,-1)if sign==1 else slice(1,None);neighbour[axis]=slice(1,None)if sign==1 else slice(None,-1);adjacent[tuple(target)]=mask[tuple(neighbour)];oracle.update((*map(int,p),axis,sign)for p in np.argwhere(mask&~adjacent))
 assert set(map(tuple,faces))==oracle and len(faces)==len(oracle)
 tri=world[indices];normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);assert np.array_equal(np.linalg.norm(normals,axis=1)*.5,np.full(len(indices),.125))
 for i,f in enumerate(faces):
  outward=S[:3,int(f[3])]*int(f[4]);assert np.all(np.einsum('ij,j->i',normals[2*i:2*i+2],outward)>0)
 # Evaluate volume after a translation only for numerical integration; emitted source coordinates stay untouched.
 relative=world-S[:3,3];t=relative[indices];volume=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6);assert volume==len(cells)*.125
 raw=struct.pack('<4sIII',b'HVX1',len(positions),len(indices),0)+positions.tobytes()+indices.tobytes();name=filename.replace('.nii.gz','.sform.mesh.gz');packed=gzip.compress(raw,mtime=0);(O/name).write_bytes(packed);facebytes=np.asarray(faces,dtype='<i4').tobytes();facefile=name.replace('.mesh.gz','-faces.bin.gz');(O/facefile).write_bytes(gzip.compress(facebytes,mtime=0));np.savez_compressed(O/name.replace('.mesh.gz','-source-corners.npz'),nativeCornersDoubled=np.asarray(corners,dtype='<i4'),originalSform=S,originalQform=Q)
 rows.append({'sourceFile':filename,'sourceMeaning':meaning,'file':name,'sourceCells':len(cells),'sourceFaces':len(faces),'vertices':len(positions),'triangles':len(indices),'gzipSHA256':sha(packed),'decodedSHA256':sha(raw),'positionSHA256':sha(positions.tobytes()),'indexSHA256':sha(indices.tobytes()),'originalSform':S.tolist(),'originalQform':Q.tolist(),'qformAlternativeVertexDisplacementMinMaxMm':[float(np.linalg.norm(alternative-world,axis=1).min()),float(np.linalg.norm(alternative-world,axis=1).max())],'faceProvenance':facefile,'allSourceCellsAndComponentsRetained':True,'allExposedFacesMatchedIndependentFullGridOracle':True,'triangleAreaMm2':.125,'sourceCellEnclosedVolumeMm3':volume,'float32SformCoordinatesExact':True,'sourceCoordinatesFitted':False,'sourceSmoothingOrRepairAppliedByPrimer':False,'sourceImagesAreAcquisitionNative':False,'biologicalWallsResolved':False,'clinicalApproval':False})
proof={'scope':'Exact surfaces of the provided processed source masks under their explicitly retained sform; qform conflict is not corrected','sourceDatasetDOI':'10.6084/m9.figshare.27894084.v1','models':rows,'sourceMRIResampledByPrimer':False,'sourceHeaderChanged':False,'registrationConflictResolved':False,'clinicalApproval':False,'wholeGoalComplete':False};(O/'proof.json').write_text(json.dumps(proof,indent=2)+'\n');print([{'file':r['file'],'vertices':r['vertices'],'triangles':r['triangles'],'sourceFaces':r['sourceFaces'],'cellVolumeMm3':r['sourceCellEnclosedVolumeMm3']}for r in rows])
