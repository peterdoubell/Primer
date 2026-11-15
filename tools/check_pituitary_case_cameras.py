from pathlib import Path
import gzip,json,struct,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'docs/pituitary-case-source-review-20261101/provided-plane-reader';O=R/('docs/pituitary-case-source-review-20261101/'+('reader-hosted'if '--hosted'in __import__('sys').argv else'reader'));browser=json.loads((O/'browser-proof.json').read_bytes());metadata=json.loads((D/'source-models/proof.json').read_bytes());points=[]
for m in metadata['models']:
 raw=gzip.decompress((D/'source-models'/m['file']).read_bytes());n=struct.unpack('<I',raw[4:8])[0];points.append(np.frombuffer(raw,dtype='<f4',count=n*3,offset=16).reshape(-1,3).astype(float))
world=np.concatenate(points);low,high=world.min(0),world.max(0);center=(low+high)*.5;maxclip=0.;maxrigid=0.
for c in browser['cameras']:
 assert c['center']==np.asarray(center,dtype='<f4').astype(float).tolist();basis=np.array([c['right'],c['up'],c['depth']]);error=float(np.max(abs(np.einsum('ij,kj->ik',basis,basis)-np.eye(3))));assert error<2e-7;maxrigid=max(maxrigid,error);relative=world-center;display=np.column_stack([relative[:,0],relative[:,2],-relative[:,1]]);clip=np.einsum('ij,kj->ik',display,basis)/np.array([c['radius']*c['aspect'],c['radius'],4*c['radius']]);maximum=float(np.max(abs(clip)));assert maximum<1;maxclip=max(maxclip,maximum)
assert len(browser['cameras'])==6 and len(browser['modelGPU'])==2
for viewport in browser['modelGPU']:
 assert len(viewport['models'])==2
 for actual in viewport['models']:
  expected=next(m for m in metadata['models']if m['file']==actual['file']);assert actual['positions']==expected['positionSHA256']and actual['indices']==expected['indexSHA256']
proof={'allPassed':True,'sourceModels':2,'GPUModelReadbacks':4,'GPUUniformCameraStates':6,'allOriginalSourceVerticesInsideFrustum':True,'maxAbsoluteClipCoordinate':maxclip,'maxGPUCameraBasisRigidError':maxrigid,'sourceCoordinatesFitted':False,'coordinateConflictResolved':False,'clinicalApproval':False};(O/'model-camera-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
