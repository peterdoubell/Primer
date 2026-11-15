#!/usr/bin/env python3
"""Display all original matching objects and complete foot-labelled objects without fit/cropping/repair."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj

def render(output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    source=json.loads((output/'source-identity-review.json').read_text());parts=[]
    for row in source['objects']:
        if not row['matches_requested_mapping']:continue
        raw=gzip.decompress((output/row['file']).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Original object changed')
        v,n,f,nf=read_obj(raw.decode());parts.append((row,v,f))
    foot=[p for p in parts if any(word in p[0]['requested_is_a_mapping']['source_label'].lower() for word in ['plantar','digital','pedis','tarsal','arcuate','metatarsal'])];fig=plt.figure(figsize=(14,9),layout='constrained');records=[]
    for index,(title,selected) in enumerate([('All 69 identity-matched original collection objects',parts),('All selected foot-labelled original objects',foot)]):
        ax=fig.add_subplot(1,2,index+1,projection='3d');bounds=[]
        for i,(row,v,f) in enumerate(selected):
            ax.add_collection3d(Poly3DCollection(v[f],facecolor=plt.get_cmap('tab20')(i%20),edgecolors='none',alpha=.8,rasterized=True));bounds.extend([v.min(axis=0),v.max(axis=0)])
        lo=np.asarray(bounds).min(axis=0);hi=np.asarray(bounds).max(axis=0);centre=(lo+hi)/2;radius=(hi-lo).max()/2
        ax.set_xlim(centre[0]-radius,centre[0]+radius);ax.set_ylim(centre[1]-radius,centre[1]+radius);ax.set_zlim(centre[2]-radius,centre[2]+radius);ax.set_box_aspect((1,1,1));ax.view_init(elev=12,azim=30);ax.set_proj_type('ortho');ax.set_title(title);ax.set_xlabel('Original X');ax.set_ylabel('Original Y');ax.set_zlabel('Original Z')
        records.append({'panel':index+1,'source_ids':[r['id'] for r,v,f in selected],'source_triangles_displayed':sum(len(f) for r,v,f in selected),'entire_selected_object_triangles_displayed':True})
    fig.suptitle('BodyParts3D 4.3 source collection — original coordinates and complete objects\nFJ2127 identity conflict held; source collection includes adjacent non-leg branches\nAtlas/reference geometry, not acquired MRA, registered patient anatomy or verified complete arterial/tissue coverage',fontsize=11)
    path=output/'original-peripheral-source-context.png';fig.savefig(path,dpi=130);plt.close(fig);proof={'license':'CC BY-SA 2.1 Japan','license_url':'https://creativecommons.org/licenses/by-sa/2.1/jp/','attribution':'BodyParts3D, Database Center for Life Science (DBCLS), source version4.3.','adaptation':'Scientific display with per-object colours in original coordinates; no source geometry changes.','file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'panels':records,'source_geometry_changed_or_refitted':False,'MRI_registration_or_fusion_performed':False,'held_source_ids':['FJ2127'],'closed_objects_prove_wall_volume_or_lumen_connections':False,'clinical_approval':False,'runtime_promoted':False};(output/'source-display-review.json').write_text(json.dumps(proof,indent=2)+'\n');print('All matching objects and complete foot subset rendered; held identity excluded.',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);render(p.parse_args().output)
