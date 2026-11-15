#!/usr/bin/env python3
"""Render every original upstream pancreatic source element without fusion or repairs."""
import argparse
import hashlib
import json
from pathlib import Path


def render(root,output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    receipt=json.loads((root/'upstream-acquisition.json').read_text())
    review_path=output/'original-obj-geometry-review.json';review=json.loads(review_path.read_text());meshes={}
    if hashlib.sha256((root/'upstream-acquisition.json').read_bytes()).hexdigest()!=review['original_acquisition_sha256']:raise ValueError('Acquisition review changed')
    for record in review['records']:
        raw=(root/'objects'/(record['id']+'.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=record['source_sha256']:raise ValueError('Original source changed')
        v,n,f,nf=read_obj(raw.decode())
        if hashlib.sha256(v.astype('<f8').tobytes()).hexdigest()!=record['positions_float64_le_sha256'] or hashlib.sha256(f.astype('<i8').tobytes()).hexdigest()!=record['face_indices_int64_le_sha256']:
            raise ValueError('Original geometry differs from audit')
        meshes[record['id']]=(v,f)
    panels=[]
    for group in review['source_groups']:
        ids=group['element_ids']
        if group['source_fma']=='FMA63120':
            panels.extend([(group['source_target_label']+' | '+fid,[fid]) for fid in ids])
        else:panels.append((group['source_target_label'],ids))
    if len(panels)!=12 or set(fid for _,ids in panels for fid in ids)!=set(meshes):raise ValueError('Original element omitted from atlas')
    figures=[]
    def draw(ax,ids,colors,azimuth):
        points=np.concatenate([meshes[fid][0] for fid in ids]);lo=points.min(0);hi=points.max(0);extent=np.maximum(hi-lo,.1);pad=extent*.05
        for fid,color in zip(ids,colors):
            v,f=meshes[fid];tri=v[f]
            normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normal,axis=1)
            unit=np.divide(normal,length[:,None],out=np.zeros_like(normal),where=length[:,None]>0)
            light=np.array([1,-1,2],float);light/=np.linalg.norm(light)
            face_colors=np.tile(color,(len(f),1));face_colors[:,:3]*=(.6+.4*np.maximum(unit@light,0))[:,None]
            ax.add_collection3d(Poly3DCollection(tri,facecolors=face_colors,edgecolor='none',linewidths=0))
        ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_zlim(lo[2]-pad[2],hi[2]+pad[2]);ax.set_box_aspect(extent)
        ax.view_init(elev=20,azim=azimuth);ax.locator_params(nbins=3);ax.tick_params(labelsize=5)
        ax.set_xlabel('Source X mm',fontsize=7);ax.set_ylabel('Source Y mm',fontsize=7);ax.set_zlabel('Source Z mm',fontsize=7)
        return {'element_ids':ids,'all_original_triangles':sum(len(meshes[fid][1]) for fid in ids),'bounds_original_mm':[lo.tolist(),hi.tolist()],
                'source_vertices_or_faces_changed':False,'display_colors':[list(c) for c in colors]}
    for azimuth in [35,215]:
        fig=plt.figure(figsize=(20,15));rows=[]
        for i,(label,ids) in enumerate(panels,1):
            ax=fig.add_subplot(3,4,i,projection='3d')
            row=draw(ax,ids,[(.3,.6,.7,1)]*len(ids),azimuth);row['label']=label;rows.append(row)
            ax.set_title(label+'\n'+str(row['all_original_triangles'])+' original triangles',fontsize=9)
        fig.suptitle('BodyParts3D upstream version-manifest 4.3 | every selected duct and vessel source element\nOriginal geometry and declared millimetres; colours are review aids; panel scales differ; no fitting, repairs or clinical approval',fontsize=12)
        fig.subplots_adjust(left=.05,right=.95,bottom=.07,top=.90,hspace=.35,wspace=.16)
        fig.text(.5,.015,'BodyParts3D © 2008 DBCLS | CC BY-SA 2.1 Japan | adaptation: review colours, lighting and source views',ha='center',fontsize=9)
        path=output/('original-elements-azimuth'+str(azimuth)+'.png');fig.savefig(path,dpi=110);plt.close(fig)
        figures.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'azimuth_degrees':azimuth,'panels':rows})
    fig=plt.figure(figsize=(14,10));rows=[]
    for slot,(azimuth,parent) in enumerate([(35,None),(35,'FJ1895'),(35,'FJ2629'),(215,None),(215,'FJ1895'),(215,'FJ2629')],1):
        ax=fig.add_subplot(2,3,slot,projection='3d');ids=([parent] if parent else [])+['FJ1896']
        colors=([(.7,.7,.65,.12)] if parent else [])+[(.15,.5,.75,1)]
        row=draw(ax,ids,colors,azimuth);row['azimuth_degrees']=azimuth;rows.append(row)
        ax.set_title(('Original duct tree alone' if parent is None else 'Source duct + '+parent+' coordinate context')+f'\nAzimuth {azimuth}; no patient registration',fontsize=10)
    fig.suptitle('Original pancreatic duct tree with each separate source parenchymal element\nSource coordinates retained; alternative parenchyma not merged; overlay does not prove biological correspondence or complete duct anatomy',fontsize=11)
    fig.subplots_adjust(left=.05,right=.95,bottom=.08,top=.87,hspace=.35,wspace=.15)
    fig.text(.5,.015,'BodyParts3D © 2008 DBCLS | CC BY-SA 2.1 Japan | adaptation: review colours, lighting and source views',ha='center',fontsize=9)
    path=output/'original-duct-parenchyma-context.png';fig.savefig(path,dpi=120);plt.close(fig)
    figures.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'panels':rows,'alternative_source_parenchyma_fused':False})
    (output/'source-figure-review.json').write_text(json.dumps({'source_geometry_review_sha256':hashlib.sha256(review_path.read_bytes()).hexdigest(),'figures':figures,
            'review_face_lighting_applied':True,'derived_figure_license':'CC BY-SA 2.1 Japan','source_coordinate_transforms_performed':False,'source_elements_repaired_or_fused':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Each source compound is displayed with all original constituent triangles; parent labels do not confer fine lumen/wall or reporting-target coverage.',
                      'Duplicate/alternative parenchymal source elements are kept separate; same declared source coordinates do not establish matched donor anatomy or acquired CT correspondence.',
                      'Review colours/transparency and camera pose are display choices, not biological boundaries or clinical phase orientation.']},indent=2)+'\n')
    print('Rendered all 25 source objects and separate duct/parenchyma contexts',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();render(a.source_root,a.output)
