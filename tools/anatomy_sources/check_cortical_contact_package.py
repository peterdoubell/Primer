"""Decode delivery bytes independently and compare every source vertex and index."""
from pathlib import Path
import gzip,hashlib,json,struct
import numpy as np
R=Path(__file__).resolve().parents[2];D=R/'.research/epilepsy-grey-white-20261030';A=R/'web/anatomy/spl-source-contacts'
sha=lambda x:hashlib.sha256(x).hexdigest()
def main():
    manifest_bytes=(A/'manifest.json').read_bytes();m=json.loads(manifest_bytes);p=json.loads((D/'package-proof.json').read_bytes());row=m['meshes']['contacts'];packed=(D/'native-package'/row['file']).read_bytes();assert len(packed)==p['compressedBytes']==row['compressedBytes'];assert sha(packed)==p['compressedSHA256']==row['compressedSHA256']
    raw=gzip.decompress(packed);assert len(raw)==p['decodedBytes']==row['bytes'];assert sha(raw)==p['decodedSHA256']==row['sha256']
    magic,nv,nt,reserved=struct.unpack_from('<4sIII',raw);assert magic==b'HVX1' and reserved==0 and nv==274786 and nt==548218;assert len(raw)==16+12*nv+12*nt
    positions=np.frombuffer(raw,dtype='<f4',count=nv*3,offset=16).reshape(-1,3);indices=np.frombuffer(raw,dtype='<u4',offset=16+nv*12).reshape(-1,3)
    source=D/'source-contact-mesh.npz';assert sha(source.read_bytes())==p['sourceMeshSHA256']==m['sourceMeshSHA256']
    with np.load(source)as original:
        assert np.array_equal(positions.astype(np.float64),original['positionsRAS']);assert np.array_equal(indices,original['triangleIndices'])
    assert sha(positions.tobytes())==p['positionBytesSHA256'];assert sha(indices.tobytes())==p['indexBytesSHA256'];assert sha(manifest_bytes)==p['manifestSHA256']
    proof={'allPassed':True,'verticesCompared':nv,'trianglesCompared':nt,'allCoordinatesExact':True,'allIndicesExact':True,'manifestSHA256':sha(manifest_bytes),'packageProofSHA256':sha((D/'package-proof.json').read_bytes()),'checkerSHA256':sha(Path(__file__).read_bytes()),'clinicalApproval':False}
    (D/'package-independent-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
