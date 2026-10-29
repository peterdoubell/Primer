"""Compare actual browser canvas readback with original FLAIR and ROI samples."""
from pathlib import Path
import hashlib,json,nibabel as nib,numpy as np
R=Path(__file__).resolve().parents[1];S=R/'.research/fcd-source-20261028';M=json.loads((S/'native-package/manifest.json').read_bytes())
def load(role):
 v=M['volumes'][role];p=S/v['sourceFile'];assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sourceSHA256'];return np.asarray(nib.load(p).dataobj)
image,mask=load('flair'),load('roi');coords=np.argwhere(mask==1);centroid=coords.mean(0);focus=coords[np.argmin(((coords-centroid)**2).sum(1))];assert focus.tolist()==[71,177,148] and mask[tuple(focus)]==1
rows=json.loads((S/'browser-lesion-pixels.json').read_bytes());assert len(rows)==3 and {r['axis'] for r in rows}=={0,1,2};count=0
for row in rows:
 a=row['axis'];selection=[slice(None)]*3;selection[a]=focus[a];grey=np.floor(255*np.clip(image[tuple(selection)]/350,0,1)+.5);labels=mask[tuple(selection)]==1
 rgb=np.repeat(grey[:,:,None],3,axis=2);rgb[labels]=np.floor(.55*rgb[labels]+.45*np.array([255,100,20])+.5);rgba=np.empty((*grey.shape,4),np.uint8);rgba[:,:,:3]=rgb;rgba[:,:,3]=255
 actual=np.array(row['pixels'],np.uint8).reshape(row['height'],row['width'],4);assert np.array_equal(actual,rgba.transpose(1,0,2)[::-1]);count+=grey.size
proof=dict(allPassed=True,sourceLabelledFocusIJK=focus.tolist(),nativePlanes=3,actualBrowserPixelsCompared=count,crosshairsSeparateFromMRI=True,productionVerified=False,clinicalApproval=False)
(S/'browser-pixel-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
