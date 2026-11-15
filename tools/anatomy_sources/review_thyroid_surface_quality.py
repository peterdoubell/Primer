#!/usr/bin/env python3
"""Inspect all original derived surfaces and their source-field coupling without repair."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np,nibabel as nib
from scipy import sparse,ndimage
from scipy.sparse.csgraph import connected_components
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection,Line3DCollection

def sha(raw):return hashlib.sha256(raw).hexdigest()
def review(source,proof,output):
    original=json.loads((proof/'native-source-review.json').read_text());output.mkdir(parents=True,exist_ok=True);rows=[];surfaces=[]
    for row in original['targets']:
        stem=row['file'].removesuffix('.nii.gz');p=gzip.decompress((proof/(stem+'-positions.f64.gz')).read_bytes());f=gzip.decompress((proof/(stem+'-triangles.u32.gz')).read_bytes())
        if sha(p)!=row['positions_sha256'] or sha(f)!=row['triangles_sha256']:raise ValueError('Original derived geometry changed')
        vertices=np.frombuffer(p,'<f8').reshape(-1,3);faces=np.frombuffer(f,'<u4').reshape(-1,3);triangles=vertices[faces]
        edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);unique,counts=np.unique(edges,axis=0,return_counts=True);boundary=unique[counts==1]
        graph=sparse.coo_matrix((np.ones(len(unique)*2),(np.concatenate([unique[:,0],unique[:,1]]),np.concatenate([unique[:,1],unique[:,0]]))),shape=(len(vertices),len(vertices))).tocsr();component_count,components=connected_components(graph,directed=False);component_faces=components[faces[:,0]]
        if not np.all(components[faces]==component_faces[:,None]):raise ValueError('Faces cross disconnected source components')
        raw=(source/row['file']).read_bytes();file=next(x for x in original['original_files'] if x['file']==row['file'])
        if sha(raw)!=file['source_file_sha256']:raise ValueError('Original mask changed')
        image=nib.load(source/row['file']);mask=np.asarray(image.dataobj);inverse=np.linalg.inv(image.affine);indices=vertices@inverse[:3,:3].T+inverse[:3,3]
        residual=np.abs(ndimage.map_coordinates(mask.astype(float),indices.T,order=1,mode='constant',cval=np.nan)-.5)
        area=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)/2
        rows.append({'file':row['file'],'vertices':len(vertices),'triangles':len(faces),'surface_connected_components':int(component_count),'component_triangle_counts':np.bincount(component_faces).tolist(),'boundary_edges':int(len(boundary)),'nonmanifold_edges':int((counts>2).sum()),'degenerate_triangle_count':int((area==0).sum()),'all_vertices_finite':bool(np.isfinite(vertices).all()),'all_vertices_inside_original_mask_grid':bool(np.all((indices>=0)&(indices<=np.array(mask.shape)-1))), 'original_interpolated_binary_field_residual_max':float(np.nanmax(residual)),'vertices_with_nonzero_field_residual':[{'vertex_index':int(i),'source_voxel_coordinates':indices[i].tolist(),'source_world_coordinates':vertices[i].tolist(),'binary_field_residual':float(residual[i])} for i in np.flatnonzero(residual>1e-6)],'field_residual_is_geometric_distance_or_anatomical_accuracy':False,'source_components_faces_or_boundaries_repaired':False})
        surfaces.append((stem,vertices,faces,boundary))
    fig=plt.figure(figsize=(16,24))
    for i,(stem,vertices,faces,boundary) in enumerate(surfaces):
        ax=fig.add_subplot(4,2,i+1,projection='3d');triangles=vertices[faces];normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);lengths=np.linalg.norm(normals,axis=1);normals=np.divide(normals,lengths[:,None],out=np.zeros_like(normals),where=lengths[:,None]>0);light=np.array([.3,-.5,.8]);light/=np.linalg.norm(light);shade=.35+.65*np.abs(normals@light);colours=shade[:,None]*np.array([168,184,200])/255;ax.add_collection3d(Poly3DCollection(triangles,facecolors=colours,edgecolor='none',linewidth=0));ax.set_proj_type('ortho');ax.tick_params(labelsize=7)
        if len(boundary):ax.add_collection3d(Line3DCollection(vertices[boundary],colors='red',linewidths=1.2))
        low=vertices.min(0);high=vertices.max(0);ax.set_xlim(low[0],high[0]);ax.set_ylim(low[1],high[1]);ax.set_zlim(low[2],high[2]);ax.set_box_aspect(high-low);ax.view_init(elev=20,azim=-65);ax.set_title(stem+'\nAll original faces; red = source boundary openings',fontsize=10,pad=15);ax.set_xlabel('Source x',fontsize=8,labelpad=2);ax.set_ylabel('Source y',fontsize=8,labelpad=2);ax.set_zlabel('Source z',fontsize=8,labelpad=2)
    fig.suptitle('s0358 original annotation surfaces — neutral display colour, not tissue photography',fontsize=14);fig.subplots_adjust(left=.04,right=.96,bottom=.04,top=.94,wspace=.25,hspace=.35);plot=output/'all-source-surface-review.png';fig.savefig(plot,dpi=120);plt.close(fig)
    report={'source_case':'s0358','native_source_review_sha256':sha((proof/'native-source-review.json').read_bytes()),'surface_checks':rows,'rendered_plot_sha256':sha(plot.read_bytes()),'all_source_triangles_rendered_without_decimation':True,'display_colours_are_original_photographic_tissue_colours':False,'independent_anatomical_review_complete':False,'clinical_approval':False,'runtime_promoted':False};(proof/'surface-quality-review.json').write_text(json.dumps(report,indent=2)+'\n');print([(r['file'],r['surface_connected_components'],r['degenerate_triangle_count'],r['original_interpolated_binary_field_residual_max']) for r in rows]);print(plot)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();review(a.source_root,a.proof_dir,a.output_dir)
