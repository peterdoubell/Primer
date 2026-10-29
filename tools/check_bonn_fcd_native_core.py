"""Independent native-NIfTI pixel oracle for the browser core at three axes."""
from pathlib import Path
import tempfile,subprocess,json,hashlib
import nibabel as nib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];S=ROOT/'.research/fcd-source-20261028';M=json.loads((S/'native-package/manifest.json').read_bytes())
core=ROOT/'web/anatomy/bonn-fcd-case4/native-core.js';cases=[];expected=[]
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder)
 for role in ['flair','t1']:
  v=M['volumes'][role];im=nib.load(S/v['sourceFile']);stored=np.asarray(im.dataobj.get_unscaled());scaled=np.asarray(im.dataobj)
  for axis in range(3):
   for index in [0,stored.shape[axis]//2,stored.shape[axis]-1]:
    selection=[slice(None)]*3;selection[axis]=index;raw=stored[tuple(selection)];source=d/f'{len(cases)}.bin';source.write_bytes(np.asarray(raw,dtype='<i2').tobytes())
    grey=np.floor(255*np.clip(scaled[tuple(selection)]/350,0,1)+.5).astype(np.uint8);rgba=np.empty((*grey.shape,4),np.uint8);rgba[:,:,:3]=grey[:,:,None];rgba[:,:,3]=255
    expected.append(rgba[::-1].copy().tobytes());cases.append(dict(volume=v,axis=axis,index=index,file=str(source),output=str(d/f'{len(cases)}.rgba')))
 fixture=d/'cases.json';fixture.write_text(json.dumps(cases));script=d/'check.mjs'
 script.write_text('''import fs from 'node:fs';
const core=await import('data:text/javascript;base64,'+fs.readFileSync(process.argv[2]).toString('base64'));
const cases=JSON.parse(fs.readFileSync(process.argv[3]));
for(const c of cases){const raw=fs.readFileSync(c.file),values=core.decodeStored(raw,c.volume.dtype),r=core.renderNative(values,c.volume,c.axis,0,350);fs.writeFileSync(c.output,r.pixels);
const g=r.geometry;for(const [x,y] of [[0,0],[g.width-1,g.height-1]]){const ijk=core.pixelToVoxel(c.volume,c.axis,c.index,x,y);if(ijk[c.axis]!==c.index||ijk[g.uAxis]!==x||ijk[g.vAxis]!==g.height-1-y)throw Error('Picking mismatch');}}
if(core.annotationAllowed('t1')||!core.annotationAllowed('flair'))throw Error('Registration guard');
let rejected=false;try{core.renderNative(new Int16Array(1),cases[0].volume,0,10,10);}catch{rejected=true;}if(!rejected)throw Error('Invalid window accepted');
''')
 subprocess.run(['node',str(script),str(core),str(fixture)],check=True)
 for case,oracle in zip(cases,expected):assert Path(case['output']).read_bytes()==oracle
proof=dict(allPassed=True,nativePlanes=len(cases),pixelsCompared=sum(len(x)//4 for x in expected),coreSHA256=hashlib.sha256(core.read_bytes()).hexdigest(),browserRenderingVerified=False,clinicalApproval=False)
(S/'native-core-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
