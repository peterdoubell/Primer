"""Independent global label-transition oracle and binary mesh checks."""
from pathlib import Path
import gzip,io,json,struct,zipfile,hashlib,datetime,gc
import numpy as np
import nibabel as nib
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'boundaries';proof=json.loads((OUT/'boundary-proof.json').read_text());assert proof['allPassed'] and len(proof['rows'])==332
sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(ROOT/'atlas_v1.0.zip') as z:raw=gzip.decompress(z.read('substructure_atlas.nii.gz'))
assert sha(raw)==proof['sourceLabelSHA256'];h=nib.Nifti1Header.from_fileobj(io.BytesIO(raw[:352]));data=np.frombuffer(raw,offset=int(h['vox_offset']),dtype=h.get_data_dtype()).reshape(h.get_data_shape(),order='F');A=h.get_sform();assert np.array_equal(A,h.get_qform());shape=np.array(data.shape);ny,nz=int(shape[1]),int(shape[2]);codes=[];keys=[]
def record(code,cell,axis,sign):
 keep=code!=0;code=code[keep];cell=cell[keep].astype(np.int64);key=(((cell[:,0]*ny+cell[:,1])*nz+cell[:,2])*6+axis*2+(1 if sign>0 else 0)).astype(np.uint64);codes.append(code.astype(np.uint16));keys.append(key)
# One global pass finds transitions between unequal adjacent label values. It
# does not use per-class cropped masks, generator face lists or pair counts.
for axis in range(3):
 left=[slice(None)]*3;right=left.copy();left[axis]=slice(None,-1);right[axis]=slice(1,None);a=data[tuple(left)];b=data[tuple(right)];cell=np.argwhere(a!=b);codeA=a[tuple(cell.T)];codeB=b[tuple(cell.T)];record(codeA,cell,axis,1);cell=cell.copy();cell[:,axis]+=1;record(codeB,cell,axis,-1)
 for sign in [-1,1]:
  border=[slice(None)]*3;border[axis]=0 if sign<0 else int(shape[axis]-1);v=data[tuple(border)];remaining=[i for i in range(3) if i!=axis];ij=np.argwhere(v!=0);xyz=np.zeros((len(ij),3),np.int64);xyz[:,axis]=0 if sign<0 else shape[axis]-1;xyz[:,remaining]=ij;record(v[tuple(ij.T)],xyz,axis,sign)
 del a,b,cell;gc.collect()
codes=np.concatenate(codes);keys=np.concatenate(keys);order=np.lexsort((keys,codes));codes=codes[order];keys=keys[order];del order
assert len(keys)==sum(r['faces'] for r in proof['rows']);assert not np.any((codes[1:]==codes[:-1])&(keys[1:]==keys[:-1]));oracleSHA=sha(codes.tobytes()+keys.tobytes());results=[]
for row in proof['rows']:
 code=row['code'];faceBytes=gzip.decompress((OUT/row['facesPayload']['file']).read_bytes());assert sha(faceBytes)==row['facesPayload']['sha256'];f=np.frombuffer(faceBytes,dtype='<i2').reshape(-1,5);F=len(f);cell=f[:,:3].astype(np.int64);faceKey=(((cell[:,0]*ny+cell[:,1])*nz+cell[:,2])*6+f[:,3]*2+(f[:,4]>0)).astype(np.uint64);lo=np.searchsorted(codes,code,'left');hi=np.searchsorted(codes,code,'right');assert np.array_equal(np.sort(faceKey),keys[lo:hi])
 mesh=gzip.decompress((OUT/row['mesh']['file']).read_bytes());assert sha(mesh)==row['mesh']['sha256'];magic,V,T,reserved=struct.unpack_from('<4sIII',mesh);assert magic==b'HVX1' and reserved==0 and T==2*F and len(mesh)==16+12*V+12*T
 p=np.frombuffer(mesh,dtype='<f4',count=V*3,offset=16).reshape(-1,3);t=np.frombuffer(mesh,dtype='<u4',count=T*3,offset=16+12*V).reshape(-1,3);assert t.max()<V and np.isfinite(p).all();xyz=p[t].astype(np.float64);six=xyz.reshape(F,6,3);center=cell*.5+A[:3,3];delta=six-center[:,None,:]
 quadrant=np.zeros((F,6),np.uint8)
 for axis in range(3):
  use=f[:,3]==axis;others=[i for i in range(3) if i!=axis];assert np.array_equal(delta[use,:,axis],np.repeat((f[use,4]*.25)[:,None],6,axis=1));assert np.all(np.abs(delta[use][:,:,others])==.25);quadrant[use]=(delta[use,:,others[0]]>0).astype(np.uint8)+2*(delta[use,:,others[1]]>0)
 counts=np.stack([(quadrant==q).sum(axis=1) for q in range(4)],axis=1);assert np.all(np.sort(counts,axis=1)==[1,1,2,2]);assert np.all(((counts[:,0]==2)&(counts[:,3]==2))|((counts[:,1]==2)&(counts[:,2]==2)))
 assert np.all(np.diff(np.sort(quadrant.reshape(F,2,3),axis=2),axis=2)>0)
 normal=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);expected=np.eye(3)[f[:,3]]*f[:,4,None]*.25;assert np.array_equal(normal,np.repeat(expected,2,axis=0));volume=float(np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6);assert volume==row['sourceVoxels']*.125
 edges=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);direction=np.where(edges[:,0]<edges[:,1],1,-1);key=(np.minimum(edges[:,0],edges[:,1]).astype(np.uint64)<<32)|np.maximum(edges[:,0],edges[:,1]).astype(np.uint64);unique,inverse,incidence=np.unique(key,return_inverse=True,return_counts=True);balance=np.bincount(inverse,weights=direction,minlength=len(unique));assert np.all(balance==0) and np.all(incidence>=2);values,frequency=np.unique(incidence,return_counts=True)
 results.append({'code':code,'sourceName':row['sourceName'],'exactCompleteGlobalOracleFaces':True,'everyTriangleHasSourceSquareCorners':True,'eachFaceUsesAnActualSquareDiagonal':True,'everyTriangleWindsOutward':True,'signedVolumeMM3':volume,'closedOrientedEdgeBalance':True,'edgeIncidenceHistogram':{str(int(a)):int(b) for a,b in zip(values,frequency)},'sourceContactsLeftUnrepaired':True});print('Verified',code,F,flush=True);del mesh,faceBytes,f,cell,p,t,xyz,six,center,delta,quadrant,counts,normal,expected,edges,key,inverse,unique,incidence,balance;gc.collect()
result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Binary meshes against independent global source-label transitions; no anatomical/clinical approval or runtime delivery claim','allPassed':True,'classes':len(results),'faces':len(keys),'triangles':2*len(keys),'globalOracleSHA256':oracleSHA,'sourceLabelSHA256':sha(raw),'rows':results};(OUT/'independent-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
