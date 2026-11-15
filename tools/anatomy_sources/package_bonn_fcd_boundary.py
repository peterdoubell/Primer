"""Encode the independently audited source-cell surface for WebGL delivery."""
from pathlib import Path
import gzip
import hashlib
import json
import struct
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.research/fcd-source-20261028'
OUT = SOURCE / 'native-package'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    proof = json.loads((SOURCE / 'independent-boundary-proof.json').read_bytes())
    original = SOURCE / 'sub-00004-source-boundary.npz'
    assert proof['allPassed'] and proof['completeFaceSetMatched'] and proof['twoTrianglesTileEachFace']
    assert sha(original.read_bytes()) == proof['meshSHA256']
    with np.load(original) as source:
        world = source['world']
        indices = source['triangles']
    assert np.isfinite(world).all() and indices.min() >= 0 and indices.max() < len(world)
    positions = np.asarray(world, dtype='<f4')
    triangles = np.asarray(indices, dtype='<u4')
    error = float(np.max(np.abs(positions.astype(np.float64) - world)))
    assert error < 1e-5 and np.array_equal(triangles, indices)
    raw = struct.pack('<4sIII', b'HVX1', len(positions), len(triangles), 0) + positions.tobytes() + triangles.tobytes()
    encoded = gzip.compress(raw, mtime=0)
    filename = 'lesion-source-boundary.mesh.gz'
    (OUT / filename).write_bytes(encoded)
    row = dict(file=filename, bytes=len(raw), sha256=sha(raw), compressedBytes=len(encoded),
               compressedSHA256=sha(encoded), vertices=len(world), triangles=len(indices),
               maximumFloat32PositionErrorMm=error, sourceMeshSHA256=proof['meshSHA256'],
               sourceROI_SHA256=proof['sourceROI_SHA256'], sourceVoxels=proof['sourceVoxels'],
               coordinateSpace='original ROI affine, millimetres', completeSourceBoundaries=True,
               smoothing=False, decimation=False, boundsMm=[world.min(0).tolist(), world.max(0).tolist()])
    manifest = json.loads((OUT / 'manifest.json').read_bytes())
    assert manifest['volumes']['roi']['sourceSHA256'] == row['sourceROI_SHA256']
    manifest['meshes'] = {'lesion': row}
    manifest['independentMeshDeliveryVerificationPending'] = True
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(row))


if __name__ == '__main__':
    main()
