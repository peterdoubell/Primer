#!/usr/bin/env python3
"""Preserve all source-pair vertex proximity without claiming continuous gaps or junctions."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path


def review(root, output):
    import numpy as np
    from scipy.spatial import cKDTree
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    path = output / 'original-obj-geometry-review.json'; report = json.loads(path.read_text()); meshes = {}
    for r in report['records']:
        raw = (root / 'objects' / (r['id'] + '.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != r['source_sha256']:
            raise ValueError('Original source changed')
        v, n, f, nf = read_obj(raw.decode())
        if np.unique(f).size != len(v):
            raise ValueError('Nearest-vertex surface bound requires referenced source positions; review unused vertices separately')
        meshes[r['id']] = {'vertices': v, 'tree': cKDTree(v), 'positions': {tuple(x) for x in v},
                          'group': r['source_fma'], 'sha256': r['source_sha256']}
    rows = []
    for a, b in itertools.combinations(sorted(meshes), 2):
        av, bv = meshes[a]['vertices'], meshes[b]['vertices']; distance, indices = meshes[b]['tree'].query(av)
        i = int(np.argmin(distance)); j = int(indices[i])
        rows.append({'source_ids': [a, b], 'same_source_fma_group': meshes[a]['group'] == meshes[b]['group'],
            'source_sha256': [meshes[a]['sha256'], meshes[b]['sha256']], 'minimum_vertex_pair_distance_mm': float(distance[i]),
            'closest_source_vertex_indices': [i, j], 'closest_source_positions_mm': [av[i].tolist(), bv[j].tolist()],
            'exact_shared_position_count': len(meshes[a]['positions'] & meshes[b]['positions']),
            'vertex_distance_is_continuous_surface_distance': False, 'gap_or_biological_junction_verified': False,
            'source_geometry_changed': False})
    (output / 'all-source-pair-proximity-review.json').write_text(json.dumps({'source_geometry_review_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_coordinate_units': 'millimetres', 'pairs': rows, 'source_objects_fused_or_fitted': False,
        'clinical_approval': False, 'runtime_promoted': False,
        'limits': ['Nearest source vertices provide only an upper bound for the minimum continuous surface distance. Positive vertex distance cannot prove a surface gap.',
            'Exact shared positions and source contacts do not prove an anatomically correct or patent duct junction.',
            'All same-label representations are retained and compared as source candidates, not simultaneous independently approved anatomy.']}, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); review(args.source_root, args.output)
