#!/usr/bin/env python3
"""Display every source rater triangle in original physical space for offline review."""
import argparse
import hashlib
import json
from pathlib import Path


def render(mesh_root, report_path, output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    report = json.loads(report_path.read_text()); meshes = []
    for row in report['records']:
        if not row['mesh_created']: raise ValueError('Held extraction has no display surface')
        path = mesh_root / row['mesh_file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['mesh_sha256']: raise ValueError('Source mesh changed')
        with np.load(path) as data: meshes.append((row, data['vertices'].copy(), data['faces'].copy()))
    low = np.min([v.min(0) for _, v, _ in meshes], axis=0); high = np.max([v.max(0) for _, v, _ in meshes], axis=0)
    span = high - low; centre = (high + low) / 2; bounds = [(c-s/2-5, c+s/2+5) for c, s in zip(centre, span)]
    output.mkdir(parents=True, exist_ok=True); figures = []
    for name, azimuth in [('ras-view-azimuth-minus65', -65), ('ras-view-azimuth-plus115', 115)]:
        fig = plt.figure(figsize=(14, 11))
        for index, (row, vertices, faces) in enumerate(meshes, 1):
            ax = fig.add_subplot(2, 2, index, projection='3d')
            collection = Poly3DCollection(vertices[faces], facecolors='#b37b57' if 'liver' in row['source_file'] else '#64a3c0',
                                          linewidths=0, alpha=1, shade=True, lightsource=matplotlib.colors.LightSource(315, 45))
            ax.add_collection3d(collection); ax.set_xlim(*bounds[0]); ax.set_ylim(*bounds[1]); ax.set_zlim(*bounds[2])
            ax.set_box_aspect(span+10); ax.view_init(elev=20, azim=azimuth)
            ax.set_xlabel('RAS X mm', fontsize=8); ax.set_ylabel('RAS Y mm', fontsize=8); ax.set_zlabel('RAS Z mm', fontsize=8)
            ax.tick_params(labelsize=7)
            handles = [c['orientable_closed_surface_genus'] for c in row['topology']['mesh_components']]
            ax.set_title(row['source_file'].replace('.nii.gz', '') + f" | {len(faces):,} triangles\nSource surface genera {handles}; cause unverified", fontsize=10)
        fig.suptitle('TCGA-BC-A3KG | separate independent liver/tumour rater surfaces\n'
                     'All triangles retained at a common physical scale; no smoothing, averaged boundary or clinical approval', fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, .93)); path = output / (name+'.png'); fig.savefig(path, dpi=130); plt.close(fig)
        figures.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'all_source_faces_rendered': True, 'azimuth_degrees': azimuth, 'elevation_degrees': 20})
    (output/'surface-figure-review.json').write_text(json.dumps({'source_surface_review_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(),
        'source_mesh_sha256': [row['mesh_sha256'] for row, _, _ in meshes], 'figures': figures,
        'common_world_axis_limits_ras_mm': bounds, 'source_vertices_changed': False, 'source_faces_decimated': False,
        'clinical_approval': False, 'runtime_promoted': False, 'limits': ['Static views do not prove every surface point or reporting structure.',
        'Separate source raters remain separate candidates; handles and tumour/liver label differences need original MRI review.']}, indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mesh-root',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();render(a.mesh_root,a.report,a.output)
