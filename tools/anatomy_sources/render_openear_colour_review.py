#!/usr/bin/env python3
"""Preview original anatomical surfaces with reconstructed source samples, not approved tissue textures."""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from tools.anatomy_sources.review_openear_ZETA_geometry import ply

def render(root,proof_dir,out):
    p=proof_dir/'ZETA-source-colour-sample-review.json';r=json.loads(p.read_text());rows=[m for m in r['models'] if Path(m['member']).name!='Bone.ply'];fig=plt.figure(figsize=(15,19));views=[]
    for i,row in enumerate(rows):
        raw=(root/'ZETA-selected'/Path(row['member']).name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['source_mesh_sha256']:raise ValueError('Original source geometry changed')
        vertices,faces,_=ply(raw);rgb_path=root/'ZETA-colour-samples'/row['RGB_file'];valid_path=root/'ZETA-colour-samples'/row['support_file']
        if hashlib.sha256(rgb_path.read_bytes()).hexdigest()!=row['RGB_gzip_sha256'] or hashlib.sha256(valid_path.read_bytes()).hexdigest()!=row['support_gzip_sha256']:raise ValueError('Reviewed source samples changed')
        rgb=np.frombuffer(gzip.decompress(rgb_path.read_bytes()),dtype='u1').reshape(-1,3);valid=np.frombuffer(gzip.decompress(valid_path.read_bytes()),dtype='u1').astype(bool)
        colors=rgb[faces].mean(axis=1)/255.;whole=valid[faces].all(1);colors[~whole]=128/255.
        ax=fig.add_subplot(4,3,i+1,projection='3d');ax.add_collection3d(Poly3DCollection(vertices[faces],facecolors=colors,edgecolors='none',linewidths=0));low=vertices.min(0);high=vertices.max(0);ax.set_xlim(low[0],high[0]);ax.set_ylim(low[1],high[1]);ax.set_zlim(low[2],high[2]);ax.set_box_aspect(high-low);ax.view_init(elev=20,azim=-65);ax.set_axis_off();title=Path(row['member']).stem.split('_',1)[-1];ax.set_title(title+'\n'+f"{len(faces):,} original triangles; {int((~whole).sum()):,} neutral faces",fontsize=10)
        views.append({'source_member':row['member'],'all_original_triangles_displayed':len(faces),'whole_face_neutral_rule_applied':True,'display_triangle_RGB':'Mean of original source-reconstructed vertex samples; no extra lighting or colour enhancement','camera_elevation':20,'camera_azimuth':-65})
    fig.suptitle('OpenEar ZETA original surfaces — offline reconstructed-colour review\nPrepared cadaver specimen; grey means unsupported domain, not tissue colour\nCoordinate/photographic tissue validity and clinical anatomy still unapproved; full Bone geometry remains separately retained',fontsize=13);fig.subplots_adjust(top=.88,bottom=.04,hspace=.12,wspace=.05);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=120,bbox_inches='tight');plt.close(fig)
    proof={'source_sample_review_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'views':views,
           'Bone_full_mesh_geometry_retained_in_source_package_but_not_rendered_in_this_small_structure_sheet':True,
           'full_Bone_surface_visual_or_clinical_approval_granted':False,'source_geometry_modified':False,'clinical_approval':False,'runtime_promoted':False}
    (proof_dir/'ZETA-offline-colour-display-review.json').write_text(json.dumps(proof,indent=2)+'\n');print(out)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.source_root,a.proof_dir,a.output)
