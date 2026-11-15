#!/usr/bin/env python3
"""Render all original HRA pancreatic regions without smoothing or source repairs."""
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
    from tools.anatomy_sources.inspect_hra_renal_glb import read_glb,accessor
    rotation=np.array([[1,0,0],[0,0,-1],[0,1,0]],float)
    results=[]
    for sex in ['female','male']:
        key='pancreas-'+sex+'-v1.3';folder=root/key
        inventory_path=output/(key+'-original-primitives.json');proof=json.loads(inventory_path.read_text())
        path=folder/('3d-vh-'+sex[0]+'-pancreas.glb');raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=proof['source_glb_sha256']:raise ValueError('Original source GLB changed')
        doc,binary=read_glb(raw);parts=[]
        for record in proof['records']:
            node=doc['nodes'][record['node_index']];p=doc['meshes'][node['mesh']]['primitives'][record['primitive_index']]
            vertices=accessor(doc,binary,p['attributes']['POSITION']);indices=accessor(doc,binary,p['indices']).reshape(-1)
            if hashlib.sha256(vertices.tobytes()).hexdigest()!=record['position_accessor_sha256'] or hashlib.sha256(indices.tobytes()).hexdigest()!=record['indices_accessor_sha256']:
                raise ValueError('Source primitive differs from inventory')
            color=doc['materials'][p['material']].get('pbrMetallicRoughness',{}).get('baseColorFactor',[.7,.5,.3,1])
            parts.append((record,vertices,indices.reshape(-1,3),color))
        panels=[('All five original regions',parts)]+[(r['source_label'],[(r,v,f,c)]) for r,v,f,c in parts]
        if len(panels)!=6:raise ValueError('Unreviewed pancreatic region inventory')
        for azimuth in [35,215]:
            fig=plt.figure(figsize=(15,11));rows=[]
            for slot,(name,selected) in enumerate(panels,1):
                ax=fig.add_subplot(2,3,slot,projection='3d')
                displayed=[v@rotation.T for _,v,_,_ in selected]
                lo=np.min([v.min(0) for v in displayed],axis=0);hi=np.max([v.max(0) for v in displayed],axis=0)
                extent=np.maximum(hi-lo,.001);pad=.05*extent
                for r,v,f,c in selected:
                    tri=(v@rotation.T)[f]
                    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normal,axis=1)
                    unit=np.divide(normal,length[:,None],out=np.zeros_like(normal),where=length[:,None]>0)
                    light=np.array([1,-1,2],float);light/=np.linalg.norm(light)
                    colors=np.tile(c,(len(f),1));colors[:,:3]*=(.65+.35*np.maximum(unit@light,0))[:,None]
                    ax.add_collection3d(Poly3DCollection(tri,facecolors=colors,linewidths=0,shade=False))
                ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_zlim(lo[2]-pad[2],hi[2]+pad[2]);ax.set_box_aspect(extent)
                ax.view_init(elev=20,azim=azimuth);ax.locator_params(nbins=3);ax.tick_params(labelsize=6)
                ax.set_xlabel('glTF X m',fontsize=7);ax.set_ylabel('−glTF Z m',fontsize=7);ax.set_zlabel('glTF Y m',fontsize=7)
                ax.set_title(name+'\n'+str(sum(len(f) for _,_,f,_ in selected))+' original triangles',fontsize=9)
                rows.append({'label':name,'source_nodes':[r['node_name'] for r,_,_,_ in selected],
                             'source_triangle_count':sum(len(f) for _,_,f,_ in selected),'display_bounds_metres':[lo.tolist(),hi.tolist()],
                             'display_rigid_rotation':rotation.tolist(),'source_vertex_or_face_values_changed':False})
            fig.suptitle('HRA '+sex+' pancreas v1.3 | original reference regions\nSource colours and review lighting; all triangles retained; panel scales differ; no CT registration or clinical approval',fontsize=11)
            fig.subplots_adjust(left=.05,right=.95,bottom=.09,top=.87,hspace=.35,wspace=.16)
            path=output/(key+'-azimuth'+str(azimuth)+'.png');fig.savefig(path,dpi=110);plt.close(fig)
            results.append({'sex':sex,'source_glb_sha256':proof['source_glb_sha256'],'inventory_sha256':hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
                            'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'azimuth_degrees':azimuth,'elevation_degrees':20,'panels':rows})
            print('Rendered',path,flush=True)
    (output/'source-figure-review.json').write_text(json.dumps({'figures':results,'source_geometry_repaired':False,'runtime_promoted':False,'clinical_approval':False,
        'limits':['Source-defined five gross regions do not provide duct lumina/walls, arteries/veins or neural pathways.',
                  'All open, nonmanifold and zero-area source elements remain unchanged; source mesh appearance is not clinical boundary approval.',
                  'The display axis rotation retains source geometry, not patient coordinate registration; independently derived models are not fitted to the acquired CT case.']},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();render(a.source_root,a.output)
