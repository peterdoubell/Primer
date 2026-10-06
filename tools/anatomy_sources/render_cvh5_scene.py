#!/usr/bin/env python3
"""Render source-placed candidates with authored colours and named view controls for review."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.review_cvh5_scene import transform_points,transform_normals


def render(scene,candidates,normals):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    scene_raw=(scene/'source-scene-review.json').read_bytes();data=json.loads(scene_raw)
    views_raw=(scene/'source-pdf-view-review.json').read_bytes();views=json.loads(views_raw)
    if views['original_u3d_sha256']!=data['original_u3d_sha256']:raise ValueError('View/source mismatch')
    parts=[]
    for row in data['occurrences']:
        packed=(candidates/row['candidate_file']).read_bytes();npacked=(normals/row['normal_file']).read_bytes()
        if hashlib.sha256(packed).hexdigest()!=row['candidate_sha256'] or hashlib.sha256(npacked).hexdigest()!=row['normal_sha256']:raise ValueError('Candidate differs')
        mesh=json.loads(gzip.decompress(packed));normal=json.loads(gzip.decompress(npacked));matrix=np.asarray(row['source_world_matrix_rows'])
        v=transform_points(mesh['positions'],matrix);n=transform_normals(normal['interpreted_normal_vectors'],matrix);f=np.asarray(mesh['faces']);ni=np.asarray(mesh['normal_indices']).reshape(-1,3)
        if hashlib.sha256(v.astype('<f8').tobytes()).hexdigest()!=row['placed_candidate_positions_float64_sha256']:raise ValueError('Source placement differs')
        colour=np.asarray(row['source_material']['diffuse_rgb'])
        if np.any(colour<0) or np.any(colour>1):raise ValueError('Display colour range needs review')
        nf=n[ni].mean(1);length=np.linalg.norm(nf,axis=1);nf=np.divide(nf,length[:,None],out=np.zeros_like(nf),where=length[:,None]>0)
        light=np.asarray([.4,-.6,.7]);light/=np.linalg.norm(light);intensity=.35+.65*np.abs(nf@light)
        parts.append((row,v,f,colour*intensity[:,None]))
    all_v=np.concatenate([v for _,v,_,_ in parts]);lo=all_v.min(0);hi=all_v.max(0);extent=hi-lo;pad=float(extent.max())*.04
    fig=plt.figure(figsize=(12,12),layout='constrained');fig.get_layout_engine().set(rect=(0,.035,1,.94));panels=[]
    for index,view in enumerate(views['views']):
        overrides={r['node_name']:r for r in view['node_overrides'] if r['node_name'] is not None}
        for column,azimuth in enumerate([-90,90]):
            ax=fig.add_subplot(2,2,index*2+column+1,projection='3d');shown=[];triangles=0
            for row,v,f,colours in parts:
                override=overrides.get(row['node_name'],{})
                if override.get('visible') is False:continue
                if row['source_visibility']==0:continue
                opacity=override.get('opacity')
                if opacity is None:opacity=row['source_material']['opacity']
                ax.add_collection3d(Poly3DCollection(v[f],facecolors=colours,edgecolor='none',alpha=opacity))
                shown.append(row['node_name']);triangles+=len(f)
            ax.set_xlim(lo[0]-pad,hi[0]+pad);ax.set_ylim(lo[1]-pad,hi[1]+pad);ax.set_zlim(lo[2]-pad,hi[2]+pad);ax.set_box_aspect(extent+2*pad);ax.view_init(10,azimuth);ax.set_axis_off()
            ax.set_title(view['external_name']+' | review azimuth '+str(azimuth)+'°\n'+str(len(shown))+' named model occurrences',fontsize=11)
            panels.append({'authored_view_name':view['external_name'],'review_azimuth':azimuth,'displayed_nodes':shown,'displayed_triangles':triangles,'named_node_overrides':list(overrides.values())})
    fig.suptitle('CVH5 | source placements, authored colours and named view visibility\nCandidate geometry and encoded-normal interpretation remain held\nReview cameras/lighting/transparency approximation; no clinical axes or pixel equivalence',fontsize=12)
    fig.text(.5,.006,'Wu et al. 2015 | CC BY 4.0 | Source U3D and original PDF remain unchanged\nColours are authored atlas controls, not tissue/perfusion signals. View matrices and unnamed override scope remain unverified.',ha='center',fontsize=9)
    file=scene/'source-placed-candidate-assembly.png';fig.savefig(file,dpi=100);plt.close(fig)
    (scene/'assembly-view-review.json').write_text(json.dumps({'scene_review_sha256':hashlib.sha256(scene_raw).hexdigest(),'pdf_view_review_sha256':hashlib.sha256(views_raw).hexdigest(),
        'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'panels':panels,'candidate_encoded_normals_used':True,
        'review_lighting_is_original_pdf_lighting':False,'pdf_view_matrices_applied':False,'unnamed_override_scope_applied_as_verified':False,
        'original_renderer_pixel_equivalence_verified':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--scene',type=Path,required=True);p.add_argument('--candidates',type=Path,required=True);p.add_argument('--normals',type=Path,required=True)
    a=p.parse_args();render(a.scene,a.candidates,a.normals)
