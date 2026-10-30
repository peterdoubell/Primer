"""Independent original-array and actual PNG-centre comparison for review sheets."""
from pathlib import Path
import gzip,hashlib,json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];S=R/'web/anatomy/spl-nac-limbic';D=R/'docs/epilepsy-structure-coverage-20261030/native-review'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def array(row):
    packed=(S/row['file']).read_bytes();assert sha(packed)==row['gzipSHA256']
    raw=gzip.decompress(packed);assert sha(raw)==row['decodedSHA256'] and len(raw)==row['byteLength']
    return np.frombuffer(raw,dtype=row['dtype']).reshape(row['shape'],order=row['storageOrder'])
def main():
    manifest_raw=(S/'manifest.json').read_bytes();m=json.loads(manifest_raw);p=json.loads((D/'proof.json').read_bytes());assert sha(manifest_raw)==p['sourceManifestSHA256'];assert sha((R/'tools/anatomy_sources/render_epilepsy_mesial_review.py').read_bytes())==p['generatorSHA256']
    labels=array(m['labelVolume']);scans={key:array(row)for key,row in m['volumes'].items()};samples=0;displayed=0
    for sheet in p['reviewSheets']:
        image=(D/sheet['image']).read_bytes();assert sha(image)==sheet['sha256'];png=np.asarray(Image.open(D/sheet['image']).convert('RGB'));height=png.shape[0]
        for panel in sheet['panels']:
            u,v,n=panel['horizontalSourceAxis'],panel['verticalSourceAxis'],panel['normalSourceAxis'];assert sorted([u,v,n])==[0,1,2]
            lower,upper=panel['sourceCropLower'],panel['sourceCropUpperExclusive'];selection=[slice(lower[a],upper[a]) for a in range(3)];selection[n]=panel['sourceSlice'];native=scans[panel['modality']][tuple(selection)];remaining=[a for a in range(3) if a!=n];expected=native if remaining==[v,u] else native.T
            assert list(expected.shape)==panel['shape'] and sha(np.ascontiguousarray(expected).tobytes())==panel['originalPlaneSampleSHA256']
            lo,hi=panel['window'];grey=np.floor(255*np.clip((expected-lo)/(hi-lo),0,1)+.5).astype(np.uint8);rgb=np.repeat(grey[...,None],3,axis=2)
            y,x=np.indices(expected.shape);points=np.ones((*x.shape,4));points[...,u]=x+lower[u];points[...,v]=y+lower[v];points[...,n]=panel['sourceSlice'];mapping=np.linalg.inv(m['labelVolume']['voxelToRAS'])@np.asarray(m['volumes'][panel['modality']]['voxelToRAS']);indices=np.floor(np.einsum('...j,ij->...i',points,mapping)[...,:3]+.5).astype(int);inside=np.all((indices>=0)&(indices<np.array(labels.shape)),axis=-1);mask=np.zeros(expected.shape,bool);mask[inside]=labels[tuple(indices[inside].T)]==sheet['code'];marked=rgb.copy();marked[mask]=np.floor(.65*rgb[mask]+.35*np.array([255,128,0])+.5).astype(np.uint8)
            assert int(mask.sum())==panel['labelPixels'] and sha(rgb.tobytes())==panel['unmarkedRGB_SHA256'] and sha(marked.tobytes())==panel['annotatedRGB_SHA256']
            coords=np.stack([x,y,np.ones_like(x)],axis=-1)
            for matrix,wanted in zip(panel['sourcePixelToFigureMatrices'],[rgb,marked],strict=True):
                positions=np.einsum('...j,ij->...i',coords,np.asarray(matrix));px=np.floor(positions[...,0]).astype(int);py=height-1-np.floor(positions[...,1]).astype(int)
                assert np.all((px>=0)&(px<png.shape[1])&(py>=0)&(py<height))
                actual=png[py,px];assert np.array_equal(actual,wanted),(sheet['code'],panel['modality'],panel['view'],int(np.max(abs(actual.astype(int)-wanted.astype(int)))))
                displayed+=wanted.shape[0]*wanted.shape[1]
            samples+=expected.size
    proof={'allPassed':True,'reviewSheets':len(p['reviewSheets']),'originalSamplesCompared':samples,'renderedPixelCentresCompared':displayed,'sourceProofSHA256':sha((D/'proof.json').read_bytes()),'checkerSHA256':sha(Path(__file__).read_bytes()),'clinicalAdequacyVerified':False}
    (D/'independent-pixel-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
