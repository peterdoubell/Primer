#!/usr/bin/env python3
"""Render the staged FDA assembly for source review; no anatomical certification."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

STAGE = Path('/tmp/primer-msk-sources/shoulder-next/fda-shoulder')
COLORS = {'Labrum': '#9b6aad', 'Gcart': '#43aeb6', 'Hcart': '#e1ad45',
          'AC_Lig': '#c25c4f', 'Humerus': '#d6cbbb', 'SCAPULA': '#c7bba8', 'CLAVICLE': '#bdae97'}


def main():
    report = json.loads((STAGE / 'mesh-inspection.json').read_text())
    parts = {}
    for part in report['parts']:
        geometry = np.load(STAGE / part['geometry'])
        parts[part['source_part']] = (geometry['positions_world'], geometry['indices'])
    views = [
        ('Native assembly · source instance transforms', list(parts), None, (-55, 15)),
        ('Glenohumeral region · display crop', ['SCAPULA', 'Humerus', 'Gcart', 'Hcart', 'Labrum'],
         np.array([[40, 235, 915], [110, 315, 980]]), (-65, 12)),
        ('Isolated labrum + glenoid cartilage', ['Gcart', 'Labrum'], None, (-170, 10)),
        ('AC ligament in bone context · display crop', ['SCAPULA', 'CLAVICLE', 'AC_Lig'],
         np.array([[65, 235, 965], [115, 300, 1002]]), (-80, 35)),
    ]
    fig = plt.figure(figsize=(15, 12), facecolor='#f6f3ef')
    for index, (title, names, clip, (azimuth, elevation)) in enumerate(views):
        ax = fig.add_subplot(2, 2, index + 1, projection='3d', facecolor='#f6f3ef')
        extent = []
        for name in names:
            positions, faces = parts[name]
            triangles = positions[faces]
            if clip is not None:
                centers = triangles.mean(axis=1)
                triangles = triangles[np.all((centers >= clip[0]) & (centers <= clip[1]), axis=1)]
            extent.append(triangles.reshape(-1, 3))
            collection = Poly3DCollection(triangles, linewidths=0, facecolor=COLORS[name],
                                          alpha=.2 if name in ('Humerus', 'SCAPULA', 'CLAVICLE') else .95)
            ax.add_collection3d(collection)
        vertices = np.concatenate(extent)
        bounds = clip if clip is not None else np.array([vertices.min(axis=0), vertices.max(axis=0)])
        center = bounds.mean(axis=0); radius = np.ptp(bounds, axis=0).max() / 2
        ax.set_xlim(center[0] - radius, center[0] + radius)
        ax.set_ylim(center[1] - radius, center[1] + radius)
        ax.set_zlim(center[2] - radius, center[2] + radius)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elevation, azim=azimuth)
        ax.set_xlabel('Native X'); ax.set_ylabel('Native Y'); ax.set_zlabel('Native Z')
        ax.set_title(title, fontsize=12)
    fig.suptitle('FDA shoulder source — extracted native finite-element surfaces\n'
                 'Research inspection; no clinical approval or cuff-tendon volume claim', fontsize=16)
    fig.legend(handles=[Patch(color=COLORS[key], label=label) for key, label in (
        ('Labrum', 'Labrum'), ('Gcart', 'Glenoid cartilage (offset)'), ('Hcart', 'Humeral cartilage (offset)'),
        ('AC_Lig', 'AC ligament'), ('Humerus', 'Bones translucent'))], loc='lower center', ncol=3,
        bbox_to_anchor=(.5, .036), frameon=False)
    fig.text(.5, .018, 'CC0 · FDA RST24OP04.01 · Native assembly transforms retained; quadratic faces tessellated only for preview',
             ha='center', fontsize=9)
    fig.subplots_adjust(top=.89, bottom=.13, left=.04, right=.98, hspace=.13, wspace=.06)
    fig.savefig(STAGE / 'native-shoulder-review.png', dpi=150)
    plt.close(fig)
    print(STAGE / 'native-shoulder-review.png')


if __name__ == '__main__':
    main()
