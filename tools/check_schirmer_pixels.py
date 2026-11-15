from pathlib import Path
import hashlib,json
import nibabel as nib
import numpy as np
from scipy.ndimage import binary_erosion
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'web/anatomy/schirmer-vascular';DOC=ROOT/'docs/schirmer-vascular-review-20261026';proof=json.loads((DOC/'reader/viewer-proof.json').read_bytes());assert proof['allPassed'];pins=json.loads((DOC/'source-index.json').read_bytes());sources={}
for row in pins['files']:
 raw=(O/'originals'/row['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];sources[row['file']]=np.asanyarray(nib.load(O/'originals'/row['file']).dataobj)
labels=sources['mni_vascular_territories.nii.gz'];names={'T1':'caa_t1_in_mni_template_smooth.nii.gz','T2':'caa_t2_in_mni_template_smooth.nii.gz','FLAIR':'caa_flair_in_mni_template_smooth.nii.gz'};pixels=0;singletons=0
for case in proof['cases']:
 for row in case['planes']:
  axis=row['axis'];lab=np.moveaxis(labels,axis,-1)[...,case['ijk'][axis]];selected=lab==case['code'];mask=selected&~binary_erosion(selected,structure=np.array([[0,1,0],[1,1,1],[0,1,0]],bool),border_value=0) if case['outline'] else selected
  out=np.empty((*lab.shape,4),np.uint8);out[...,3]=255
  if case['mode']=='mri' and not case['overlay']:mask=np.zeros_like(mask)
  if case['mode']=='mri':
   a=np.moveaxis(sources[names[case['contrast']]],axis,-1)[...,case['ijk'][axis]];g=np.floor(255*np.clip((a-case['low'])/(case['high']-case['low']),0,1)+.5);out[...,:3]=g[...,None];out[...,0][mask]=np.floor(g[mask]*.45+.5);out[...,1][mask]=out[...,2][mask]=np.floor(g[mask]*.45+255*.55+.5)
  else:
   out[:]=[250,248,241,255];out[(lab!=0)&case['context']]=[218,224,220,255];out[mask]=[20,108,108,255]
  raw=np.ascontiguousarray(out.transpose(1,0,2)[::-1]).tobytes();assert hashlib.sha256(raw).hexdigest()==row['sha'],(case['code'],case['contrast'],case['mode'],axis);pixels+=lab.size
  if case['code']==19:assert selected.sum()==1;singletons+=1
result={'allPassed':True,'cases':len(proof['cases']),'planes':len(proof['cases'])*3,'renderedPixelsCompared':pixels,'singleton19PlaneChecks':singletons,'browserProofSHA256':hashlib.sha256((DOC/'reader/viewer-proof.json').read_bytes()).hexdigest(),'oracleSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'clinicalApproval':False,'runtimeBound':True};print(json.dumps(result))
