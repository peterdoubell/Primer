from pathlib import Path
import gzip,hashlib,io,json,zipfile,argparse
import nibabel as nib
import numpy as np
from scipy.ndimage import binary_erosion
parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,required=True);args=parser.parse_args();R=Path(__file__).resolve().parents[1];O=R/'docs/holiatlas-schematic-review-20261026/reader';raw=args.archive.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(raw)=='6932bc8063568f0037627d5b85199ff6142b4457413f8fef8817871a3ffa1ee5'
with zipfile.ZipFile(io.BytesIO(raw)) as z:native=gzip.decompress(z.read('substructure_atlas.nii.gz'))
assert sha(native)=='6d34608fd32ecb04eda638e7877cc90f903cb7edf16d7fbf84e1b8819c8ae7d8'
v=np.asanyarray(nib.Nifti1Image.from_bytes(native).dataobj);proof=json.loads((O/'viewer-browser-proof.json').read_bytes());assert proof['allPassed'];pixels=0
for case in proof['cases']:
 assert case['codes']==([170,178] if case['code']==17 else [171,179])
 for row in case['planes']:
  p=np.take(v,case['ijk'][row['axis']],axis=row['axis']);selected=np.isin(p,case['codes']);mask=selected&~binary_erosion(selected,structure=np.array([[0,1,0],[1,1,1],[0,1,0]],bool),border_value=0) if case['outline'] else selected
  out=np.empty((*p.shape,4),np.uint8);out[:]=[250,248,241,255]
  if case['context']:out[p!=0]=[218,224,220,255]
  out[mask]=[20,108,108,255];expected=np.ascontiguousarray(out.transpose(1,0,2)[::-1]).tobytes()
  assert row['width']==p.shape[0] and row['height']==p.shape[1] and sha(expected)==row['sha'];pixels+=p.size
mri_pixels=0
manifest=json.loads((R/'web/anatomy/holiatlas/manifest.json').read_bytes())
for contrast in ['T1','T2','WMn']:
 info=manifest['volumes'][contrast]
 with zipfile.ZipFile(io.BytesIO(raw)) as z:image_native=gzip.decompress(z.read(info['sourceMember']))
 assert sha(image_native)==info['sourceNativeNIfTISHA256']
 image=np.asanyarray(nib.Nifti1Image.from_bytes(image_native).dataobj)
 for case in [c for c in proof['mriCases'] if c['contrast']==contrast]:
  assert case['codes']==([170,178] if case['code']==17 else [171,179])
  for row in case['planes']:
   axis=row['axis'];labels=np.take(v,case['ijk'][axis],axis=axis);values=np.take(image,case['ijk'][axis],axis=axis).astype(np.float64)
   gray=np.floor(255*np.clip((values-case['low'])/(case['high']-case['low']),0,1)+.5).astype(np.uint8)
   out=np.empty((*gray.shape,4),np.uint8);out[...,:3]=gray[...,None];out[...,3]=255
   if case['overlay']:
    selected=np.isin(labels,case['codes']);mask=selected&~binary_erosion(selected,structure=np.array([[0,1,0],[1,1,1],[0,1,0]],bool),border_value=0) if case['outline'] else selected
    out[...,0][mask]=np.floor(gray[mask]*.45+.5).astype(np.uint8)
    out[...,1][mask]=out[...,2][mask]=np.floor(gray[mask]*.45+255*.55+.5).astype(np.uint8)
   assert sha(np.ascontiguousarray(out.transpose(1,0,2)[::-1]).tobytes())==row['sha'],(contrast,case['code'],axis,case['outline'],case['overlay'])
   mri_pixels+=gray.size
result={'allPassed':True,'browserCases':len(proof['cases']),'planes':len(proof['cases'])*3,'nativePixelsCompared':pixels,'mriCases':len(proof['mriCases']),'mriPlanes':len(proof['mriCases'])*3,'mriNativePixelsCompared':mri_pixels,'sourceNativeSHA256':sha(native),'browserProofSHA256':sha((O/'viewer-browser-proof.json').read_bytes()),'productionVerified':False,'clinicalApproval':False};(O/'viewer-native-proof.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
