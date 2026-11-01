from pathlib import Path
import re
import numpy as np
from tools.anatomy_sources.spl_limbic_source import require

def parse_additional_vtk(path):
    raw = Path(path).read_bytes()
    match = re.match(rb'# vtk DataFile Version [34]\.0\nvtk output\nBINARY\nDATASET POLYDATA\nPOINTS (\d+) float\n', raw)
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
