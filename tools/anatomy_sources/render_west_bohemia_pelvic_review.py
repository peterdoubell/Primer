#!/usr/bin/env python3
"""Render every original template face for offline review; no clinical axis or colour claim."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def render(source, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.colors import LightSource
    import numpy as np
    review_raw = (source / 'review.json').read_bytes()
    review = json.loads(review_raw)
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for model in review['models']:
        raw = gzip.decompress((source / model['retained_file']).read_bytes())
        if hashlib.sha256(raw).hexdigest() != model['source_JSON_sha256']:
            raise ValueError('Retained original source changed')
        data = json.loads(raw)
        if list(data) != [o['source_label'] for o in model['objects']]:
            raise ValueError('Original part order differs')
        prefix = 'advanced' if model['object_count'] == 43 else 'basic'
        for index, (label, (points, cells)) in enumerate(data.items()):
            vertices = np.asarray(points, dtype=np.float64)
            faces = np.asarray(cells, dtype=np.int64).reshape(-1, 4)[:, 1:]
            center = (vertices.min(0) + vertices.max(0)) / 2
            radius = max((vertices.max(0) - vertices.min(0)).max() / 2, 1e-10)
            fig = plt.figure(figsize=(12, 4), dpi=150)
            for slot, (elev, azim) in enumerate([(15, -90), (15, 0), (75, -90)], start=1):
                ax = fig.add_subplot(1, 3, slot, projection='3d')
                # Only the camera/plot limits change. Every original source face
                # is present, including duplicates and nonmanifold interfaces.
                mesh = Poly3DCollection(vertices[faces], facecolors='#6599b8',
                                        shade=True, lightsource=LightSource(azdeg=225, altdeg=45))
                mesh.set_edgecolor('none')
                ax.add_collection3d(mesh)
                for dim, setter in enumerate([ax.set_xlim, ax.set_ylim, ax.set_zlim]):
                    setter(center[dim] - radius * 1.05, center[dim] + radius * 1.05)
                ax.set_box_aspect((1, 1, 1))
                ax.view_init(elev=elev, azim=azim)
                ax.set_axis_off()
                ax.set_title(f'Review camera {slot}; source frame', fontsize=9)
            fig.suptitle(f'{prefix}: {label} — all {len(faces):,} source triangles', fontsize=11)
            fig.text(.5, .015, 'Review colour and camera only; no clinical axes, biological colour or anatomical approval.',
                     ha='center', fontsize=8)
            fig.subplots_adjust(left=0, right=1, bottom=.04, top=.84, wspace=0)
            file = f'{prefix}-{index:02d}.png'
            fig.savefig(output / file)
            plt.close(fig)
            records.append({'source_model': model['source_filename'], 'source_label': label,
                            'file': file, 'sha256': hashlib.sha256((output / file).read_bytes()).hexdigest(),
                            'original_triangles_per_camera': len(faces), 'source_faces_removed_or_repaired': False,
                            'anatomical_review_complete': False})
            print(prefix, index, label, flush=True)
    proof = {'source_review_sha256': hashlib.sha256(review_raw).hexdigest(), 'rendered_objects': records,
             'original_faces_retained_in_every_camera': True, 'clinical_axes_or_biological_colours_claimed': False,
             'lighting': 'Review facet shading from original source triangles; not encoded source normals or biological optical properties.',
             'source_geometry_changed': False, 'clinical_approval': False, 'runtime_promoted': False}
    (output / 'render-review.json').write_text(json.dumps(proof, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    render(args.source, args.output)
