#!/usr/bin/env python3
"""Inspect one licensed native Abaqus ankle pair; never publish or approve it.

C3D10 ordering follows the Abaqus second-order tetrahedron definition:
https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-tritetwedge.htm
Preview tessellation retains corner/midside coordinates; it approximates each
quadratic boundary face with four planar triangles, without fitting/smoothing.
"""
import collections
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np

STAGE = Path('/tmp/primer-msk-sources/ankle-next/leeds-1207')
FILES = ('Ankle1_1_intact.inp', 'Ankle1_1_cysts.inp')
FACES = ((0, 1, 2, 4, 5, 6, 3), (0, 3, 1, 7, 8, 4, 2),
         (1, 3, 2, 8, 9, 5, 0), (2, 3, 0, 9, 7, 6, 1))


def parse(path):
    nodes, elements, sets, instances = {}, {}, {}, []
    active, selected = None, None
    in_part = False
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            fields = [part.strip() for part in line.split(',')]
            active = fields[0].upper()
            props = dict(part.split('=', 1) for part in fields[1:] if '=' in part)
            if active == '*INCLUDE':
                raise ValueError('External includes require explicit review')
            if active == '*PART':
                assert not nodes, 'Only one native part is supported'
                in_part = True
            if active == '*END PART':
                in_part = False
            if active == '*ELEMENT':
                assert props.get('type') == 'C3D10H'
            if active == '*INSTANCE':
                instances.append({'declaration': line, 'transform_lines': []})
            if active == '*ELSET' and in_part:
                assert 'generate' in fields, 'Unexpected non-range tissue set'
                selected = props['elset']
                sets[selected] = []
            continue
        if in_part and active == '*NODE':
            values = line.split(',')
            nodes[int(values[0])] = [float(v) for v in values[1:]]
        elif in_part and active == '*ELEMENT':
            values = [int(v.strip()) for v in line.split(',') if v.strip()]
            assert len(values) == 11
            elements[values[0]] = values[1:]
        elif in_part and active == '*ELSET':
            first, last, step = [int(v) for v in line.split(',')]
            sets[selected].extend(range(first, last + 1, step))
        elif active == '*INSTANCE':
            instances[-1]['transform_lines'].append(line)
    assert len(instances) == 1 and not instances[0]['transform_lines'], 'Non-identity native assembly'
    assert all(len(point) == 3 and np.isfinite(point).all() for point in nodes.values())
    assert set().union(*(set(ids) for ids in sets.values())) == set(elements), 'Every cell is tissue-labelled'
    assert sum(map(len, sets.values())) == len(elements), 'Tissue sets do not overlap'
    return nodes, elements, sets, instances


def boundary(nodes, elements, cell_ids):
    faces = {}
    for cell_id in cell_ids:
        cell = elements[cell_id]
        for pattern in FACES:
            face = tuple(cell[i] for i in pattern)
            key = tuple(sorted(face[:3]))
            if key not in faces:
                faces[key] = [face, 1]
            else:
                assert set(face[:6]) == set(faces[key][0][:6]), 'Shared quadratic faces must match all six nodes'
                faces[key][1] += 1
    assert all(count <= 2 for _, count in faces.values()), 'Nonmanifold tetrahedral face incidence'
    triangles = []
    quadratic = []
    for face, count in faces.values():
        if count != 1:
            continue
        a, b, c, ab, bc, ca, opposite = face
        pa, pb, pc, po = np.array([nodes[i] for i in (a, b, c, opposite)])
        if np.dot(np.cross(pb - pa, pc - pa), po - pa) > 0:
            b, c, ab, ca = c, b, ca, ab
        quadratic.append((a, b, c, ab, bc, ca))
        triangles.extend(((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)))
    ids = np.array(sorted({node for face in quadratic for node in face}), dtype=np.int64)
    mapping = {node: index for index, node in enumerate(ids)}
    points = np.array([nodes[node] for node in ids], dtype=np.float64)
    indexed = np.array([[mapping[node] for node in face] for face in triangles], dtype=np.int64)
    quad_indexed = np.array([[mapping[node] for node in face] for face in quadratic], dtype=np.int64)
    edges = collections.Counter(tuple(sorted(edge)) for tri in indexed
                                for edge in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])))
    areas = np.linalg.norm(np.cross(points[indexed[:, 1]] - points[indexed[:, 0]],
                                   points[indexed[:, 2]] - points[indexed[:, 0]]), axis=1) / 2
    return points, indexed, ids, quad_indexed, {
        'tetrahedra': len(cell_ids), 'boundary_quadratic_faces': len(quadratic),
        'preview_triangles': len(indexed), 'surface_vertices': len(ids),
        'bounds_native': [points.min(axis=0).tolist(), points.max(axis=0).tolist()],
        'boundary_edges': sum(count == 1 for count in edges.values()),
        'nonmanifold_edges': sum(count > 2 for count in edges.values()),
        'exact_zero_area_preview_triangles': int(np.count_nonzero(areas == 0)),
        'surface_area_native_squared': float(areas.sum()),
    }


def main():
    archive = STAGE / 'FE_input_files.zip'
    report = {'status': 'Research inspection only; not a normal-anatomy or clinically approved atlas',
              'license': 'CC BY 4.0', 'source_doi': '10.5518/1207',
              'source_url': 'https://archive.researchdata.leeds.ac.uk/1016/',
              'license_url': 'https://creativecommons.org/licenses/by/4.0/',
              'attribution': 'Talbott, Harriet and Mengoni, Marlene (2022), Subchondral bone cysts in the ankle: patient-specific finite element study data. University of Leeds. doi:10.5518/1207.',
              'adaptation': 'Boundary faces extracted per native tissue cell set. Quadratic faces retained; four-triangle previews use exact native corner/midside coordinates. No coordinate registration, smoothing, decimation, or tissue synthesis.',
              'coordinate_basis': 'Native Abaqus axes retained; anatomical axis directions and laterality not established.',
              'units': 'Not declared in Abaqus deck. Source publication uses mm/MPa; inferred consistent mm, not independently registered to source MRI.',
              'models': []}
    if archive.exists():
        report['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
        with zipfile.ZipFile(archive) as source:
            for filename in FILES:
                (STAGE / filename).write_bytes(source.read('FE input files/' + filename))
    else:
        raise FileNotFoundError('Complete source archive required for reproducible inspection')
    for filename in FILES:
        source = STAGE / filename
        nodes, elements, sets, instances = parse(source)
        record = {'file': filename, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                  'nodes': len(nodes), 'cells': len(elements), 'instances': instances, 'parts': []}
        for name, cell_ids in sets.items():
            points, triangles, ids, quadratic, stats = boundary(nodes, elements, cell_ids)
            target = STAGE / (source.stem + '-' + name + '.npz')
            np.savez_compressed(target, positions=points, indices=triangles,
                                source_node_ids=ids, quadratic_faces=quadratic,
                                source_element_ids=np.array(cell_ids, dtype=np.int64))
            record['parts'].append({'source_set': name, 'geometry': target.name,
                                    'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), **stats})
        report['models'].append(record)
        print(json.dumps(record, indent=2), flush=True)
    (STAGE / 'mesh-inspection.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
