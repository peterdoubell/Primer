#!/usr/bin/env python3
"""Compare all same-label vessel representations without treating overlapping requested groups as anatomical identity."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path


def review(root, output):
    import numpy as np
    from scipy.spatial import cKDTree
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    path = output / 'original-obj-geometry-review.json'; report = json.loads(path.read_text()); objects = {}
    for r in report['records']:
        raw = (root / 'objects' / (r['id'] + '.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != r['source_sha256']:
            raise ValueError('Original source changed')
        v, n, f, nf = read_obj(raw.decode())
        objects[r['id']] = (v, n, f, nf)
    pairs = []
    groups = {}
    for row in report['records']:
        groups.setdefault(row['source_fma'], {'source_fma': row['source_fma'], 'source_target_label': row['source_label'], 'element_ids': []})['element_ids'].append(row['id'])
    for group in groups.values():
        for a, b in itertools.combinations(sorted(group['element_ids']), 2):
            av, an, af, anf = objects[a]; bv, bn, bf, bnf = objects[b]
            same_faces = np.array_equal(af, bf); same_shape = av.shape == bv.shape
            pairs.append({'source_fma': group['source_fma'], 'source_target_label': group['source_target_label'],
                'source_ids': [a, b], 'position_records_exactly_equal': bool(np.array_equal(av, bv)),
                'face_indices_exactly_equal': bool(same_faces), 'normal_records_exactly_equal': bool(np.array_equal(an, bn)),
                'normal_indices_exactly_equal': bool(np.array_equal(anf, bnf)),
                'ordered_triangle_positions_exactly_equal': bool(np.array_equal(av[af], bv[bf])),
                'maximum_first_vertex_to_second_vertex_distance_mm': float(cKDTree(bv).query(av)[0].max()),
                'maximum_second_vertex_to_first_vertex_distance_mm': float(cKDTree(av).query(bv)[0].max()),
                'nearest_vertex_distances_are_continuous_surface_bounds': False,
                'same_index_continuous_triangle_displacement_upper_bound_mm': float(np.linalg.norm(av-bv, axis=1).max()) if same_faces and same_shape else None,
                'source_geometry_changed': False, 'biological_identity_or_independent_branch_verified': False})
    (output / 'source-geometry-correspondence.json').write_text(json.dumps({'source_geometry_review_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'comparisons': pairs, 'repeated_objects_deduplicated_fitted_or_fused': False, 'clinical_approval': False,
        'runtime_promoted': False, 'limits': ['Repeated labels/positions do not establish independent branches or anatomical identity.',
            'Same-index triangle displacement bounds use existing vertex/face correspondence without registration; they are not biological accuracy estimates.',
            'Original labels and every source geometry remain separate; missing wall layers, lumina and patient-specific variants remain unverified.']}, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); review(args.source_root, args.output)
