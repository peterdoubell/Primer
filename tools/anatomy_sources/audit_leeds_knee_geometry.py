#!/usr/bin/env python3
"""Bounded, offline audit of the Leeds 981 LTKN8941 segmented/intact FE input.

This is geometry inspection, not a solver, MRI registration, normal-anatomy
certification or clinical/commercial approval. All ten C3D10 nodes and all six
boundary-face nodes are retained. Preview triangles sample the quadratic map;
they are explicitly an approximation, never a replacement for the source mesh.

References:
https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-tritetwedge.htm
https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-instance.htm
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np


STAGE = Path('/tmp/primer-msk-sources/leeds-knee-981')
SOURCE = STAGE / 'fe-baseline/ltkn8941_seg_intact_fix.inp'
SOURCE_SHA256 = '55b3050e3b6e0ce594d418f865e4bedfeef5bb360f12769de002fadc4d68eb03'
SOURCE_BYTES = 32559198
INTERPOLATION_URL = ('https://docs.software.vt.edu/abaqusv2025/English/'
                     'SIMACAETHERefMap/simathe-c-tritetwedge.htm')
INSTANCE_URL = ('https://docs.software.vt.edu/abaqusv2025/English/'
                'SIMACAEKEYRefMap/simakey-r-instance.htm')
# Abaqus S1..S4: three corners followed by midsides ab, bc, ca.
FACE_NODES = np.array(((0, 1, 2, 4, 5, 6), (0, 3, 1, 7, 8, 4),
                       (1, 3, 2, 8, 9, 5), (2, 3, 0, 9, 7, 6)))
OPPOSITE_NODES = np.array((3, 2, 0, 1))
EDGE_NODES = np.array(((0, 1, 4), (1, 2, 5), (2, 0, 6),
                       (0, 3, 7), (1, 3, 8), (2, 3, 9)))
EXPECTED_SECTIONS = {'PT_FCART', 'PT_FEMUR', 'PT_TIBIA', 'PT_TCART_MED',
                     'PT_TCART_LAT', 'PT_MEDIAL_MEN', 'PT_LATERAL_MEN'}
# Explicitly bounded syntax. Unknown keywords fail, including INCLUDE, SYSTEM,
# NGEN, NFILL, NMAP, IMPORT and any additional geometry representation.
KEYWORDS = set('HEADING|PREPRINT|PART|NODE|ELEMENT|ELSET|SURFACE|SOLID SECTION|'
               'DISTRIBUTION|ORIENTATION|END PART|ASSEMBLY|INSTANCE|END INSTANCE|'
               'NSET|COUPLING|KINEMATIC|SPRING|END ASSEMBLY|DISTRIBUTION TABLE|'
               'MATERIAL|HYPERELASTIC|ELASTIC|SURFACE INTERACTION|FRICTION|'
               'SURFACE BEHAVIOR|BOUNDARY|CONTACT PAIR|STEP|STATIC|CONTROLS|'
               'RESTART|OUTPUT|END STEP|CLOAD|NODE OUTPUT|ELEMENT OUTPUT|'
               'CONTACT OUTPUT'.split('|'))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def blocks(text):
    """Consume every input line; retain every keyword and its source location."""
    block = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            if block is not None:
                yield block
            fields = [v.strip() for v in line[1:].split(',')]
            keyword = fields[0].upper()
            require(keyword in KEYWORDS, f'Unsupported keyword at line {number}: {keyword}')
            props = {v.split('=', 1)[0].upper(): v.split('=', 1)[1].strip()
                     for v in fields[1:] if '=' in v}
            flags = [v.upper() for v in fields[1:] if v and '=' not in v]
            block = {'keyword': keyword, 'parameters': props, 'flags': flags,
                     'line': number, 'declaration': raw, 'data': []}
        else:
            require(block is not None, f'Data before keyword at line {number}')
            block['data'].append((number, line))
    if block is not None:
        yield block


def parse_input(data):
    """Parse this self-contained native deck; do not apply solver displacements."""
    node_rows, cell_rows, assembly_nodes, springs = [], [], [], []
    sets, sections, instances, materials, inventory, spring_settings = {}, [], [], [], [], []
    in_part = in_assembly = in_instance = False
    part_names = []
    for block in blocks(data.decode('ascii')):
        key, props, rows = block['keyword'], block['parameters'], block['data']
        scope = 'part' if in_part else ('instance' if in_instance else
                                      ('assembly' if in_assembly else 'model'))
        inventory.append({k: v for k, v in block.items() if k != 'data'} |
                         {'scope_before_keyword': scope, 'data_lines': len(rows)})
        if key == 'PART':
            require(not in_part and not in_assembly and not part_names, 'Only one part is supported')
            in_part = True
            part_names.append(props['NAME'])
        elif key == 'END PART':
            require(in_part, 'Unbalanced END PART')
            in_part = False
        elif key == 'ASSEMBLY':
            require(not in_part and not in_assembly, 'Invalid assembly scope')
            in_assembly = True
        elif key == 'END ASSEMBLY':
            require(in_assembly and not in_instance, 'Invalid END ASSEMBLY')
            in_assembly = False
        elif key == 'INSTANCE':
            require(in_assembly and not in_instance and not instances, 'Only one part instance supported')
            require(set(props) == {'NAME', 'PART'}, 'Unsupported instance parameters')
            instances.append({'name': props['NAME'], 'part': props['PART'],
                              'transform_lines': [line for _, line in rows],
                              'source_line': block['line']})
            in_instance = True
        elif key == 'END INSTANCE':
            require(in_instance, 'Unbalanced END INSTANCE')
            in_instance = False
        elif key == 'NODE':
            require(not props and not in_instance and (in_part or in_assembly),
                    'Only Cartesian part nodes and assembly reference nodes supported')
            target = node_rows if in_part else assembly_nodes
            for number, line in rows:
                values = [v.strip() for v in line.split(',') if v.strip()]
                require(len(values) == 4, f'Invalid node at line {number}')
                target.append((int(values[0]), *(float(v) for v in values[1:])))
        elif key == 'ELEMENT':
            kind = props.get('TYPE', '').upper()
            require((in_part and kind == 'C3D10') or
                    (in_assembly and not in_instance and kind == 'SPRINGA'),
                    f'Unsupported element scope or type: {kind}')
            for number, line in rows:
                values = [v.strip() for v in line.split(',') if v.strip()]
                if kind == 'C3D10':
                    require(len(values) == 11, f'Expected all ten C3D10 nodes at line {number}')
                    cell_rows.append([int(v) for v in values])
                else:
                    require(len(values) == 3, f'Invalid SpringA at line {number}')
                    springs.append({'id': int(values[0]), 'endpoints': values[1:],
                                    'elset': props['ELSET'], 'source_line': number})
        elif key == 'ELSET' and in_part:
            require(set(props) == {'ELSET'}, 'Unsupported part elset parameters')
            name = props['ELSET']
            target = sets.setdefault(name, [])
            for number, line in rows:
                values = [int(v) for v in line.split(',') if v.strip()]
                if 'GENERATE' in block['flags']:
                    require(len(values) == 3 and values[2] > 0 and values[1] >= values[0],
                            f'Invalid generated elset at line {number}')
                    require((values[1] - values[0]) % values[2] == 0, 'Inexact generated set range')
                    target.extend(range(values[0], values[1] + 1, values[2]))
                else:
                    target.extend(values)
        elif key == 'SOLID SECTION':
            require(in_part, 'Only part solid sections supported')
            sections.append({'elset': props['ELSET'], 'material': props['MATERIAL'],
                             'orientation': props.get('ORIENTATION'), 'source_line': block['line']})
        elif key == 'MATERIAL':
            materials.append(props['NAME'])
        elif key == 'SPRING':
            spring_settings.append({'parameters': props, 'data': [line for _, line in rows],
                                    'source_line': block['line']})
    require(not (in_part or in_assembly or in_instance), 'Unclosed input scope')
    require(len(part_names) == len(instances) == 1, 'Expected one part and instance')
    require(instances[0]['part'] == part_names[0], 'Instance references another part')
    ids = np.array([row[0] for row in node_rows], dtype=np.int64)
    points = np.array([row[1:] for row in node_rows], dtype=np.float64)
    cells = np.array(cell_rows, dtype=np.int64)
    require(len(ids) and len(cells), 'Empty volume geometry')
    require(len(np.unique(ids)) == len(ids) and len(np.unique(cells[:, 0])) == len(cells),
            'Repeated native node or element IDs')
    require(np.isfinite(points).all(), 'Nonfinite coordinates')
    require(np.isin(cells[:, 1:], ids).all(), 'Element references an undefined part node')
    require(all(len(set(row)) == 10 for row in cells[:, 1:]), 'Repeated nodes within C3D10')
    order = np.argsort(ids)
    cell_order = np.argsort(cells[:, 0])
    return {'node_ids': ids[order], 'points': points[order], 'element_ids': cells[cell_order, 0],
            'cells': cells[cell_order, 1:], 'sets': sets, 'sections': sections,
            'instances': instances, 'part': part_names[0], 'materials': materials,
            'assembly_nodes': assembly_nodes, 'springs': springs,
            'spring_settings': spring_settings, 'inventory': inventory}


def instance_matrix(transform_lines):
    """Abaqus: translate, then right-handed rotation around assembly-space a→b."""
    require(len(transform_lines) in (0, 1, 2), 'Unsupported instance positioning data')
    matrix = np.eye(4)
    if not transform_lines:
        return matrix
    translation = np.array([float(v) for v in transform_lines[0].split(',')])
    require(translation.shape == (3,) and np.isfinite(translation).all(), 'Invalid translation')
    matrix[:3, 3] = translation
    if len(transform_lines) == 1:
        return matrix
    values = np.array([float(v) for v in transform_lines[1].split(',')])
    require(values.shape == (7,) and np.isfinite(values).all(), 'Invalid rotation')
    a, b, angle = values[:3], values[3:6], np.deg2rad(values[6])
    axis = b - a
    require(np.linalg.norm(axis) > 0, 'Zero rotation axis')
    x, y, z = axis / np.linalg.norm(axis)
    skew = np.array(((0, -z, y), (z, 0, -x), (-y, x, 0)))
    rotation = np.eye(3) + np.sin(angle) * skew + (1 - np.cos(angle)) * (skew @ skew)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = a + rotation @ (translation - a)
    return matrix


def transform_points(points, matrix):
    return np.asarray(points) @ matrix[:3, :3].T + matrix[:3, 3]


def quadratic_triangle_shape(barycentric):
    """Weights in corner a,b,c then edge ab,bc,ca order."""
    bary = np.asarray(barycentric, dtype=np.float64)
    require(bary.shape[-1] == 3 and np.allclose(bary.sum(axis=-1), 1), 'Invalid triangle barycentrics')
    a, b, c = np.moveaxis(bary, -1, 0)
    return np.stack((a*(2*a-1), b*(2*b-1), c*(2*c-1), 4*a*b, 4*b*c, 4*c*a), axis=-1)


def quadratic_tetrahedron_shape(barycentric):
    """C3D10 interpolation in native Abaqus node order."""
    bary = np.asarray(barycentric, dtype=np.float64)
    require(bary.shape[-1] == 4 and np.allclose(bary.sum(axis=-1), 1), 'Invalid tetrahedron barycentrics')
    a, b, c, d = np.moveaxis(bary, -1, 0)
    return np.stack((a*(2*a-1), b*(2*b-1), c*(2*c-1), d*(2*d-1),
                     4*a*b, 4*b*c, 4*c*a, 4*a*d, 4*b*d, 4*c*d), axis=-1)


def canonical_faces(faces):
    """Canonical corners and edge-associated midsides; never just sort six IDs."""
    permutation = np.argsort(faces[:, :3], axis=1)
    row = np.arange(len(faces))[:, None]
    corners = faces[row, permutation]
    edge_column = np.array(((-1, 3, 5), (3, -1, 4), (5, 4, -1)))
    mids = edge_column[permutation, np.roll(permutation, -1, axis=1)]
    return np.concatenate((corners, faces[row, mids]), axis=1)


def face_topology(cells):
    """Return unique boundaries and paired interior incidences of C3D10 cells."""
    faces = cells[:, FACE_NODES].reshape(-1, 6)
    canonical = canonical_faces(faces)
    order = np.lexsort(canonical[:, :3].T[::-1])
    sorted_faces = canonical[order]
    starts = np.r_[0, np.flatnonzero(np.any(np.diff(sorted_faces[:, :3], axis=0), axis=1)) + 1]
    counts = np.diff(np.r_[starts, len(faces)])
    require(np.all(counts <= 2), 'Nonmanifold volume face incidence (>2 cells)')
    paired = starts[counts == 2]
    require(np.array_equal(sorted_faces[paired], sorted_faces[paired + 1]),
            'Shared corner face has incompatible edge-associated midside nodes')
    interior = np.stack((order[paired], order[paired + 1]), axis=1)
    boundary = order[starts[counts == 1]]
    return {'faces': faces, 'boundary_indices': boundary, 'interior_pairs': interior,
            'unique_faces': len(starts), 'boundary_faces': len(boundary),
            'interior_faces': len(paired)}


def unique_edges(cells):
    edges = cells[:, EDGE_NODES].reshape(-1, 3).copy()
    edges[:, :2].sort(axis=1)
    edges = np.unique(edges, axis=0)
    require(not np.any(np.all(edges[1:, :2] == edges[:-1, :2], axis=1)),
            'One corner edge has multiple midside-node assignments')
    return edges


def bounds(points):
    return [points.min(axis=0).tolist(), points.max(axis=0).tolist()]


def deviation_stats(points, indexed_edges):
    a, b, middle = (points[indexed_edges[:, i]] for i in range(3))
    vector = b - a
    length = np.linalg.norm(vector, axis=1)
    require(np.all(length > 0), 'Zero-length corner edge')
    midpoint_distance = np.linalg.norm(middle - (a+b)/2, axis=1)
    t = np.clip(np.einsum('ij,ij->i', middle-a, vector) / length**2, 0, 1)
    line_distance = np.linalg.norm(middle - (a + t[:, None]*vector), axis=1)
    def summary(values):
        return dict(zip(('min', 'median', 'p95', 'p99', 'max'),
                        np.quantile(values, (0, .5, .95, .99, 1)).tolist()))
    return {'unique_quadratic_edges': len(indexed_edges),
            'midpoint_deviation_native_units': summary(midpoint_distance),
            'distance_to_straight_segment_native_units': summary(line_distance),
            'midpoint_deviation_over_corner_edge_length': summary(midpoint_distance/length),
            'midpoint_deviation_above_1e_6_native_units': int(np.count_nonzero(midpoint_distance > 1e-6))}, midpoint_distance, line_distance


def preview_grid(subdivisions=4):
    require(isinstance(subdivisions, int) and subdivisions >= 2 and subdivisions % 2 == 0,
            'An even subdivision count >=2 is required to include native midside nodes')
    lattice = [(i, j) for i in range(subdivisions+1) for j in range(subdivisions+1-i)]
    lookup = {pair: index for index, pair in enumerate(lattice)}
    triangles = []
    for i in range(subdivisions):
        for j in range(subdivisions-i):
            triangles.append((lookup[i, j], lookup[i+1, j], lookup[i, j+1]))
            if i+j < subdivisions-1:
                triangles.append((lookup[i+1, j], lookup[i+1, j+1], lookup[i, j+1]))
    bary = np.array([(1-(i+j)/subdivisions, i/subdivisions, j/subdivisions) for i, j in lattice])
    return bary, np.array(triangles, dtype=np.int64)


def surface_edge_topology(faces):
    edge_patterns = np.array(((0, 1, 3), (1, 2, 4), (2, 0, 5)))
    edges = faces[:, edge_patterns].reshape(-1, 3).copy()
    edges[:, :2].sort(axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    corners = np.unique(faces[:, :3])
    parent = {int(node): int(node) for node in corners}

    def root(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for a, b, _ in unique:
        left, right = root(int(a)), root(int(b))
        if left != right:
            parent[left] = right
    components = len({root(node) for node in parent})
    return {'unique_quadratic_surface_edges': len(counts),
            'open_surface_edges': int(np.count_nonzero(counts == 1)),
            'nonmanifold_surface_edges': int(np.count_nonzero(counts > 2)),
            'surface_connected_components': components,
            'surface_euler_characteristic': int(len(corners) - len(unique) + len(faces))}


def write_npz(path, **arrays):
    np.savez_compressed(path, **arrays)
    return {'file': path.name, 'bytes': path.stat().st_size,
            'sha256': sha256(path.read_bytes()),
            'arrays': {key: {'shape': list(value.shape), 'dtype': str(value.dtype)}
                       for key, value in arrays.items()}}


def audit(source=SOURCE, output=STAGE / 'geometry-audit', subdivisions=4):
    source, output = Path(source), Path(output)
    raw = source.read_bytes()
    require(len(raw) == SOURCE_BYTES and sha256(raw) == SOURCE_SHA256,
            'Source is not the acquired, pinned Leeds segmented/intact baseline')
    model = parse_input(raw)
    require({s['elset'] for s in model['sections']} == EXPECTED_SECTIONS and len(model['sections']) == 7,
            'Unexpected material-section partition')
    require(set(model['materials']) == {s['material'] for s in model['sections']}, 'Material declaration mismatch')
    output.mkdir(parents=True, exist_ok=True)
    copy = output / source.name
    require(copy.resolve() != source.resolve(), 'Source and staged copy must be separate')
    copy.write_bytes(raw)
    require(copy.read_bytes() == raw, 'Staged native source differs')
    node_ids, points, element_ids, cells = (model[k] for k in ('node_ids', 'points', 'element_ids', 'cells'))
    indexed_cells = np.searchsorted(node_ids, cells)
    matrix = instance_matrix(model['instances'][0]['transform_lines'])
    author_points = transform_points(points, matrix)
    labels = np.full(len(cells), -1, dtype=np.int16)
    sections = model['sections']
    for label, section in enumerate(sections):
        members = np.array(model['sets'][section['elset']], dtype=np.int64)
        require(len(np.unique(members)) == len(members), 'Repeated member in material section')
        require(np.isin(members, element_ids).all(), 'Section references missing element')
        indices = np.searchsorted(element_ids, members)
        require(np.all(labels[indices] == -1), 'Overlapping material sections')
        labels[indices] = label
    require(np.all(labels >= 0), 'Unlabelled volume elements')
    topology = face_topology(cells)
    edges = unique_edges(cells)
    edge_stats, midpoint_deviation, segment_deviation = deviation_stats(points, np.searchsorted(node_ids, edges))
    spring_ids = np.array([s['id'] for s in model['springs']], dtype=np.int64)
    require(len(spring_ids) == len(np.unique(spring_ids)) == 60, 'Unexpected spring connector count')
    endpoint_ids = []
    for spring in model['springs']:
        endpoints = []
        for endpoint in spring['endpoints']:
            instance, native_id = endpoint.rsplit('.', 1)
            require(instance == model['instances'][0]['name'] and int(native_id) in node_ids,
                    'Spring references undefined instance/node')
            endpoints.append(int(native_id))
        endpoint_ids.append(endpoints)
    endpoint_ids = np.array(endpoint_ids, dtype=np.int64)
    bary, local_triangles = preview_grid(subdivisions)
    artifacts = [write_npz(output / 'volume.npz', source_node_ids=node_ids,
                          positions_native=points, positions_author_instance=author_points,
                          source_element_ids=element_ids, c3d10_source_node_ids=cells,
                          c3d10_indices=indexed_cells, element_section_index=labels,
                          global_boundary_quadratic_face_source_node_ids=topology['faces'][topology['boundary_indices']],
                          global_boundary_source_element_ids=element_ids[topology['boundary_indices']//4],
                          global_boundary_abaqus_face_numbers=topology['boundary_indices']%4+1,
                          interior_source_element_pairs=element_ids[topology['interior_pairs']//4],
                          interior_abaqus_face_number_pairs=topology['interior_pairs']%4+1,
                          section_elset_names=np.array([s['elset'] for s in sections]),
                          author_instance_matrix=matrix, quadratic_edge_source_node_ids=edges,
                          edge_midpoint_deviation=midpoint_deviation,
                          edge_distance_to_straight_segment=segment_deviation,
                          spring_element_ids=spring_ids, spring_endpoint_source_node_ids=endpoint_ids,
                          spring_endpoint_positions_author_instance=author_points[np.searchsorted(node_ids, endpoint_ids)],
                          assembly_reference_node_ids=np.array([n[0] for n in model['assembly_nodes']], dtype=np.int64),
                          assembly_reference_positions=np.array([n[1:] for n in model['assembly_nodes']]))]
    parts = []
    for label, section in enumerate(sections):
        mask = labels == label
        local_cells, local_ids = cells[mask], element_ids[mask]
        local_topology = face_topology(local_cells)
        face_indices = local_topology['boundary_indices']
        faces = local_topology['faces'][face_indices].copy()
        owner_indices, side_indices = face_indices // 4, face_indices % 4
        face_points = points[np.searchsorted(node_ids, faces)]
        opposite = points[np.searchsorted(node_ids, local_cells[owner_indices, OPPOSITE_NODES[side_indices]])]
        side = np.einsum('ij,ij->i', np.cross(face_points[:, 1]-face_points[:, 0],
                                           face_points[:, 2]-face_points[:, 0]), opposite-face_points[:, 0])
        require(np.all(side != 0), 'Zero-volume corner tetrahedron on boundary')
        reverse = side > 0
        faces[reverse] = faces[reverse][:, [0, 2, 1, 5, 4, 3]]
        surface_node_ids = np.unique(faces)
        surface_points = points[np.searchsorted(node_ids, surface_node_ids)]
        face_indices_local = np.searchsorted(surface_node_ids, faces)
        face_points = surface_points[face_indices_local]
        preview = np.einsum('vk,fkd->fvd', quadratic_triangle_shape(bary), face_points).reshape(-1, 3)
        preview_indices = (local_triangles[None, :, :] +
                           np.arange(len(faces))[:, None, None]*len(bary)).reshape(-1, 3)
        # Bernstein controls enclose the full curved face; nodal bounds alone need not.
        controls = face_points.copy()
        controls[:, 3:] = 2*face_points[:, 3:] - .5*(face_points[:, :3] + np.roll(face_points[:, :3], -1, axis=1))
        tissue_edges = unique_edges(local_cells)
        tissue_edge_stats, _, _ = deviation_stats(points, np.searchsorted(node_ids, tissue_edges))
        tissue_nodes = np.unique(local_cells)
        all_tissue_points = points[np.searchsorted(node_ids, tissue_nodes)]
        corner_points = points[np.searchsorted(node_ids, local_cells[:, :4])]
        signed_corner_volumes = np.einsum('ij,ij->i', np.cross(corner_points[:, 1]-corner_points[:, 0],
                                                            corner_points[:, 2]-corner_points[:, 0]),
                                         corner_points[:, 3]-corner_points[:, 0]) / 6
        artifact = write_npz(output / (section['elset'] + '.npz'),
                             source_node_ids=surface_node_ids, positions_native=surface_points,
                             positions_author_instance=transform_points(surface_points, matrix),
                             quadratic_faces=face_indices_local, quadratic_face_source_node_ids=faces,
                             boundary_source_element_ids=local_ids[owner_indices],
                             boundary_abaqus_face_numbers=side_indices+1,
                             source_element_ids=local_ids, all_tissue_source_node_ids=tissue_nodes,
                             preview_positions_native=preview,
                             preview_positions_author_instance=transform_points(preview, matrix),
                             preview_triangles=preview_indices,
                             preview_sample_barycentric=bary,
                             preview_triangle_parent_quadratic_face=np.repeat(np.arange(len(faces)), len(local_triangles)))
        artifacts.append(artifact)
        parts.append(section | {'geometry': artifact['file'], 'elements': len(local_cells),
                                'all_tissue_nodes': len(tissue_nodes), 'surface_nodes': len(surface_node_ids),
                                'boundary_quadratic_faces': len(faces),
                                'interior_quadratic_faces': local_topology['interior_faces'],
                                'all_node_bounds_native': bounds(all_tissue_points),
                                'all_node_bounds_author_instance': bounds(transform_points(all_tissue_points, matrix)),
                                'surface_node_bounds_native': bounds(surface_points),
                                'quadratic_surface_bernstein_enclosure_native': bounds(controls.reshape(-1, 3)),
                                'quadratic_surface_bernstein_enclosure_author_instance': bounds(transform_points(controls.reshape(-1, 3), matrix)),
                                'preview_triangles': len(preview_indices), 'preview_samples_per_face': len(bary),
                                'corner_signed_volume_min': float(signed_corner_volumes.min()),
                                'corner_signed_volume_max': float(signed_corner_volumes.max()),
                                'nonpositive_corner_volumes': int(np.count_nonzero(signed_corner_volumes <= 0)),
                                **surface_edge_topology(faces), **tissue_edge_stats})
        print(f"{section['elset']}: {len(local_cells)} C3D10; {len(faces)} six-node boundary faces", flush=True)
    pairs = topology['interior_pairs'] // 4
    interface_pairs = np.sort(labels[pairs], axis=1)
    interface_pairs = interface_pairs[interface_pairs[:, 0] != interface_pairs[:, 1]]
    interface_labels, interface_counts = np.unique(interface_pairs, axis=0, return_counts=True)
    documents = []
    for name in ('README_Cooper-etal_2023.pdf', 'README_Cooper-etal_2023.txt',
                 'method_documentation.pdf', 'method_documentation.txt'):
        path = source.parent.parent / name
        require(path.is_file(), f'Required source documentation missing: {path}')
        document_bytes = path.read_bytes()
        (output / name).write_bytes(document_bytes)
        documents.append({'file': name, 'bytes': len(document_bytes), 'sha256': sha256(document_bytes)})
    report = {
        'schema': 'primer.leeds-knee-geometry-audit.v1',
        'status': 'source geometry audit only; independent anatomical review pending',
        'clinical_approval': False, 'commercial_readiness_demonstrated': False,
        'source': {'file': source.name, 'bytes': len(raw), 'sha256': sha256(raw),
                   'staged_native_bytes_identical': True, 'doi': '10.5518/981',
                   'license': 'CC BY 4.0', 'license_evidence': 'README_Cooper-etal_2023.pdf, page 2',
                   'attribution': 'Cooper RJ, Day GA, Wijayathunga VN, Yao J, Mengoni M, Wilcox RK, Jones AC (2023), Three subject-specific human tibiofemoral joint finite element models: complete three-dimensional imaging (CT & MR), experimental validation and modelling dataset. University of Leeds. doi:10.5518/981.'},
        'source_context': [
            'LTKN8941 is Knee 2; seg denotes directly segmented nonuniform cartilage, intact denotes included menisci, fix denotes constrained tibia (README page 3).',
            'Bone and cartilage geometry came from post-test CT; menisci from registered pre-dissection MR (methods page 5). This audit has not recovered or validated that registration.',
            'Meniscus segmentations underwent contact-conformity adjustments for solver convergence, including dilation, binary operations and curvature adjustments (methods page 5).',
            'Uniform-thickness cartilage variants exist, but this selected seg_intact input is not one of them. Subject-derived geometry does not establish normal anatomy.',
            'Only the seven explicitly labelled solid groups are represented. SpringA attachments represent meniscal-root mechanics, not volumetric root fibres (methods page 6).'],
        'coordinates': {'native': 'Native PART-1 Cartesian coordinates, preserved without anatomical relabelling.',
                        'author_instance': 'Author assembly placement only, before analysis/loading displacements.',
                        'anatomical_axis_identity': 'unverified', 'mri_registration': 'not established by this audit',
                        'units': 'Native deck has no units declaration; source methods use mm/MPa. No unit conversion applied.',
                        'instance': model['instances'][0], 'operation_order': 'translation then rotation',
                        'column_vector_matrix': matrix.tolist(), 'reference': INSTANCE_URL,
                        'all_node_bounds_native': bounds(points), 'all_node_bounds_author_instance': bounds(author_points)},
        'volume': {'part': model['part'], 'element_type': 'C3D10', 'nodes': len(node_ids), 'elements': len(cells),
                   'unused_part_nodes': int(len(node_ids)-len(np.unique(cells))),
                   'exact_section_partition': True, 'unlabelled_elements': 0, 'overlapping_section_elements': 0,
                   'unique_faces': topology['unique_faces'], 'boundary_faces': topology['boundary_faces'],
                   'interior_faces': topology['interior_faces'], 'midside_face_mismatches': 0,
                   'nonmanifold_volume_faces': 0, **edge_stats},
        'shared_material_interfaces': [{'sections': [sections[i]['elset'] for i in pair], 'quadratic_faces': int(count)}
                                       for pair, count in zip(interface_labels, interface_counts)],
        'assembly_reference_nodes': [{'id': int(row[0]), 'position_author_assembly': list(row[1:])} for row in model['assembly_nodes']],
        'spring_connectors': {'count': len(spring_ids), 'geometry_kind': 'two-node mechanical connectors, not anatomical fibre volumes',
                              'groups': dict(Counter(s['elset'] for s in model['springs'])),
                              'settings': model['spring_settings'], 'elements': model['springs']},
        'surface_representation': {'primary': 'Six-node quadratic triangular faces with native midside coordinates',
                                   'face_node_order': ['a', 'b', 'c', 'ab', 'bc', 'ca'],
                                   'winding': 'PT_*.npz boundary faces are oriented outward relative to the opposite corner. volume.npz global boundary faces preserve native Abaqus S1..S4 ordering without outward reorientation. Neither convention is a full curved-Jacobian validity proof.',
                                   'preview': f'Quadratic interpolation on an even {subdivisions}-division barycentric grid; {subdivisions**2} planar triangles per face; no decimation or smoothing',
                                   'preview_error_bound': 'not established; use quadratic arrays for quantitative review',
                                   'geometry_vs_displacement_interpolation': 'Quadratic C3D10 order supports quadratic interpolation but does not imply added anatomical detail. In this undeformed source the maximum midside-to-edge-midpoint offset is about 1.04e-5 native units; its geometry is consequently almost straight-sided at that scale. All native midside nodes are nevertheless preserved.',
                                   'bounds': 'Nodal extrema are labelled as such. Bernstein control bounds conservatively enclose continuous curved boundary faces, not necessarily tightly.',
                                   'topology_limits': 'Edge-incidence and quadratic face-adjacency checks are not a proof of vertex manifoldness, absence of self-intersections, positive curved-element Jacobians, or anatomical validity.',
                                   'interpolation_reference': INTERPOLATION_URL},
        'sections': parts, 'artifacts': artifacts, 'source_documents': documents,
        'input_keyword_counts': dict(Counter(b['keyword'] for b in model['inventory'])),
        'input_keyword_inventory': model['inventory'],
        'scope_limits': ['No FE solve, loaded state reconstruction, remeshing, smoothing, synthesis or runtime publication.',
                         'No recovered segmentation labels for structures absent from these seven FE groups.',
                         'No diagnostic completeness, expert approval, normality or commercial-readiness claim.'],
    }
    (output / 'geometry-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'README.md').write_text(
        '# Leeds 981 geometry audit staging\n\nResearch inspection only; anatomical review and MRI registration remain pending.\n\n'
        'The native INP and source documents are byte copies. See geometry-audit.json for hashes, provenance, section membership and limitations.\n\n'
        '`volume.npz` preserves all native node IDs, coordinates, ten-node cells, material indices, author placement matrix and mechanical spring endpoints. '
        'The seven PT_*.npz files retain six-node boundary faces, source element IDs and Abaqus face numbers. '
        'PT_* boundary faces are oriented outward relative to the opposite corner; volume.npz global boundaries retain native Abaqus face order, without outward reorientation. '
        '`quadratic_faces` indexes `positions_native` / `positions_author_instance`; columns are a,b,c,ab,bc,ca. '
        'All array indices are zero-based; `source_*` labels and Abaqus face numbers retain native numbering.\n\n'
        '`preview_*` arrays are explicitly approximate piecewise-planar samples of the quadratic map. '
        'Their vertices are duplicated by face; assess topology on the quadratic faces, not on preview vertex indices. '
        'No corners-only mesh is provided. Preview error has not been bounded. '
        'Author-instance coordinates reproduce the input transform; they are not MRI coordinates or a certified anatomical frame.\n')
    require(source.read_bytes() == raw, 'Native source changed during audit')
    print(output / 'geometry-audit.json', flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=STAGE / 'geometry-audit')
    parser.add_argument('--preview-subdivisions', type=int, default=4)
    args = parser.parse_args()
    audit(args.source, args.output, args.preview_subdivisions)


if __name__ == '__main__':
    main()
