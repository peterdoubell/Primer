#!/usr/bin/env python3
"""Render every original bowel source triangle, preserving original coordinates and parts."""
import argparse
import hashlib
import json
from pathlib import Path


def render(root, output, single_panel_bottom=.18, sparse_short_axes=False):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    report_path = output / 'original-obj-geometry-review.json'
    report = json.loads(report_path.read_text())
    parts = []
    for r in report['records']:
        raw = (root / 'objects' / (r['id'] + '.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != r['source_sha256']:
            raise ValueError('Original source changed')
        v, n, f, nf = read_obj(raw.decode())
        if hashlib.sha256(v.astype('<f8').tobytes()).hexdigest() != r['positions_float64_le_sha256']:
            raise ValueError('Original source coordinates differ')
        if hashlib.sha256(f.astype('<i8').tobytes()).hexdigest() != r['face_indices_int64_le_sha256']:
            raise ValueError('Original source triangles differ')
        parts.append((r, v, f))
    figures = []
    groups = report['source_groups']
    for group in groups:
        selected = [p for p in parts if p[0]['id'] in group['element_ids']]
        for azimuth in [35, 215]:
            columns=min(3,len(selected)); rows=(len(selected)+columns-1)//columns
            fig = plt.figure(figsize=(14 if columns>=2 else 8, max(5,4.6*rows)))
            panels = []
            for slot, (r, v, f) in enumerate(selected, 1):
                ax = fig.add_subplot(rows, columns, slot, projection='3d')
                triangles = v[f]
                normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
                lengths = np.linalg.norm(normals, axis=1)
                unit = np.divide(normals, lengths[:, None], out=np.zeros_like(normals), where=lengths[:, None] > 0)
                light = np.array([1, -1, 2], float); light /= np.linalg.norm(light)
                tone = [.36, .64, .54, 1] if 'colon' in r['source_label'].lower() else [.7, .35, .3, 1] if 'artery' in r['source_label'].lower() else [.3, .48, .7, 1]
                colors = np.tile(tone, (len(f), 1)); colors[:, :3] *= (.6 + .4 * np.maximum(unit @ light, 0))[:, None]
                ax.add_collection3d(Poly3DCollection(triangles, facecolors=colors, edgecolor='none', linewidths=0))
                lo, hi = v.min(0), v.max(0); extent = np.maximum(hi - lo, .1); pad = extent * .05
                ax.set_xlim(lo[0] - pad[0], hi[0] + pad[0]); ax.set_ylim(lo[1] - pad[1], hi[1] + pad[1]); ax.set_zlim(lo[2] - pad[2], hi[2] + pad[2]); ax.set_box_aspect(extent)
                ax.view_init(elev=20, azim=azimuth); ax.locator_params(nbins=3); ax.tick_params(labelsize=6)
                ax.set_xlabel('Source X mm', fontsize=8); ax.set_ylabel('Source Y mm', fontsize=8); ax.set_zlabel('Source Z mm', fontsize=8)
                if sparse_short_axes:
                    for axis,short in enumerate(extent.max()/extent>8):
                        if short:[ax.set_xticks,ax.set_yticks,ax.set_zticks][axis]([])
                    ax.set_xlabel('\nSource X mm',fontsize=8)
                    ax.set_zlabel('Source Z mm',fontsize=8,labelpad=30)
                count = len(r['exact_position_analysis_topology']['components'])
                ax.set_title(r['id']+f' | {len(f)} original triangles\n{count} components',fontsize=9)
                panels.append({'element_id': r['id'], 'original_triangle_count': len(f), 'exact_position_components': count,
                    'source_bounds_mm': [lo.tolist(), hi.tolist()], 'source_positions_or_faces_changed': False})
            fig.suptitle(group['source_target_label']+' | version-manifest 4.3\nEvery original triangle; panel scales differ; no repair, fusion, registration or clinical approval', fontsize=11)
            fig.subplots_adjust(left=.05, right=.95, bottom=single_panel_bottom if rows==1 else .14, top=.73 if rows==1 else .85, hspace=.38, wspace=.18)
            fig.text(.5, .015, 'BodyParts3D © 2008 DBCLS | CC BY-SA 2.1 Japan | adaptation: review lighting and original-source views', ha='center', fontsize=9)
            file = output / (group['source_fma']+'-original-source-azimuth' + str(azimuth) + '.png')
            fig.savefig(file, dpi=110); plt.close(fig)
            figures.append({'file': file.name, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(), 'source_group':group['source_fma'], 'azimuth_degrees': azimuth, 'panels': panels})
    (output / 'source-figure-review.json').write_text(json.dumps({'source_geometry_review_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(),
        'figures': figures, 'source_meshes_merged_repaired_or_deduplicated': False, 'clinical_approval': False,
        'runtime_promoted': False, 'derived_figure_license': 'CC BY-SA 2.1 Japan'}, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); render(args.source_root, args.output)
