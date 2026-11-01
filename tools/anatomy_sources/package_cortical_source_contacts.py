"""Package verified source contact geometry; pin every delivered byte to the viewer."""
from pathlib import Path
import gzip,hashlib,json,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'.research/epilepsy-grey-white-20261030'
REVIEW=ROOT/'docs/cortical-source-contacts-review-20261101'
ASSETS=ROOT/'web/anatomy/spl-source-contacts'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    index=json.loads((REVIEW/'evidence-index.json').read_bytes())
    for name,digest in index['evidenceSHA256'].items():assert sha((REVIEW/name).read_bytes())==digest
    proof=json.loads((REVIEW/'mesh-proof.json').read_bytes())
    original=SOURCE/'source-contact-mesh.npz';assert sha(original.read_bytes())==proof['meshSHA256']
    manifest_raw=(ASSETS/'manifest.json').read_bytes();manifest=json.loads(manifest_raw)
    assert manifest['sourceMeshSHA256']==proof['meshSHA256'] and manifest['clinicalApproval'] is False
    assert manifest['anatomicalBoundaryValidated'] is False and manifest['completeReportingCoverage'] is False
    with np.load(original)as data:
        world=data['positionsRAS'];triangles=data['triangleIndices'];faces=data['sourceFaces']
    positions=np.asarray(world,dtype='<f4');indices=np.asarray(triangles,dtype='<u4')
    assert np.isfinite(world).all() and np.array_equal(positions.astype(np.float64),world)
    assert np.array_equal(indices,triangles) and len(indices)==548218 and len(positions)==274786
    assert len(faces)*2==len(indices)
    raw=struct.pack('<4sIII',b'HVX1',len(positions),len(indices),0)+positions.tobytes()+indices.tobytes()
    compressed=gzip.compress(raw,mtime=0);row=manifest['meshes']['contacts']
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
    assert len(compressed)==row['compressedBytes'] and sha(compressed)==row['compressedSHA256']
    assert len(manifest['groups'])==len(proof['groups'])==77
    for current,expected in zip(manifest['groups'],proof['groups'],strict=True):
        assert all(current[k]==v for k,v in expected.items())
        start=current['firstTriangle'];end=start+current['triangles'];source_faces=faces[start//2:end//2]
        assert np.all(source_faces[:,5]==current['whiteCode'])and np.all(source_faces[:,6]==current['corticalCode'])
        vertices=world[np.unique(indices[start:end])]
        assert np.array_equal(vertices.min(0),current['boundsRAS'][0]) and np.array_equal(vertices.max(0),current['boundsRAS'][1])
    out=SOURCE/'native-package';out.mkdir(exist_ok=True);(out/row['file']).write_bytes(compressed);(out/'manifest.json').write_bytes(manifest_raw)
    evidence={'allPassed':True,'manifestSHA256':sha(manifest_raw),'sourceMeshSHA256':proof['meshSHA256'],'compressedBytes':len(compressed),'compressedSHA256':sha(compressed),'decodedBytes':len(raw),'decodedSHA256':sha(raw),'positionBytesSHA256':sha(positions.tobytes()),'indexBytesSHA256':sha(indices.tobytes()),'vertices':len(world),'triangles':len(indices),'sourcePairs':77,'float32CoordinatesExact':True,'clinicalApproval':False,'runtimeBound':False,'packagerSHA256':sha(Path(__file__).read_bytes())}
    (SOURCE/'package-proof.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence))
if __name__=='__main__':main()
