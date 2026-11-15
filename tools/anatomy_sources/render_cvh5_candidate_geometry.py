#!/usr/bin/env python3
"""Show every candidate resource without changing coordinates or promoting decoder assumptions."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import textwrap


def render(output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    raw=(output/'candidate-geometry-review.json').read_bytes();review=json.loads(raw);figures=[]
    for start in range(0,len(review['resources']),8):
        selected=review['resources'][start:start+8];fig=plt.figure(figsize=(12,17),layout='constrained');fig.get_layout_engine().set(rect=(0,.035,1,.95))
        for k,row in enumerate(selected,1):
            packed=(output/row['file']).read_bytes()
            if hashlib.sha256(packed).hexdigest()!=row['sha256']:raise ValueError('Candidate resource differs')
            mesh=json.loads(gzip.decompress(packed));v=np.asarray(mesh['positions']);f=np.asarray(mesh['faces']);lo=v.min(0);hi=v.max(0);extent=hi-lo;pad=max(float(extent.max())*.05,.001)
            face_normals=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
            length=np.linalg.norm(face_normals,axis=1);unit=np.divide(face_normals,length[:,None],out=np.zeros_like(face_normals),where=length[:,None]>0)
            light=np.asarray([.4,-.6,.7]);light/=np.linalg.norm(light)
            intensity=.3+.7*np.abs(unit@light);colours=intensity[:,None]*np.asarray([.55,.67,.68])
            ax=fig.add_subplot(4,2,k,projection='3d');ax.add_collection3d(Poly3DCollection(v[f],facecolors=colours,edgecolor='none',alpha=1))
            ax.set_xlim(lo[0]-pad,hi[0]+pad);ax.set_ylim(lo[1]-pad,hi[1]+pad);ax.set_zlim(lo[2]-pad,hi[2]+pad);ax.set_box_aspect(np.maximum(extent+pad*2,.001));ax.view_init(22,-65);ax.set_axis_off()
            names=' / '.join(n['name'] for n in row['source_model_nodes'])
            ax.set_title('\n'.join(textwrap.wrap(names,44))+'\n'+row['resource_name']+' | '+str(row['triangles'])+' candidate triangles',fontsize=10)
        fig.suptitle('CVH5 | experimental encoded-mesh interpretations\nAll candidate faces retained; UIC1 bootstrap and normal attributes held\nResource coordinates only; no fitting, clinical axes, registration or anatomy approval',fontsize=12)
        fig.text(.5,.006,'Wu et al. 2015 | CC BY 4.0 | Original U3D bytes remain unchanged\nReview colour and geometric face shading are display choices, not recovered source materials/normals',ha='center',fontsize=9)
        name=f'candidate-resources-{start:02d}-{start+len(selected)-1:02d}.png';p=output/name;fig.savefig(p,dpi=100);plt.close(fig)
        figures.append({'file':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'resource_names':[r['resource_name'] for r in selected],'all_candidate_triangles_displayed':sum(r['triangles'] for r in selected),'coordinates_changed':False})
    (output/'candidate-view-review.json').write_text(json.dumps({'candidate_review_sha256':hashlib.sha256(raw).hexdigest(),'figures':figures,'decoder_interpretation_verified':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    render(p.parse_args().output)
