"""Decode delivery bytes independently and compare every vertex and triangle."""
from pathlib import Path
import gzip
import hashlib
import json
import struct
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.research/fcd-source-20261028'
OUT = SOURCE / 'native-package'
manifest = json.loads((OUT / 'manifest.json').read_bytes())
row = manifest['meshes']['lesion']
encoded = (OUT / row['file']).read_bytes()
assert len(encoded) == row['compressedBytes']
assert hashlib.sha256(encoded).hexdigest() == row['compressedSHA256']
raw = gzip.decompress(encoded)
assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
magic, vertices, faces, reserved = struct.unpack_from('<4sIII', raw)
assert magic == b'HVX1' and reserved == 0
assert vertices == row['vertices'] and faces == row['triangles']
assert len(raw) == 16 + vertices * 12 + faces * 12
positions = np.frombuffer(raw, dtype='<f4', count=vertices * 3, offset=16).reshape(-1, 3)
indices = np.frombuffer(raw, dtype='<u4', offset=16 + vertices * 12).reshape(-1, 3)
source_path = SOURCE / 'sub-00004-source-boundary.npz'
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == row['sourceMeshSHA256']
with np.load(source_path) as original:
    world = original['world']
    assert np.array_equal(indices, original['triangles'])
    assert np.array_equal(positions, world.astype('<f4'))
    error = float(np.max(abs(positions.astype(np.float64) - world)))
assert error == row['maximumFloat32PositionErrorMm'] and error < 1e-5
triangle = positions.astype(np.float64)[indices]
areas = np.linalg.norm(np.cross(triangle[:, 1] - triangle[:, 0], triangle[:, 2] - triangle[:, 0]), axis=1)
assert np.all(areas > 0)
proof = dict(allPassed=True, vertices=vertices, triangles=faces,
             allTriangleIndicesExact=True, allVerticesCorrectlyRounded=True,
             maximumPositionErrorMm=error, noDegenerateDeliveredTriangles=True,
             manifestSHA256=hashlib.sha256((OUT / 'manifest.json').read_bytes()).hexdigest(),
             clinicalApproval=False, wholeGoalComplete=False)
(SOURCE / 'independent-mesh-delivery-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof))
