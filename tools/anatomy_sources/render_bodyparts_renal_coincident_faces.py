#!/usr/bin/env python3
"""Render original coincident source faces with full coordinate ticks and no topology changes."""
import argparse
import hashlib
import json
from pathlib import Path


def render(output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import ScalarFormatter
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    review_path=output/'coincident-source-face-review.json';review=json.loads(review_path.read_text())
    if len(review['findings']) != 3:
        raise ValueError('Reviewed source face set differs')
    fig=plt.figure(figsize=(14,5))
    for k,row in enumerate(review['findings'],1):
        ax=fig.add_subplot(1,3,k,projection='3d');tri=np.asarray(row['original_positions_mm'],dtype=float)
        if tri.shape != (2,3,3) or not np.isfinite(tri).all():
            raise ValueError('Original source face positions differ')
        ax.add_collection3d(Poly3DCollection(tri,facecolors=['#b84c6f','#3b77b4'],edgecolors='#182a35',alpha=.45))
        lo=tri.min((0,1));hi=tri.max((0,1));span=np.maximum(hi-lo,.001);pad=span*.15
        ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_zlim(lo[2]-pad[2],hi[2]+pad[2]);ax.set_box_aspect(span)
        ax.view_init(elev=25,azim=35);ax.set_title(row['element_id']+' original faces '+str(row['face_indices']),fontsize=10)
        ax.set_xlabel('Source X mm');ax.set_ylabel('Source Y mm');ax.set_zlabel('Source Z mm',labelpad=18);ax.tick_params(labelsize=7);ax.locator_params(nbins=3)
        for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:
            formatter=ScalarFormatter(useOffset=False);formatter.set_scientific(False);axis.set_major_formatter(formatter)
    fig.suptitle('Three original coincident two-face components | no pruning or anatomical classification',fontsize=12)
    fig.subplots_adjust(left=.04,right=.96,bottom=.23,top=.8,wspace=.28)
    fig.text(.5,.045,'Each pair occupies the same exact-position triangle; review colours distinguish source faces, not tissue.\nBodyParts3D © 2008 DBCLS | CC BY-SA 2.1 Japan | adaptation: original-coordinate analytical close-ups',ha='center',fontsize=9)
    path=output/'coincident-source-face-locations.png';fig.savefig(path,dpi=120);plt.close(fig)
    (output/'coincident-source-face-figure-review.json').write_text(json.dumps({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_review_sha256':hashlib.sha256(review_path.read_bytes()).hexdigest(),'source_positions_or_faces_changed':False,
        'clinical_approval':False,'runtime_promoted':False,'derived_figure_license':'CC BY-SA 2.1 Japan'},indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    render(parser.parse_args().output)
