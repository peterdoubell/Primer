"""Independent whole-volume transition and decoded-triangle verification."""
from pathlib import Path
import gzip,hashlib,json,struct
import nibabel as nib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'web/anatomy/schirmer-vascular';DOC=ROOT/'docs/schirmer-vascular-review-20261026';proof=json.loads((DOC/'mesh-build-proof.json').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();results=[]
for level,name in [('territory','mni_vascular_territories.nii.gz')]:
 raw=(O/'originals'/name).read_bytes();arr=np.asanyarray(nib.Nifti1Image.from_bytes(gzip.decompress(raw)).dataobj);shape=np.array(arr.shape)
 rows=[r for r in proof['rows'] if r['level']==level]
 assert len(rows)==len({r['sourceId'] for r in rows})
 assert {r['sourceId'] for r in rows}==set(np.unique(arr))-{0}
 for row in rows:
  assert sha(raw)==row['sourceSHA256'];mask=arr==row['sourceId'];expected=[]
  def key(cells,axes,signs):return ((cells[:,0]+shape[0]*(cells[:,1]+shape[1]*cells[:,2]))*6+axes*2+(signs>0)).astype(np.int64)
  for axis in range(3):
   pads=[(0,0)]*3;pads[axis]=(1,1);delta=np.diff(np.pad(mask.astype(np.int8),pads),axis=axis);points=np.argwhere(delta!=0);changes=delta[tuple(points.T)];cells=points.copy();cells[:,axis]-=changes<0;expected.extend(key(cells,np.full(len(cells),axis),-changes).tolist())
  decoded={}
  for kind,p in row['files'].items():
   rawp=(O/p['file']).read_bytes();assert sha(rawp)==p['gzipSHA256'];b=gzip.decompress(rawp);assert sha(b)==p['sha256'] and len(b)==p['bytes'];decoded[kind]=b
  faces=np.frombuffer(decoded['faces'],dtype='<i2').reshape(-1,5).astype(np.int64);assert np.all((faces[:,:3]>=0)&(faces[:,:3]<shape));assert np.all((faces[:,3]>=0)&(faces[:,3]<3));assert set(faces[:,4])<={-1,1};actual=key(faces[:,:3],faces[:,3],faces[:,4]);assert len(actual)==len(np.unique(actual));assert np.array_equal(np.sort(actual),np.sort(expected))
  magic,nv,nt,flags=struct.unpack('<4sIII',decoded['mesh'][:16]);assert magic==b'HVX1' and flags==0 and nt==2*len(faces);v=np.frombuffer(decoded['mesh'],dtype='<f4',offset=16,count=nv*3).reshape(-1,3).astype(float);t=np.frombuffer(decoded['mesh'],dtype='<u4',offset=16+nv*12).reshape(-1,3);assert t.max()<nv
  xyz=v[t];norm=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);out=np.zeros((len(faces),3));out[np.arange(len(faces)),faces[:,3]]=faces[:,4]*np.array([-1,1,1])[faces[:,3]];assert np.array_equal(norm,np.repeat(out,2,axis=0));assert np.all(np.linalg.norm(norm,axis=1)==1)
  # Each triangle vertex belongs to the exact source face's four half-grid corners.
  grid=((xyz-[90,-126,-72])*np.array([-2,2,2])).reshape(-1,6,3);centres=faces[:,:3]*2;offsets=grid-centres[:,None,:];assert np.all(np.abs(offsets)==1)
  for axis in range(3):
   use=faces[:,3]==axis;assert np.all(offsets[use,:,axis]==faces[use,4,None])
  edges=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);canonical=np.sort(edges,axis=1);_,inverse=np.unique(canonical,axis=0,return_inverse=True);balance=np.bincount(inverse,weights=np.where(edges[:,0]<edges[:,1],1,-1));assert np.all(balance==0)
  volume=np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6;assert volume==int(mask.sum())==row['voxels']
  results.append({'level':level,'id':row['sourceId'],'faces':len(faces),'triangles':nt,'allSourceFacesExact':True,'outwardWinding':True,'closedOrientedEdges':True,'volumeExact':True})
result={'allPassed':True,'rows':results,'triangles':sum(r['triangles']for r in results),'sourceBuildProofSHA256':sha((DOC/'mesh-build-proof.json').read_bytes()),'verifierSHA256':sha(Path(__file__).read_bytes()),'clinicalApproval':False,'runtimeBound':True};print(json.dumps(result))
