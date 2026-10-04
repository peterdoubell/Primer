#!/usr/bin/env python3
"""Render all original peritoneal source objects with fragmentation and unapproved scope visible."""
import argparse,gzip,hashlib,json
from pathlib import Path


def render(root,output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    path=output/'original-obj-geometry-review.json.gz';payload=gzip.decompress(path.read_bytes());report=json.loads(payload);parts=[]
    for r in report['records']:
        raw=(root/'objects'/(r['id']+'.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=r['source_sha256']:raise ValueError('Original source changed')
        v,n,f,nf=read_obj(raw.decode())
        if hashlib.sha256(v.astype('<f8').tobytes()).hexdigest()!=r['positions_float64_le_sha256'] or hashlib.sha256(f.astype('<i8').tobytes()).hexdigest()!=r['face_indices_int64_le_sha256']:raise ValueError('Original geometry differs')
        parts.append((r,v,f))
    figures=[]
    for azimuth in [35,215]:
        fig=plt.figure(figsize=(14,11));panels=[]
        for slot,(r,v,f) in enumerate(parts,1):
            ax=fig.add_subplot(2,2,slot,projection='3d');tri=v[f]
            normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normals,axis=1)
            unit=np.divide(normals,length[:,None],out=np.zeros_like(normals),where=length[:,None]>0);light=np.array([1,-1,2],float);light/=np.linalg.norm(light)
            colors=np.tile([.4,.65,.68,1],(len(f),1));colors[:,:3]*=(.6+.4*np.maximum(unit@light,0))[:,None]
            ax.add_collection3d(Poly3DCollection(tri,facecolors=colors,edgecolor='none',linewidths=0))
            lo=v.min(0);hi=v.max(0);extent=np.maximum(hi-lo,.1);pad=extent*.05
            ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_zlim(lo[2]-pad[2],hi[2]+pad[2]);ax.set_box_aspect(extent)
            ax.view_init(elev=20,azim=azimuth);ax.locator_params(nbins=3);ax.tick_params(labelsize=6)
            ax.set_xlabel('Source X mm',fontsize=8);ax.set_ylabel('Source Y mm',fontsize=8);ax.set_zlabel('Source Z mm',fontsize=8)
            count=len(r['exact_position_analysis_topology']['components'])
            ax.set_title(r['id']+' | '+r['source_label']+f'\n{len(f)} original triangles; {count} exact-position components',fontsize=9)
            panels.append({'element_id':r['id'],'source_label':r['source_label'],'original_triangle_count':len(f),'exact_position_components':count,
                           'source_bounds_mm':[lo.tolist(),hi.tolist()],'source_positions_or_faces_changed':False})
        fig.suptitle('Original upstream peritoneal source objects | version-manifest 4.3\nSource labels/fragmentation retained; no fusion, repair, patient registration or complete peritoneal anatomy approval',fontsize=11)
        fig.subplots_adjust(left=.05,right=.95,bottom=.09,top=.86,hspace=.35,wspace=.18)
        fig.text(.5,.02,'BodyParts3D © 2008 DBCLS | CC BY-SA 2.1 Japan | adaptation: review lighting and original-source views',ha='center',fontsize=9)
        file=output/('original-source-azimuth'+str(azimuth)+'.png');fig.savefig(file,dpi=110);plt.close(fig)
        figures.append({'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'azimuth_degrees':azimuth,'panels':panels})
    (output/'source-figure-review.json').write_text(json.dumps({'source_geometry_review_sha256':hashlib.sha256(payload).hexdigest(),'figures':figures,
       'source_meshes_merged_repaired_or_deduplicated':False,'clinical_approval':False,'runtime_promoted':False,'derived_figure_license':'CC BY-SA 2.1 Japan'},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();render(a.source_root,a.output)
