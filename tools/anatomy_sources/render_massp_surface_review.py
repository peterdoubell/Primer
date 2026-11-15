"""Render verified offline source-label candidates without changing geometry."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def render(root, out, filename='pallidal-native-surface-candidates.png'):
    out.mkdir(parents=True, exist_ok=True)
    record = json.loads((root/'surface-review.json').read_text())
    colors = {'gpi': '#a638bf', 'gpe': '#1c947b', 'put': '#cc7b23'}
    meshes = []
    for row in record['records']:
        if not row['output_mesh_created']:
            continue
        path = root/row['mesh_file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['mesh_sha256']:
            raise ValueError('Candidate mesh hash changed')
        with np.load(path) as data:
            meshes.append((row['code'], data['vertices'].copy(), data['faces'].copy()))
    if not meshes:
        raise ValueError('No reviewed candidate outputs')
    low = np.min([v.min(0) for _, v, _ in meshes], axis=0) - 3
    high = np.max([v.max(0) for _, v, _ in meshes], axis=0) + 3
    legend = ' | '.join({'gpi': 'GPi purple', 'gpe': 'GPe green', 'put': 'Putamen amber'}[code]
                        for code in sorted({code for code, _, _ in meshes}))
    selection = 'best-label' if 'bestlabel' in record.get('publisher_selection_file', '') else 'maximum-label'
    fig = plt.figure(figsize=(15,6), layout='constrained')
    for index, (elev, azim) in enumerate([(15,-90), (20,0), (65,-70)]):
        ax = fig.add_subplot(1,3,index+1,projection='3d')
        for code, vertices, faces in meshes:
            surface = Poly3DCollection(vertices[faces], facecolor=colors[code], edgecolor='none',
                                       alpha=.35 if code == 'put' else .9)
            ax.add_collection3d(surface)
        ax.text2D(.01,.98,legend,transform=ax.transAxes,fontsize=9)
        ax.set_xlim(low[0],high[0]); ax.set_ylim(low[1],high[1]); ax.set_zlim(low[2],high[2])
        ax.set_box_aspect(high-low)
        ax.set_xlabel('RAS X mm'); ax.set_ylabel('RAS Y mm'); ax.set_zlabel('RAS Z mm')
        ax.view_init(elev=elev,azim=azim); ax.set_title(f'Native atlas view {index+1}')
    title = ("MASSP 2.0 joint-interface candidates\nUnchanged source labels; derived tetrahedral interpolation, not measured subvoxel anatomy"
             if 'Freudenthal' in record.get('construction','') else
             f'MASSP 2.0 source surface candidates — all original {selection} components\nNo smoothing, decimation, anatomical editing or individual-anatomy claim')
    fig.suptitle(title,fontsize=13)
    fig.savefig(out/filename,dpi=150,bbox_inches='tight',pad_inches=.6)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--filename',default='pallidal-native-surface-candidates.png')
    args=parser.parse_args()
    render(args.source,args.output,args.filename)
