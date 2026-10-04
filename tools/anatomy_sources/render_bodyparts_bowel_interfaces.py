#!/usr/bin/env python3
"""Locate every original source contact without making a validated biological bowel tree."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path


def render(root, output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    inventory = json.loads((output / 'original-obj-geometry-review.json').read_text()); meshes = {}
    for r in inventory['records']:
        raw = (root / 'objects' / (r['id'] + '.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != r['source_sha256']:
            raise ValueError('Original source changed')
        v, n, f, nf = read_obj(raw.decode()); meshes[r['id']] = v[f]
    summary = json.loads((output / 'complete-source-pair-summary.json').read_text())
    payload = gzip.decompress((output / summary['file']).read_bytes())
    if hashlib.sha256(payload).hexdigest() != summary['uncompressed_sha256']:
        raise ValueError('Complete source contact evidence differs')
    evidence = json.loads(payload); contacts = evidence['triangle_contact_audit']['unexpected_contacts']
    groups = [('all_source_contacts', contacts),
              ('same_source_label_contacts', [r for r in contacts if r['same_source_fma_group']]),
              ('different_source_label_contacts', [r for r in contacts if not r['same_source_fma_group']])]
    all_triangles = np.concatenate(list(meshes.values())); fig, axes = plt.subplots(3, 3, figsize=(14, 12), layout='constrained')
    fig.get_layout_engine().set(rect=(0, .045, 1, .945)); panels = []
    for row, (name, subset) in enumerate(groups):
        points = np.asarray([p for r in subset for p in r['contact_points_mm']]); affected = defaultdict(set)
        for contact in subset:
            for face in contact['original_source_faces']:
                affected[face['source_part']].add(face['source_face_index'])
        selected = np.concatenate([meshes[i][sorted(indices)] for i, indices in affected.items()])
        for col, (a, b) in enumerate([(0, 1), (0, 2), (1, 2)]):
            ax = axes[row, col]
            ax.add_collection(PolyCollection(all_triangles[:, :, [a, b]], facecolor='#b4a780', edgecolor='none', alpha=.025))
            ax.add_collection(PolyCollection(selected[:, :, [a, b]], facecolor='#bd467e', edgecolor='none', alpha=.35))
            ax.scatter(points[:, a], points[:, b], s=2, color='#176c97', zorder=4); ax.autoscale_view(); ax.set_aspect('equal')
            ax.set_xlabel('Source ' + ['X', 'Y', 'Z'][a] + ' mm'); ax.set_ylabel('Source ' + ['X', 'Y', 'Z'][b] + ' mm')
            ax.set_title(name.replace('_', ' ') + ' | ' + str(len(subset)) + ' pairs', fontsize=10); ax.tick_params(labelsize=8)
        panels.append({'category': name, 'contact_pairs': len(subset), 'contact_points_displayed': len(points),
            'original_affected_faces': [{'element_id': i, 'face_indices': sorted(indices)} for i, indices in sorted(affected.items())],
            'all_original_context_triangles': len(all_triangles), 'source_positions_or_faces_changed': False})
    fig.suptitle('Bowel source-piece contacts | analytical comparisons, not a validated biological tree\nGold: every original source triangle; magenta: affected source faces; blue: numerical contact points\nRegional pieces remain separate; no repair, fitting or anatomical junction approval', fontsize=11)
    fig.text(.5, .006, 'BodyParts3D © 2008 DBCLS | CC BY-SA 2.1 Japan | adaptation: source contact projections and review colours', ha='center', fontsize=8)
    path = output / 'source-pair-contact-locations.png'; fig.savefig(path, dpi=120); plt.close(fig)
    (output / 'source-pair-location-review.json').write_text(json.dumps({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'complete_contact_evidence_uncompressed_sha256': summary['uncompressed_sha256'], 'panels': panels,
        'source_coordinate_units': 'millimetres', 'derived_figure_license': 'CC BY-SA 2.1 Japan', 'source_geometry_changed': False,
        'biological_tree_assembled_or_approved': False, 'clinical_approval': False, 'runtime_promoted': False}, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); render(args.source_root, args.output)
