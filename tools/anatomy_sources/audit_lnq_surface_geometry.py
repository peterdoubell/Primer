#!/usr/bin/env python3
"""Audit every LNQ source-surface vertex and triangle contact without repairs."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def topology(vertices, faces):
    import numpy as np
    if (vertices.ndim != 2 or vertices.shape[1] != 3 or faces.ndim != 2 or faces.shape[1] != 3
            or not np.issubdtype(faces.dtype, np.integer) or len(faces) == 0
            or faces.min() < 0 or faces.max() >= len(vertices) or not np.isfinite(vertices).all()):
        raise ValueError('Invalid mesh arrays')
    directed = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    undirected = np.sort(directed, axis=1)
    edges, inverse, counts = np.unique(undirected, axis=0, return_inverse=True, return_counts=True)
    signs = np.where(directed[:, 0] < directed[:, 1], 1, -1)
    orientation_sum = np.bincount(inverse, weights=signs, minlength=len(edges))
    triangles = vertices[faces]
    areas = np.linalg.norm(np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]), axis=1) / 2
    links = defaultdict(list)
    adjacency = defaultdict(set)
    for a, b, c in faces:
        a, b, c = map(int, (a, b, c))
        links[a].append((b, c)); links[b].append((c, a)); links[c].append((a, b))
        adjacency[a].update((b, c)); adjacency[b].update((a, c)); adjacency[c].update((a, b))
    defects = []
    for vertex, link_edges in links.items():
        link = defaultdict(list)
        for a, b in link_edges:
            link[a].append(b); link[b].append(a)
        remaining = set(link); components = 0
        while remaining:
            components += 1; frontier = [remaining.pop()]
            while frontier:
                for other in link[frontier.pop()]:
                    if other in remaining:
                        remaining.remove(other); frontier.append(other)
        noncycle = sum(len(x) != 2 for x in link.values())
        if components != 1 or noncycle:
            defects.append({'vertex': vertex, 'link_components': components, 'noncycle_link_nodes': noncycle})
    remaining = set(adjacency); component_rows = []
    while remaining:
        selected = {remaining.pop()}; frontier = list(selected)
        while frontier:
            for other in adjacency[frontier.pop()]:
                if other in remaining:
                    remaining.remove(other); selected.add(other); frontier.append(other)
        selected = np.asarray(sorted(selected), dtype=int)
        selected_faces = np.all(np.isin(faces, selected), axis=1)
        selected_edges = np.all(np.isin(edges, selected), axis=1)
        tri = triangles[selected_faces]
        volume = float(np.einsum('ij,ij->i', tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6)
        component_rows.append({'mesh_component': len(component_rows) + 1, 'vertices': len(selected),
            'triangles': int(selected_faces.sum()), 'edges': int(selected_edges.sum()),
            'euler_characteristic': int(len(selected) - selected_edges.sum() + selected_faces.sum()),
            'signed_volume_mm3': volume, 'world_bounds_ras_mm': [vertices[selected].min(0).tolist(), vertices[selected].max(0).tolist()],
            'independent_node_identity_verified': False, 'station_identity_verified': False})
    return {'vertices_checked': len(links), 'unused_vertices': len(vertices) - len(links),
        'boundary_edges': int((counts == 1).sum()), 'nonmanifold_edges': int((counts > 2).sum()),
        'inconsistent_closed_edge_orientation': int(((counts == 2) & (orientation_sum != 0)).sum()),
        'zero_area_triangles': int((areas <= 0).sum()), 'nonmanifold_vertex_count': len(defects),
        'vertex_defects': defects, 'mesh_components': component_rows,
        'exact_duplicate_vertex_positions': len(vertices) - len(np.unique(vertices, axis=0)),
        'topology_is_anatomical_accuracy': False}


def audit(mesh_root, output):
    import numpy as np
    from tools.anatomy_sources.audit_massp_surface_intersections import inspect
    manifest_path = mesh_root / 'surface-review.json'
    manifest = json.loads(manifest_path.read_text())
    path = mesh_root / manifest['mesh_file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['mesh_sha256']:
        raise ValueError('Source surface changed')
    with np.load(path) as data:
        vertices, faces = data['vertices'].copy(), data['faces'].copy()
    topo = topology(vertices, faces)
    contacts = inspect(vertices, faces)
    for component in topo['mesh_components']:
        chi = component['euler_characteristic']
        manifold = all(topo[k] == 0 for k in ('boundary_edges', 'nonmanifold_edges',
            'inconsistent_closed_edge_orientation', 'nonmanifold_vertex_count'))
        component['orientable_closed_surface_genus'] = (2 - chi) // 2 if manifold and chi <= 2 and chi % 2 == 0 else None
        component['surface_handle_anatomical_cause_verified'] = False
    handles_unclassified = any((c['orientable_closed_surface_genus'] or 0) > 0 for c in topo['mesh_components'])
    result = {'case_id': manifest['case_id'], 'source_doi': manifest['source_doi'],
        'source_surface_sha256': manifest['mesh_sha256'], 'source_surface_review_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'topology': topo, 'continuous_contacts': contacts, 'source_geometry_changed': False,
        'status': 'held_unclassified_source_surface_handles' if handles_unclassified else 'offline_candidate_requires_anatomical_review',
        'clinical_approval': False, 'runtime_promoted': False,
        'limitations': ['Vertex links and numerical contacts test the exported surface, not original anatomical boundaries.',
                       'Separate mesh components do not establish individual nodes or station count.',
                       'All candidate triangle pairs include interactions between disconnected source components.',
                       'Native sampling, annotation extent, pathology and station identity remain unverified.']}
    output.write_text(json.dumps(result, indent=2) + '\n')
    print('Vertex defects', topo['nonmanifold_vertex_count'], '; unexpected contacts', contacts['unexpected_contact_count'],
          '; candidate triangle pairs', contacts['conservative_aabb_candidate_pairs'], flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mesh-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); audit(a.mesh_root, a.output)
