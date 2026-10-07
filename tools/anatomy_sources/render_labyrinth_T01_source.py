#!/usr/bin/env python3
"""Inspect original PLY/mask disagreements on original CT and micro-CT planes; never fit the mesh."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy.ndimage import map_coordinates
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from tools.anatomy_sources.render_nasalseg_surface_alignment import plane_segments


def render(root,proof_dir,out):
    proof_path=proof_dir/'T01-original-source-review.json';proof=json.loads(proof_path.read_text());files={r['member']:r for r in proof['files']}
    def original(member):
        p=root/member;raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=files[member]['sha256']:raise ValueError('Original source member changed')
        return p,raw
    _,raw=original('T01/CT/T01_CT_SURF.ply');header,body=raw.split(b'end_header\n',1);lines=body.decode().splitlines();n=files['T01/CT/T01_CT_SURF.ply']['vertices'];k=files['T01/CT/T01_CT_SURF.ply']['triangles'];vertices=np.array([[float(x) for x in line.split()] for line in lines[:n]]);faces=np.array([[int(x) for x in line.split()[1:4]] for line in lines[n:n+k]])
    out.mkdir(parents=True,exist_ok=True);fig=plt.figure(figsize=(14,7));surface_views=[]
    for i,az in enumerate([-65,115]):
        ax=fig.add_subplot(1,2,i+1,projection='3d');tri=vertices[faces];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normal,axis=1);normal/=length[:,None];shade=.35+.65*LightSource(azdeg=315,altdeg=45).shade_normals(normal)
        ax.add_collection3d(Poly3DCollection(tri,facecolors=shade[:,None]*np.array([.3,.72,.78]),edgecolors='none',linewidths=0))
        low=vertices.min(0);high=vertices.max(0);ax.set_xlim(low[0],high[0]);ax.set_ylim(low[1],high[1]);ax.set_zlim(low[2],high[2]);ax.set_box_aspect(high-low);ax.view_init(elev=20,azim=az)
        ax.set_xlabel('Original PLY x');ax.set_ylabel('Original PLY y');ax.set_zlabel('Original PLY z');ax.set_title(f'Original source mesh · azimuth {az}°\n{k:,} triangles, no source geometry changes')
        surface_views.append({'all_original_triangles_rendered':k,'elevation':20,'azimuth':az,'triangle_normal_display_illumination_only':True})
    fig.suptitle('T01 original bony-labyrinth surface\nBoth archive mesh files are identical; not independent CT/micro-CT models',fontsize=13);fig.tight_layout(rect=[0,0,.92,.88]);surf=out/'T01-original-surface.png';fig.savefig(surf,dpi=120,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(14,17));reviews=[]
    for col,mode in enumerate(['CT','uCT']):
        image_path,_=original(f'T01/{mode}/T01_{mode}_RAW.nii');mask_path,_=original(f'T01/{mode}/T01_{mode}_LABELS.nii');im=nib.load(image_path);lab=nib.load(mask_path);image=im.dataobj.get_unscaled();mask=lab.dataobj.get_unscaled();A=im.affine;B=lab.affine
        # Original pixel grid. Keep the source mask header discrepancy explicit;
        # mask contours are its original same-index samples, not a fitted registration.
        inverse=np.linalg.inv(A);index_vertices=vertices@inverse[:3,:3].T+inverse[:3,3];inside=((index_vertices>=0)&(index_vertices<=np.array(image.shape)-1)).all(1)
        values=map_coordinates(mask.astype(float),(vertices@np.linalg.inv(B)[:3,:3].T+np.linalg.inv(B)[:3,3]).T,order=1,mode='constant',cval=np.nan)
        residual=np.abs(values-.5);centre=[int(np.median(v)) for v in np.where(mask>0)];pitch=np.linalg.norm(A[:3,:3],axis=0);window=np.percentile(image,[5,99.5]).tolist();planes=[]
        for axis,index in enumerate(centre):
            others=[a for a in range(3) if a!=axis];ct=np.take(image,index,axis=axis).T;labels=np.take(mask,index,axis=axis).T;ax=axes[axis,col];ax.imshow(ct,cmap='gray',origin='lower',vmin=window[0],vmax=window[1],aspect=pitch[others[1]]/pitch[others[0]])
            if labels.any():ax.contour(labels,levels=[.5],colors=['#33c5b7'],linewidths=1)
            segments,coplanar=plane_segments(index_vertices,faces,axis,index)
            if len(segments):ax.add_collection(LineCollection(segments[:,:,others],colors='#ffb45a',linewidths=.9))
            ax.set_title(f'{mode} original axis {axis}, index {index}\nTeal: original mask; orange: actual PLY intersection');ax.set_xlabel('Original in-plane sample index');ax.set_ylabel('Original in-plane sample index')
            planes.append({'array_axis_xyz':axis,'source_index':index,'mesh_plane_segments':len(segments),'plane_coincident_faces':coplanar,'display_aspect':float(pitch[others[1]]/pitch[others[0]])})
        reviews.append({'mode':mode,'original_image_affine':A.tolist(),'original_mask_affine':B.tolist(),'source_grid_qforms_made_equal':False,
            'source_window_percentiles':[5,99.5],'display_window_source_units':window,'original_mesh_vertices_outside_image_bounds':int((~inside).sum()),
            'mesh_vertex_binary_field_residual_quantiles_50_95_100':np.nanquantile(residual,[.5,.95,1]).tolist(),
            'binary_field_residual_is_anatomical_distance_or_accuracy':False,'planes':planes})
    fig.suptitle('T01 original surface versus source labels on CT and micro-CT\nSource PLY is not assumed to equal the binary 0.5 interface; differences retained\nNo source repair, fitted registration or resampling; display units are not verified HU',fontsize=13);fig.tight_layout(rect=[0,0,1,.91]);context=out/'T01-original-mask-surface-planes.png';fig.savefig(context,dpi=120,bbox_inches='tight');plt.close(fig)
    result={'case':'T01','source_review_sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest(),'source_PLY_sha256':files['T01/CT/T01_CT_SURF.ply']['sha256'],
        'figures':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [surf,context]],'source_views':surface_views,'source_field_reviews':reviews,
        'original_surface_equals_original_binary_label_interface_verified':False,'source_mesh_registration_resampling_smoothing_repair_or_decimation_applied':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (proof_dir/'T01-source-display-review.json').write_text(json.dumps(result,indent=2)+'\n');print(surf);print(context)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.source_root,a.proof_dir,a.output)
