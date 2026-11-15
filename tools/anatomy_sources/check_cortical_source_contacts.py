from pathlib import Path
import json,gzip,hashlib
import numpy as np
R=Path(__file__).resolve().parents[2];D=R/'.research/epilepsy-grey-white-20261030';P=json.loads((D/'contact-proof.json').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();assert sha((D/'source-grey-white-contacts.npz').read_bytes())==P['payloadSHA256'];faces=np.load(D/'source-grey-white-contacts.npz')['faces'];m=json.loads((R/'web/anatomy/spl-nac-limbic/manifest.json').read_bytes());v=m['labelVolume'];raw=gzip.decompress((R/'web/anatomy/spl-nac-limbic'/v['file']).read_bytes());assert sha(raw)==P['labelDecodedSHA256'];labels=np.frombuffer(raw,dtype=v['dtype']).reshape(v['shape'],order='F');white=np.argwhere(np.isin(labels,P['whiteCodes']));expected=[]
reporting_path=R/'web/anatomy/spl-nac-reporting/manifest.json';reporting=json.loads(reporting_path.read_bytes());assert sha(reporting_path.read_bytes())==P['sourceManifestSHA256'];assert P['sourceAffine']==v['voxelToRAS'] and P['whiteCodes']==[2,41];assert P['corticalCodes']==next(g['codes']for g in reporting['groups']if g['id']=='cortex-and-lobes')
for axis in range(3):
 for sign in [-1,1]:
  adjacent=white.copy();adjacent[:,axis]+=sign;inside=np.all((adjacent>=0)&(adjacent<np.asarray(labels.shape)),axis=1);owners=white[inside];neighbours=adjacent[inside];codes=labels[tuple(neighbours.T)];keep=np.isin(codes,P['corticalCodes']);owners=owners[keep];codes=codes[keep];expected.append(np.column_stack([owners,np.full(len(owners),axis),np.full(len(owners),sign),labels[tuple(owners.T)],codes]))
expected=np.concatenate(expected).astype(np.int32)
def sorted_rows(a):return a[np.lexsort(tuple(a[:,i]for i in reversed(range(a.shape[1]))))]
assert np.array_equal(sorted_rows(expected),sorted_rows(faces));assert len(faces)==P['contactFaces']
# Preserve source class pairs as contiguous groups in the mesh.
faces=faces[np.lexsort((faces[:,6],faces[:,5]))];N=len(faces);corners=np.repeat((2*faces[:,:3])[:,None,:],4,axis=1);patterns=[[-1,-1],[1,-1],[1,1],[-1,1]]
for axis in range(3):
 mask=faces[:,3]==axis;corners[mask,:,axis]+=faces[mask,4,None]
 for c,(u,w)in enumerate(patterns):corners[mask,c,(axis+1)%3]+=u;corners[mask,c,(axis+2)%3]+=w
vertices,indices=np.unique(corners.reshape(-1,3),axis=0,return_inverse=True);quads=indices.reshape(-1,4);triangles=np.stack([quads[:,[0,1,2]],quads[:,[0,2,3]]],axis=1);affine=np.asarray(P['sourceAffine']);reverse=faces[:,4]*np.linalg.det(affine[:3,:3])<0;triangles[reverse]=triangles[reverse][:,:,::-1];triangles=triangles.reshape(-1,3).astype(np.uint32);native=vertices/2;world=np.column_stack([affine[i,3]+sum(affine[i,j]*native[:,j]for j in range(3))for i in range(3)])
# Every original quad is tiled by its two triangles, with physical winding from white label to cortical label.
tri=world[triangles];normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);expected_normals=np.linalg.inv(affine[:3,:3]).T[:,faces[:,3]].T*faces[:,4,None];assert np.all(np.einsum('ij,ij->i',normals,np.repeat(expected_normals,2,axis=0))>0)
areas=np.linalg.norm(normals,axis=1)/2
for axis in range(3):
 expected_area=np.linalg.norm(np.cross(affine[:3,(axis+1)%3],affine[:3,(axis+2)%3]));assert np.max(abs(areas[np.repeat(faces[:,3]==axis,2)]-expected_area/2))<1e-12
np.savez_compressed(D/'source-contact-mesh.npz',positionsRAS=world,triangleIndices=triangles,sourceFaces=faces,sourceCornersDoubled=vertices)
unique,start,counts=np.unique(faces[:,5:7],axis=0,return_index=True,return_counts=True);groups=[dict(whiteCode=int(k[0]),corticalCode=int(k[1]),firstTriangle=int(i*2),triangles=int(n*2))for k,i,n in zip(unique,start,counts)]
proof={'checkerSHA256':sha(Path(__file__).read_bytes()),'contactProofSHA256':sha((D/'contact-proof.json').read_bytes()),'allSourceContactsMatchedIndependentEnumeration':True,'sourceFaces':N,'vertices':len(world),'triangles':len(triangles),'groups':groups,'sourceToWorldAffine':affine.tolist(),'allTriangleWindingVerified':True,'allTriangleAreasVerified':True,'meshSHA256':sha((D/'source-contact-mesh.npz').read_bytes()),'clinicalAnatomicalBoundaryApproval':False,'sourceGridCellFacesNotBiologicalCorticalArea':True,'smoothing':False,'gapsBridged':False,'completeReportingCoverage':False};(D/'mesh-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:proof[k]for k in ['sourceFaces','vertices','triangles','allSourceContactsMatchedIndependentEnumeration','clinicalAnatomicalBoundaryApproval']}))
