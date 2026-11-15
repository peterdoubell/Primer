#!/usr/bin/env python3
"""Retain every exact-position source boundary edge without cap filling or endpoint inference."""
import argparse
import hashlib
import json
from pathlib import Path


def boundaries(vertices, faces):
    import numpy as np
    unique, inverse = np.unique(vertices, axis=0, return_inverse=True)
    occurrences = {}
    for face_index, original in enumerate(faces):
        mapped = inverse[original]
        for a, b in [(0, 1), (1, 2), (2, 0)]:
            edge = tuple(sorted([int(mapped[a]), int(mapped[b])]))
            occurrences.setdefault(edge, []).append((face_index, [int(original[a]), int(original[b])]))
    selected = []
    adjacency = {}
    for edge, owners in sorted(occurrences.items()):
        if len(owners) != 1:
            continue
        face, original = owners[0]
        selected.append({'exact_position_vertex_ids': list(edge), 'original_face_index': face,
                         'original_vertex_indices': original, 'original_positions_mm': vertices[original].tolist()})
        for a, b in [edge, edge[::-1]]:
            adjacency.setdefault(a, set()).add(b)
    remaining = set(adjacency)
    components = []
    while remaining:
        first = min(remaining); remaining.remove(first); members = {first}; pending = [first]
        while pending:
            for other in adjacency[pending.pop()]:
                if other in remaining:
                    remaining.remove(other); members.add(other); pending.append(other)
        ids = sorted(members); points = unique[ids]
        edge_count = sum(len(adjacency[i]) for i in ids) // 2
        components.append({'exact_position_vertex_ids': ids, 'edge_count': edge_count,
                           'all_vertices_degree_two': all(len(adjacency[i]) == 2 for i in ids),
                           'original_positions_mm': points.tolist(),
                           'original_vertex_record_groups': [np.flatnonzero(inverse == i).tolist() for i in ids],
                           'bounds_original_mm': [points.min(0).tolist(), points.max(0).tolist()]})
    return {'boundary_edges': selected, 'boundary_graph_components': components,
            'source_positions_or_faces_changed': False, 'caps_added': False,
            'anatomical_open_ends_or_defects_classified': False}


def review(root, output):
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    path = output / 'original-obj-geometry-review.json'; payload = path.read_bytes()
    inventory = json.loads(payload); rows = []
    for row in inventory['records']:
        raw = (root / 'objects' / (row['id'] + '.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row['source_sha256']:
            raise ValueError('Original source changed')
        vertices, normals, faces, normal_faces = read_obj(raw.decode())
        result = boundaries(vertices, faces)
        if len(result['boundary_edges']) != row['exact_position_analysis_topology']['boundary_edges']:
            raise ValueError('Complete exact-position source boundary count differs')
        rows.append({'element_id': row['id'], 'source_label': row['source_label'],
                     'source_sha256': row['source_sha256'], **result})
    (output / 'complete-source-boundary-review.json').write_text(json.dumps({
        'source_geometry_review_sha256': hashlib.sha256(payload).hexdigest(), 'records': rows,
        'source_coordinate_units': 'millimetres', 'clinical_approval': False, 'runtime_promoted': False,
        'limits': ['Exact-position graph cycles are numerical boundary facts, not independently classified anatomical vessel ends or defects.',
                   'No cap, weld, branch, lumen, vessel-wall layer or patent connection is inferred or added.']}, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); review(args.source_root, args.output)
