from pathlib import Path
import json,hashlib
import nibabel as nib
import numpy as np
D=Path.cwd()/'.research/pituitary-case-source-20261101';O=D/'plane-viewer-proof';manifest=json.loads((D/'plane-package/manifest.json').read_bytes());cases=json.loads((O/'browser-cases.json').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();images={};affines={}
for key,row in manifest['volumes'].items():
 path=D/'case-1'/row['sourceFile'];assert sha(path.read_bytes())==row['sourceFileSHA256'];image=nib.load(path);images[key]=image.dataobj.get_unscaled();affines[key]=image.get_sform();assert np.array_equal(affines[key],row['originalSform'])
pixels=0;probes=0
for case in cases:
 for canvas in case['canvases']:
  state=canvas['state'];spec=state['spec'];n,u,v=spec['axis'],spec['u'],spec['v'];W,H=spec['width'],spec['height'];assert n==canvas['axis']and n in [0,1,2]and {n,u,v}=={0,1,2}and spec['index']==case['point'][n];assert W==canvas['width']and H==canvas['height'];y,x=np.indices((H,W));points=np.ones((H,W,4));points[...,n]=spec['index'];points[...,u]=spec['high'][u]-x;points[...,v]=spec['high'][v]-y;p=points[...,:3].astype(int);original=images[case['contrast']][tuple(p.transpose(2,0,1))];low=state['center']-state['width']/2;grey=np.floor(np.clip(255*(original.astype(float)-low)/state['width'],0,255)).astype(np.uint8);rgb=np.repeat(grey[...,None],3,axis=2)
  if canvas['mode']=='marked':
   world=np.einsum('...j,ij->...i',points,affines[case['contrast']])
   for key,on,color in [('tumourGland',state['complex'],[255,168,52]),('carotids',state['carotids'],[92,210,244])]:
    source=np.floor(np.einsum('...j,ij->...i',world,np.linalg.inv(affines[key]))[...,:3]+.5).astype(int);inside=np.all((source>=0)&(source<np.asarray(images[key].shape)),axis=-1);mask=np.zeros((H,W),bool);mask[inside]=images[key][tuple(source[inside].T)]!=0
    if on:rgb[mask]=np.floor(.55*rgb[mask]+.45*np.asarray(color)+.5).astype(np.uint8)
  expected=np.concatenate([rgb,np.full((H,W,1),255,np.uint8)],axis=2);assert sha(expected.tobytes())==canvas['sha256'],(case['contrast'],n,canvas['mode'],case['point']);pixels+=W*H;probe=canvas['probe'];q=probe['providedSourceIJK'];assert images[case['contrast']][tuple(q)]==probe['providedSample'];world=np.einsum('ij,j->i',affines[case['contrast']],np.array([*q,1]));assert np.max(abs(world[:3]-probe['sformRAS']))<1e-10
  for key,field in [('tumourGland','tumourGland'),('carotids','combinedCarotids')]:
   source=np.floor(np.einsum('ij,j->i',np.linalg.inv(affines[key]),world)[:3]+.5).astype(int);assert int(images[key][tuple(source)])==probe[field]
  probes+=1
proof={'allPassed':True,'browserCases':len(cases),'providedSourceIndexPlaneStates':len(cases)*3,'actualPlainAndMarkedCanvasPixelsCompared':pixels,'sourceSamplesAndCoordinateProbesChecked':probes,'allComparisonsUseOriginalNiftiArraysAndExactSuppliedSforms':True,'imageResamplingAppliedByPrimer':False,'originalHeaderChanged':False,'coordinateConflictResolved':False,'clinicalApproval':False,'checkerSHA256':sha(Path(__file__).read_bytes())};(O/'pixel-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
