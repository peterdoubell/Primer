from pathlib import Path
import json,gzip,hashlib
import numpy as np
R=Path(__file__).resolve().parents[2];D=R/'.research/epilepsy-grey-white-20261030';S=R/'web/anatomy/spl-nac-limbic';M=R/'web/anatomy/spl-nac-reporting/manifest.json';assert hashlib.sha256(M.read_bytes()).hexdigest()=='b5b1666410a9ee367bff1d4556afb128e44d41ae339b73660b2191c7a46789d3';m=json.loads(M.read_bytes());assert hashlib.sha256((S/'manifest.json').read_bytes()).hexdigest()=='204f87b6d88a9570eb34664497a1462a5d8bba1afa0c2f7abe1cdf11082de2e6';source=json.loads((S/'manifest.json').read_bytes());row=source['labelVolume'];packed=(S/row['file']).read_bytes();sha=lambda x:hashlib.sha256(x).hexdigest();assert sha(packed)==row['gzipSHA256'];raw=gzip.decompress(packed);assert sha(raw)==row['decodedSHA256'];labels=np.frombuffer(raw,dtype=row['dtype']).reshape(row['shape'],order='F');cortex=next(g['codes']for g in m['groups']if g['id']=='cortex-and-lobes');white=[2,41];records=[]
for axis in range(3):
 left=[slice(None)]*3;right=left.copy();left[axis]=slice(None,-1);right[axis]=slice(1,None);a,b=labels[tuple(left)],labels[tuple(right)]
 for sign in [1,-1]:
  first,second=(a,b)if sign==1 else(b,a);mask=np.isin(first,white)&np.isin(second,cortex);positions=np.argwhere(mask);codes=first[mask];opposite=second[mask]
  if sign==-1:positions[:,axis]+=1
  records.append(np.column_stack([positions,np.full(len(positions),axis),np.full(len(positions),sign),codes,opposite]))
faces=np.concatenate(records).astype(np.int32);assert len(np.unique(faces,axis=0))==len(faces)
# Independent neighbour lookups for every selected contact.
owner=faces[:,:3];adjacent=owner.copy();adjacent[np.arange(len(faces)),faces[:,3]]+=faces[:,4];assert np.array_equal(labels[tuple(owner.T)],faces[:,5]);assert np.array_equal(labels[tuple(adjacent.T)],faces[:,6]);assert np.isin(faces[:,5],white).all() and np.isin(faces[:,6],cortex).all()
centres=owner.astype(float);centres[np.arange(len(faces)),faces[:,3]]+=faces[:,4]*.5;affine=np.asarray(row['voxelToRAS']);world=np.column_stack([affine[i,3]+sum(affine[i,j]*centres[:,j]for j in range(3))for i in range(3)])
np.savez_compressed(D/'source-grey-white-contacts.npz',faces=faces,centresRAS=world)
keys,counts=np.unique(faces[:,5:7],axis=0,return_counts=True);names={x['code']:x['name']for x in m['labels']};pairs=[{'whiteCode':int(k[0]),'corticalCode':int(k[1]),'whiteName':names[int(k[0])],'corticalName':names[int(k[1])],'sourceContactFaces':int(n)}for k,n in zip(keys,counts)]
proof={'sourceManifestSHA256':sha(M.read_bytes()),'labelDecodedSHA256':row['decodedSHA256'],'sourceAffine':row['voxelToRAS'],'corticalCodes':cortex,'whiteCodes':white,'contactFaces':len(faces),'pairs':pairs,'everyContactNeighbourVerified':True,'duplicateFaces':False,'sourceResampled':False,'gapsBridged':False,'anatomicalBoundaryValidated':False,'clinicalApproval':False,'payloadSHA256':sha((D/'source-grey-white-contacts.npz').read_bytes())};(D/'contact-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'contactFaces':len(faces),'sourceClassPairs':len(pairs),'anatomicalBoundaryValidated':False}))
