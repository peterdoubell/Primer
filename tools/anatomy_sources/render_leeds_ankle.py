#!/usr/bin/env python3
"""Render staged native-coordinate ankle surfaces for source inspection only."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

STAGE = Path('/tmp/primer-msk-sources/ankle-next/leeds-1207')
COLORS = {'PT_CARTILAGE_1': '#22a3b8', 'PT_CARTILAGE_2': '#e9b44c',
          'PT_CYSTS': '#cb3d48', 'PT_TALUS': '#d5ccc0',
          'PT_TIBIA': '#c0ac9b', 'PT_TIBIA_FOR_CYSTS': '#c0ac9b'}


def main():
    report = json.loads((STAGE / 'mesh-inspection.json').read_text())
    fig = plt.figure(figsize=(15, 11), facecolor='#f6f3ef')
    for row, model in enumerate(report['models']):
        all_points = []
        parts = []
        for part in model['parts']:
            geometry = np.load(STAGE / part['geometry'])
            vertices, faces = geometry['positions'], geometry['indices']
            all_points.append(vertices)
            parts.append((part['source_set'], vertices, faces))
        points = np.concatenate(all_points)
        low, high = points.min(axis=0), points.max(axis=0)
        center, radius = (low + high) / 2, (high - low).max() / 2
        for column, azimuth in enumerate((-55, 120)):
            ax = fig.add_subplot(2, 2, row * 2 + column + 1, projection='3d', facecolor='#f6f3ef')
            for name, vertices, faces in parts:
                collection = Poly3DCollection(vertices[faces], linewidths=0,
                    facecolor=COLORS[name], alpha=.18 if 'TIBIA' in name or name == 'PT_TALUS' else .95)
                ax.add_collection3d(collection)
            ax.set_xlim(center[0] - radius, center[0] + radius)
            ax.set_ylim(center[1] - radius, center[1] + radius)
            ax.set_zlim(center[2] - radius, center[2] + radius)
            ax.set_box_aspect((1, 1, 1))
            ax.view_init(elev=22, azim=azimuth)
            ax.set_xlabel('Native X'); ax.set_ylabel('Native Y'); ax.set_zlabel('Native Z')
            condition = 'Cyst-ignored comparator' if 'intact' in model['file'] else 'Cyst-containing model'
            ax.set_title(condition + ' · view ' + str(column + 1), fontsize=13)
    fig.suptitle('Leeds ankle 1 / timepoint 1 — actual segmented cartilage boundaries\n'
                 'Haemophilic source; not healthy anatomy or clinical approval', fontsize=17)
    handles = [Patch(color=COLORS[key], label=label) for key, label in (
        ('PT_CARTILAGE_1', 'Cartilage 1 (tibial interface)'), ('PT_CARTILAGE_2', 'Cartilage 2 (talar interface)'),
        ('PT_CYSTS', 'Source cyst volume'), ('PT_TALUS', 'Bones shown translucent'))]
    fig.legend(handles=handles, loc='lower center', ncol=2, frameon=False, bbox_to_anchor=(.5, .035))
    fig.text(.5, .018, 'CC BY 4.0 · Talbott & Mengoni (2022), doi:10.5518/1207 · Native coordinates; quadratic faces triangulated for preview',
             ha='center', fontsize=9)
    fig.subplots_adjust(top=.86, bottom=.13, left=.04, right=.97, hspace=.16, wspace=.07)
    fig.savefig(STAGE / 'native-cartilage-review.png', dpi=150)
    plt.close(fig)
    print(STAGE / 'native-cartilage-review.png')


if __name__ == '__main__':
    main()
