"""Original-DICOM RGB oracle for complete native index planes."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.research/pulmonary-intake-20261011/python-deps'))
import pydicom
OUT=ROOT/'web/anatomy/lidc-idri-0525'


def main():
    m=json.loads((OUT/'manifest.json').read_text())
    # Re-read originals, not the browser transport payload.
    ct=np.stack([pydicom.dcmread(OUT/'original-ct'/r['filename']).pixel_array for r in m['ct']['slices']])
    presets=[[0,0,0],[511,511,428],[256,256,328]]
    import gzip
    for a in m['annotations']:
        raw=np.frombuffer(gzip.decompress((OUT/a['mask']['file']).read_bytes()),dtype=np.uint8).reshape((-1,512,512))
        z,y,x=np.nonzero(raw)
        # Javascript Math.round rounds nonnegative half values upwards.
        presets.append([int(np.floor(x.mean()+.5)),int(np.floor(y.mean()+.5)),int(np.floor(np.asarray(a['source_CT_slice_indices'])[z].mean()+.5))])
    rows=[]
    for p in presets:
        planes=[ct[:,:,p[0]][::-1],ct[:,p[1],:][::-1],ct[p[2],:,:]]
        values=[]
        for plane in planes:
            hu=plane.astype(np.float64)-1024
            g=np.clip(np.floor((hu+1000)*255/1400+.5),0,255).astype(np.uint8)
            image=np.empty(g.shape+(4,),dtype=np.uint8);image[:,:,:3]=g[:,:,None];image[:,:,3]=255
            values.append(dict(width=g.shape[1],height=g.shape[0],rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest()))
        r=m['ct']['slices'][p[2]];values_raw=int(ct[p[2],p[1],p[0]])
        rows.append(dict(cursor=p,planes=values,raw=values_raw,HU=values_raw-1024,
                         LPS=[r['position_LPS_mm'][0]+p[0]*r['pixel_spacing_mm'][1],r['position_LPS_mm'][1]+p[1]*r['pixel_spacing_mm'][0],r['position_LPS_mm'][2]]))
    path=ROOT/'docs/pulmonary-nodule-source-review-20261011/original-DICOM-pixel-oracle.json'
    path.write_text(json.dumps(dict(manifest_sha256=hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest(),display_window_HU=[-1000,400],rows=rows),indent=2)+'\n')
    print('original_DICOM_native_plane_oracles',len(rows)*3)


if __name__=='__main__':main()
