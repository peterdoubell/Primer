from pathlib import Path
import gzip,json,struct,hashlib,itertools,inspect
import nibabel as nib
import numpy as np
D=Path.cwd()/'.research/pituitary-case-source-20261101';O=D/'source-models';proof=json.loads((O/'proof.json').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();rows=[]
for row in proof['models']:
 image=nib.load(D/'case-1'/row['sourceFile']);array=np.asanyarray(image.dataobj);owners=np.argwhere(array!=0);expected=set()
 for axis,sign in itertools.product(range(3),[-1,1]):
  q=owners.copy();q[:,axis]+=sign;inside=np.all((q>=0)&(q<np.asarray(array.shape)),axis=1);p=owners[inside];q=q[inside];outside=array[tuple(q.T)]==0;expected.update((*map(int,c),axis,sign)for c in p[outside]);expected.update((*map(int,c),axis,sign)for c in owners[~inside])
 encoded=(O/row['file']).read_bytes();assert sha(encoded)==row['gzipSHA256'];raw=gzip.decompress(encoded);assert sha(raw)==row['decodedSHA256'];magic,n,t,flags=struct.unpack('<4sIII',raw[:16]);assert magic==b'HVX1'and flags==0 and n==row['vertices']and t==row['triangles'];world=np.frombuffer(raw,dtype='<f4',count=n*3,offset=16).reshape(-1,3).astype(float);indices=np.frombuffer(raw,dtype='<u4',offset=16+n*12).reshape(-1,3);S=image.get_sform();inverse=np.linalg.inv(S);native=np.einsum('ij,kj->ki',inverse[:3,:3],world)+inverse[:3,3];assert np.array_equal(native*2,np.round(native*2));faces=np.frombuffer(gzip.decompress((O/row['faceProvenance']).read_bytes()),dtype='<i4').reshape(-1,5);assert set(map(tuple,faces))==expected and len(faces)*2==t
 for i,face in enumerate(faces):
  p=face[:3];axis=int(face[3]);sign=int(face[4]);other=[a for a in range(3)if a!=axis];actual=native[np.unique(indices[2*i:2*i+2])];wanted={tuple(p+np.eye(3)[axis]*sign*.5+np.eye(3)[other[0]]*a*.5+np.eye(3)[other[1]]*b*.5)for a,b in itertools.product([-1,1],repeat=2)};assert len(actual)==4 and set(map(tuple,actual))==wanted
 xyz=world[indices];normal=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);assert np.array_equal(np.linalg.norm(normal,axis=1)*.5,np.full(t,.125));outward=S[:3,faces[:,3]].T*faces[:,4,None];assert np.all(np.einsum('ij,ij->i',normal,np.repeat(outward,2,axis=0))>0)
 assert np.max(abs(image.get_qform()-image.get_sform()))==22.5
 rows.append({'sourceFile':row['sourceFile'],'allOriginalExposedCellFacesVerified':True,'sourceFaces':len(faces),'triangles':t,'allNativeHalfCellCornersVerified':True,'allTriangleAreasAndWindingVerified':True,'qformAlternativeRetainedNotRepaired':True})
result={'allPassed':True,'models':rows,'sourceHeaderOrSamplesChanged':False,'anatomicalWallValidation':False,'clinicalApproval':False};(O/'independent-proof.json').write_text(json.dumps(result,indent=2)+'\n');(O/'nibabel-affine-selection-source.txt').write_text('Installed nibabel '+nib.__version__+'\n'+inspect.getsource(nib.Nifti1Header.get_best_affine));print(result)
