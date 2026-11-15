"""Bind source labels, exact meshes and native MRI navigation without clinical approval."""
from pathlib import Path
import gzip,hashlib,json,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'web/anatomy/spl-nac-limbic'
OUT=ROOT/'docs/epilepsy-structure-coverage-20261030'
MANIFEST_SHA256='204f87b6d88a9570eb34664497a1462a5d8bba1afa0c2f7abe1cdf11082de2e6'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def decoded(row):
    packed=(SOURCE/row['file']).read_bytes()
    assert len(packed)==row['gzipBytes'] and sha(packed)==row['gzipSHA256']
    raw=gzip.decompress(packed)
    assert len(raw)==row['byteLength'] and sha(raw)==row['decodedSHA256']
    return raw

def transform(matrix,points):
    # Explicit affine arithmetic avoids BLAS-dependent handling of tiny strides.
    p=np.asarray(points,dtype=np.float64)
    return np.stack([matrix[r,3]+sum(matrix[r,c]*p[...,c] for c in range(3)) for r in range(3)],axis=-1)

def main():
    manifest_raw=(SOURCE/'manifest.json').read_bytes();assert sha(manifest_raw)==MANIFEST_SHA256
    m=json.loads(manifest_raw);label=m['labelVolume'];labels=np.frombuffer(decoded(label),dtype=label['dtype']).reshape(label['shape'],order=label['storageOrder'])
    label_affine=np.asarray(label['voxelToRAS']);label_inverse=np.linalg.inv(label_affine)
    scans={k:np.frombuffer(decoded(v),dtype=v['dtype']).reshape(v['shape'],order=v['storageOrder']) for k,v in m['volumes'].items()}
    rows=[]
    for item in m['labels']:
        code=item['code'];coordinates=np.argwhere(labels==code);assert len(coordinates)==item['voxelCount']>0
        center=coordinates.mean(0);focus=coordinates[np.argmin(((coordinates-center)**2).sum(1))];world=transform(label_affine,focus)
        mesh=next(x for x in m['labelMeshes'] if x['code']==code);raw=decoded(mesh)
        magic,nv,nt,reserved=struct.unpack_from('<4sIII',raw)
        assert magic==b'HVX1' and reserved==0 and nv==mesh['vertexCount'] and nt==mesh['triangleCount'] and len(raw)==16+12*nv+12*nt
        assert mesh['sourceVoxelCount']==len(coordinates)
        positions=np.frombuffer(raw,dtype='<f4',count=nv*3,offset=16).reshape(-1,3)
        indices=np.frombuffer(raw,dtype='<u4',offset=16+nv*12).reshape(-1,3)
        assert np.isfinite(positions).all() and indices.max()<nv
        anchors={}
        for modality,scan in scans.items():
            descriptor=m['volumes'][modality];affine=np.asarray(descriptor['voxelToRAS']);native_float=transform(np.linalg.inv(affine),world);native=np.floor(native_float+.5).astype(int)
            assert np.all((native>=0)&(native<np.asarray(scan.shape)))
            native_world=transform(affine,native);label_index=np.floor(transform(label_inverse,native_world)+.5).astype(int)
            assert np.all((label_index>=0)&(label_index<np.asarray(labels.shape)))
            assert int(labels[tuple(label_index)])==code
            anchors[modality]={'sourceIJK':native.tolist(),'sourceWorldRAS':native_world.tolist(),'storedIntensity':float(scan[tuple(native)]),'mappedSourceLabel':code,'distanceFromLabelAnchorMm':float(np.linalg.norm(native_world-world))}
        rows.append({'code':code,'sourceName':item['name'],'sourceVoxels':len(coordinates),'labelAnchorIJK':focus.tolist(),'labelAnchorRAS':world.tolist(),'MRIAnchors':anchors,'meshFile':mesh['file'],'meshSHA256':mesh['gzipSHA256'],'vertices':nv,'triangles':nt,'MRIAnatomicalVisibilityReviewed':False,'clinicalValidation':False})
    assert len(rows)==12
    proof={'auditToolSHA256':sha(Path(__file__).read_bytes()),'manifestSHA256':MANIFEST_SHA256,'sourceCommit':m['sourceCommit'],'payloadHashesVerified':True,'nativeAnchorLabelsVerified':True,'focusRule':'Source-labelled voxel nearest the complete label centroid; no components discarded. Native MRI anchors use nearest original sample and are checked back against the source label grid.','newFittedTransform':False,'MRIResampling':False,'structures':rows,'sourceLabelsAreNotAnatomicalGroundTruth':True,'completeReportingCoverage':False,'wholeGoalComplete':False}
    OUT.mkdir(exist_ok=True);(OUT/'mesial-source-anchors.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'sourceStructures':len(rows),'nativeMRIAnchors':sum(len(x['MRIAnchors'])for x in rows),'sourcePayloadsVerified':True,'clinicalAdequacyClaimed':False}))
if __name__=='__main__':main()
