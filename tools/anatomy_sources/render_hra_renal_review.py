#!/usr/bin/env python3
"""Render original source HRA renal primitives in their declared frame without repairs."""
import argparse
import hashlib
import json
from pathlib import Path


def render(root,review_root):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from tools.anatomy_sources.inspect_hra_renal_glb import read_glb,accessor
    source_files=[(root/'3d-vh-f-kidney-r.glb','kidney-female-right-v1.3'),
                  (root/'ureter-female-right-v1.2/3d-vh-f-ureter-r.glb','ureter-female-right-v1.2'),
                  (root/'renal-pelvis-female-right-v1.0/3d-vh-f-renal-pelvis-r.glb','renal-pelvis-female-right-v1.0')]
    objects={};proofs=[]
    for path,key in source_files:
        proof_path=review_root/(key+'-geometry-inventory.json');proof=json.loads(proof_path.read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest()!=proof['source_glb_sha256']:raise ValueError('Source GLB changed')
        doc,bin_data=read_glb(path.read_bytes());parts=[]
        for record in proof['records']:
            node=doc['nodes'][record['node_index']];p=doc['meshes'][node['mesh']]['primitives'][record['primitive_index']]
            vertices=accessor(doc,bin_data,p['attributes']['POSITION']);indices=accessor(doc,bin_data,p['indices']).reshape(-1)
            if hashlib.sha256(vertices.tobytes()).hexdigest()!=record['position_accessor_sha256'] or hashlib.sha256(indices.tobytes()).hexdigest()!=record['indices_accessor_sha256']:raise ValueError('Source primitive identity changed')
            material=doc.get('materials',[])[p['material']].get('pbrMetallicRoughness',{}).get('baseColorFactor',[.7,.5,.3,1])
            parts.append((record,vertices,indices.reshape(-1,3),material))
        objects[key]=parts;proofs.append({'source':key,'geometry_inventory_sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest(),'source_glb_sha256':proof['source_glb_sha256']})
    kidney=objects['kidney-female-right-v1.3']
    panels=[('Kidney capsule',[p for p in kidney if p[0]['source_label']=='kidney capsule']),
            ('Outer cortex',[p for p in kidney if p[0]['source_label']=='outer cortex of kidney']),
            ('Renal column / hilum',[p for p in kidney if p[0]['source_label'] in ['renal column','hilum of kidney']]),
            ('Pyramids and papillae',[p for p in kidney if p[0]['source_label'] in ['renal pyramid','renal papilla']]),
            ('Collecting-system source asset',objects['ureter-female-right-v1.2']),
            ('Separate pelvis asset (duplicate geometry)',objects['renal-pelvis-female-right-v1.0'])]
    figures=[]
    for name,azimuth in [('source-view-azimuth35',35),('source-view-azimuth215',215)]:
        fig=plt.figure(figsize=(16,13));panel_rows=[]
        for index,(label,parts) in enumerate(panels,1):
            ax=fig.add_subplot(2,3,index,projection='3d')
            # Display-only rigid +90-degree X rotation: original Y up becomes plot Z up.
            rotation=np.array([[1,0,0],[0,0,-1],[0,1,0]],float)
            displayed=[v@rotation.T for _,v,_,_ in parts]
            lo=np.min([v.min(0) for v in displayed],axis=0);hi=np.max([v.max(0) for v in displayed],axis=0)
            extent=np.maximum(hi-lo,.001);pad=extent*.05
            for record,vertices,faces,color in parts:
                # All source triangles, including zero-area triangles, remain in the submitted collection.
                triangles=(vertices@rotation.T)[faces]
                normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);lengths=np.linalg.norm(normals,axis=1)
                unit=np.divide(normals,lengths[:,None],out=np.zeros_like(normals),where=lengths[:,None]>0)
                light=np.array([1,-1,2],float);light/=np.linalg.norm(light);illumination=.65+.35*np.maximum(unit@light,0)
                colours=np.tile(np.asarray(color,float),(len(faces),1));colours[:,:3]*=illumination[:,None]
                ax.add_collection3d(Poly3DCollection(triangles,facecolors=colours,linewidths=0,shade=False))
            ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_zlim(lo[2]-pad[2],hi[2]+pad[2]);ax.set_box_aspect(extent)
            ax.view_init(elev=20,azim=azimuth);ax.set_xlabel('glTF X m',fontsize=8);ax.set_ylabel('−glTF Z m',fontsize=8);ax.set_zlabel('glTF Y m',fontsize=8);ax.tick_params(labelsize=6);ax.locator_params(nbins=4)
            ax.set_title(label+f'\n{len(parts)} source primitives; {sum(len(f) for _,_,f,_ in parts):,} triangles',fontsize=10)
            panel_rows.append({'label':label,'source_nodes':[p[0]['node_name'] for p in parts],'source_triangle_count':sum(len(f) for _,_,f,_ in parts),
                               'display_bounds_metres':[lo.tolist(),hi.tolist()],'display_rigid_rotation':rotation.tolist(),'source_vertex_or_face_values_changed':False})
        fig.suptitle('HRA female right renal reference objects | original declared source coordinates\n'
                     'Source base colours with review lighting; all triangles retained; panel scales differ; no CT registration or clinical approval',fontsize=12)
        fig.subplots_adjust(left=.05,right=.95,bottom=.08,top=.86,hspace=.32,wspace=.12);path=review_root/(name+'.png');fig.savefig(path,dpi=130);plt.close(fig)
        figures.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'azimuth_degrees':azimuth,'elevation_degrees':20,'original_vertical_axis':'y','display_vertical_axis':'z','presentation_is_rigid_axis_rotation':True,'panels':panel_rows})
    (review_root/'source-figure-review.json').write_text(json.dumps({'sources':proofs,'figures':figures,'source_meshes_merged_or_fitted':False,'runtime_promoted':False,'clinical_approval':False,
    'limits':['Original labels/ontology and named reviewers remain source facts; version/semantic discrepancies and open/degenerate surfaces require review.',
              'The separate pelvis mesh repeats geometry already present in the ureter asset; it is not a second anatomical structure.',
              'These are curated reference meshes, not original CT voxels or a matched clinical renal case.']},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--review-root',type=Path,required=True)
    a=p.parse_args();render(a.source_root,a.review_root)
