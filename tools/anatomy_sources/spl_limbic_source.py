"""Strict original NRRD/VTK parsing for the pinned SPL limbic source package."""
import gzip
import hashlib
from pathlib import Path
import re
import struct

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / '.research/limbic-next-20261016'
SOURCE = RESEARCH / 'spl'
PROPOSAL = RESEARCH / 'transport-proposal'
REVIEW = ROOT / 'docs/spl-limbic-source-review-20261016'
COMMIT = 'bec24db25aad5f7600e2df3becfb1f883e61ff56'
CODES = (17, 53, 18, 54, 3007, 3005, 3003, 3002, 1016, 2016, 100, 200)
VOLUMES = {'T1w': 'slicer/volumes/imaging/A1_grayT1.nrrd',
           'T2w': 'slicer/volumes/imaging/A1_grayT2.nrrd',
           'labels': 'slicer/volumes/labels/hncma-atlas.nrrd'}
RAS_FROM_LPS = np.diag([-1., -1., 1., 1.])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_nrrd(path):
    raw = Path(path).read_bytes()
    header, packed = raw.split(b'\n\n', 1)
    text = header.decode('ascii')
    require(text.startswith('NRRD0004\n'), 'Unexpected NRRD version')
    fields = dict(line.split(':', 1) for line in text.splitlines()[1:] if line and not line.startswith('#'))
    fields = {key.strip(): value.strip() for key, value in fields.items()}
    require(fields['dimension'] == '3' and fields['space'] == 'left-posterior-superior'
            and fields['encoding'] == 'gzip' and fields['endian'] == 'little', 'Unreviewed NRRD layout')
    dtype = {'float': '<f4', 'short': '<i2'}[fields['type']]
    shape = tuple(int(x) for x in fields['sizes'].split())
    vectors = [tuple(float(x) for x in group.split(',')) for group in re.findall(r'\(([^)]+)\)', fields['space directions'])]
    origin = [float(x) for x in fields['space origin'].strip('()').split(',')]
    require(len(shape) == len(vectors) == len(origin) == 3 and all(len(v) == 3 for v in vectors), 'NRRD spatial dimensions differ')
    lps = np.eye(4)
    lps[:3, :3] = np.asarray(vectors).T
    lps[:3, 3] = origin
    ras = RAS_FROM_LPS @ lps
    decoded = gzip.decompress(packed)
    require(len(decoded) == np.prod(shape) * np.dtype(dtype).itemsize, 'NRRD sample byte count differs')
    array = np.frombuffer(decoded, dtype=dtype).reshape(shape, order='F')
    require(np.isfinite(array).all(), 'Original source volume has nonfinite samples')
    return {'raw': raw, 'header': text, 'fields': fields, 'gzip': packed, 'decoded': decoded,
            'array': array, 'shape': shape, 'dtype': dtype, 'voxelToLPS': lps, 'voxelToRAS': ras}


def parse_vtk(path):
    raw = Path(path).read_bytes()
    match = re.match(rb'# vtk DataFile Version 3\.0\nvtk output\nBINARY\nDATASET POLYDATA\nPOINTS (\d+) float\n', raw)
    require(match is not None, 'Unexpected original VTK header')
    vertices = int(match[1])
    start = match.end()
    positions_raw = raw[start:start + 12 * vertices]
    positions = np.frombuffer(positions_raw, '>f4').reshape(vertices, 3)
    cursor = start + len(positions_raw)
    require(raw[cursor:cursor + 1] == b'\n', 'Missing VTK points terminator')
    match = re.match(rb'\nTRIANGLE_STRIPS (\d+) (\d+)\n', raw[cursor:])
    require(match is not None, 'Original VTK strip topology is missing')
    strip_count, strip_int_count = int(match[1]), int(match[2])
    cursor += match.end()
    strips_raw = raw[cursor:cursor + 4 * strip_int_count]
    strips = np.frombuffer(strips_raw, '>i4')
    cursor += len(strips_raw)
    match = re.match(rb'\nPOINT_DATA (\d+)\nNORMALS Normals float\n', raw[cursor:])
    require(match is not None and int(match[1]) == vertices, 'Original per-vertex normals differ')
    cursor += match.end()
    normals_raw = raw[cursor:cursor + 12 * vertices]
    normals = np.frombuffer(normals_raw, '>f4').reshape(vertices, 3)
    cursor += len(normals_raw)
    require(not raw[cursor:].strip(), 'Unparsed original VTK data remains')
    require(np.isfinite(positions).all() and np.isfinite(normals).all(), 'Original VTK has nonfinite vectors')
    triangles, provenance = [], []
    cursor = 0
    for strip in range(strip_count):
        size = int(strips[cursor])
        points = strips[cursor + 1:cursor + 1 + size]
        require(size >= 3 and len(points) == size and points.min() >= 0 and points.max() < vertices, 'Invalid original strip index')
        for offset in range(size - 2):
            triangle = [int(points[offset]), int(points[offset + 1]), int(points[offset + 2])]
            if offset % 2:
                triangle[0], triangle[1] = triangle[1], triangle[0]
            triangles.append(triangle)
            provenance.append([strip, offset])
        cursor += size + 1
    require(cursor == strip_int_count, 'Not all original strip integers were consumed')
    triangles = np.asarray(triangles, dtype='<u4')
    return {'raw': raw, 'positions': positions, 'normals': normals, 'strips': strips,
            'positionsRaw': positions_raw, 'normalsRaw': normals_raw, 'stripsRaw': strips_raw,
            'triangles': triangles, 'triangleProvenance': np.asarray(provenance, dtype='<u4'),
            'vertexCount': vertices, 'triangleCount': len(triangles),
            'stripCount': strip_count, 'stripIntCount': strip_int_count}


def pack_mesh(model):
    positions = model['positions'].astype('<f4').tobytes()
    normals = model['normals'].astype('<f4').tobytes()
    triangles = model['triangles'].tobytes()
    strips = model['strips'].astype('<i4').tobytes()
    for value, original, dtype in [(positions, model['positionsRaw'], '>f4'),
                                    (normals, model['normalsRaw'], '>f4'),
                                    (strips, model['stripsRaw'], '>i4')]:
        decoded = np.frombuffer(value, '<f4' if dtype.endswith('f4') else '<i4')
        require(decoded.astype(dtype).tobytes() == original, 'Original VTK bits changed across byte-order conversion')
    header = struct.pack('<4sIII', b'HVX1', model['vertexCount'], model['triangleCount'], 0)
    payload = header + positions + triangles
    layout = {'headerBytes': 16, 'magic': 'HVX1', 'byteOrder': 'little',
              'headerFields': ['magic[4]', 'vertexCount:uint32', 'triangleCount:uint32', 'reserved:uint32=0'],
              'positions': {'offset': 16, 'dtype': '<f4', 'components': 3, 'count': model['vertexCount']},
              'triangles': {'offset': 16 + len(positions), 'dtype': '<u4', 'components': 3, 'count': model['triangleCount']}}
    return payload, layout, {'normals': normals, 'originalStrips': strips}


def deterministic_gzip(raw):
    packed = bytearray(gzip.compress(raw, compresslevel=9, mtime=0))
    packed[9] = 255
    require(gzip.decompress(packed) == raw, 'Gzip round-trip changed source bytes')
    return bytes(packed)


def apply_affine(matrix, points):
    return np.einsum('ij,kj->ik', np.asarray(points, dtype='f8'), matrix[:3, :3], optimize=False) + matrix[:3, 3]
