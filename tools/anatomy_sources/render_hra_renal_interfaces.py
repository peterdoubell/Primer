#!/usr/bin/env python3
"""Localize every unmatched pelvis boundary in original source geometry, without connecting parts."""
import argparse
import hashlib
import json
from pathlib import Path


def render(root,review_root):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection,Line3DCollection
    from tools.anatomy_sources.inspect_hra_renal_glb import read_glb,accessor
    report_path=review_root/'exact-source-interface-review.json';report=json.loads(report_path.read_text())
    glb=root/'ureter-female-right-v1.2/3d-vh-f-ureter-r.glb';raw=glb.read_bytes()
    expected=next(r['source_glb_sha256'] for r in report['sources'] if r['source']=='ureter-female-right-v1.2')
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Source collecting-system object changed')
    d,binary=read_glb(raw);parts={};rotation=np.array([[1,0,0],[0,0,-1],[0,1,0]],float)
    for node in d['nodes']:
        if node.get('name') not in ('VH_F_renal_pelvis_R','VH_F_right_ureter'):continue
        p=d['meshes'][node['mesh']]['primitives'][0];v=accessor(d,binary,p['attributes']['POSITION']);f=accessor(d,binary,p['indices']).reshape(-1,3)
        parts[node['name']]=(v,f)
    components=report['unmatched_boundary_components']
    if sum(c['edges'] for c in components)!=report['unmatched_boundary_edges']:raise ValueError('Unmatched graph extent differs')
    curves=[np.asarray(c['coordinates_original_metres'],float) for c in components];all_points=np.concatenate([c.reshape(-1,3) for c in curves]);all_display=all_points@rotation.T
    figures=[]
    for name,azimuth in [('unmatched-pelvis-azimuth35',35),('unmatched-pelvis-azimuth215',215)]:
        fig=plt.figure(figsize=(16,7));panels=[]
        for index,(label,selected,zoom) in enumerate([('Pelvis and all unmatched source edges',['VH_F_renal_pelvis_R'],False),
                                                     ('Unmatched boundary graphs only',[],True),
                                                     ('Original ureter with pelvis boundary locations',['VH_F_right_ureter'],False)],1):
            ax=fig.add_subplot(1,3,index,projection='3d');submitted=[]
            for key in selected:
                vertices,faces=parts[key];triangles=(vertices@rotation.T)[faces]
                normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);length=np.linalg.norm(normals,axis=1)
                unit=np.divide(normals,length[:,None],out=np.zeros_like(normals),where=length[:,None]>0);light=np.array([1,-1,2],float);light/=np.linalg.norm(light)
                rgba=np.tile([.9372,.9176,.8431,1.],(len(faces),1));rgba[:,:3]*=(.65+.35*np.maximum(unit@light,0))[:,None]
                ax.add_collection3d(Poly3DCollection(triangles,facecolors=rgba,linewidths=0,shade=False));submitted.append(vertices@rotation.T)
            for i,curve in enumerate(curves):ax.add_collection3d(Line3DCollection(curve@rotation.T,colors=['#d04c88','#1b90a8'][i%2],linewidths=1.5))
            if zoom:lo=all_display.min(0)-.0005;hi=all_display.max(0)+.0005
            else:
                visible=np.concatenate(submitted+[all_display]);lo=visible.min(0);hi=visible.max(0);padding=np.maximum((hi-lo)*.05,.0005);lo-=padding;hi+=padding
            extent=hi-lo;ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect(extent);ax.view_init(elev=25,azim=azimuth)
            ax.set_xlabel('glTF X m',fontsize=8);ax.set_ylabel('−glTF Z m',fontsize=8);ax.set_zlabel('glTF Y m',fontsize=8);ax.locator_params(nbins=3);ax.tick_params(labelsize=7)
            ax.set_title(label+'\nBoth original boundary graphs; no fitted connection or cap',fontsize=10)
            panels.append({'source_parts':selected,'all_40_unmatched_edges_submitted':sum(len(c) for c in curves)==40,
                           'source_geometry_edited':False,'display_view_only_zoom':zoom,'display_axis_rotation':rotation.tolist()})
        fig.suptitle('HRA original female-right renal source | all unmatched boundary edges\nGraph component 1 pink / component 2 cyan; geometric review indices, not anatomical identities or closure approval',fontsize=12)
        fig.subplots_adjust(left=.06,right=.95,bottom=.12,top=.80,wspace=.2);path=review_root/(name+'.png');fig.savefig(path,dpi=140);plt.close(fig)
        figures.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'panels':panels,'azimuth_degrees':azimuth})
    (review_root/'unmatched-boundary-figure-review.json').write_text(json.dumps({'source_interface_review_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest(),
        'source_glb_sha256':expected,'figures':figures,'source_meshes_moved_fitted_or_closed':False,'clinical_approval':False,'runtime_promoted':False,
        'limits':['Reference objects retain original coordinates and are not a registered patient CT or MRI.',
                  'A closed boundary graph is not a closed anatomical surface or verified lumen/wall/outlet identity.',
                  'A nearby source ureter in the same coordinates does not prove continuous biological connection or absent gaps/overlaps.']},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--review-root',type=Path,required=True)
    a=p.parse_args();render(a.source_root,a.review_root)
