#!/usr/bin/env python3
"""Show exact original digital-artery double-face components without deleting or expanding them."""
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
    source=json.loads((output/'source-identity-review.json').read_text());lookup={r['id']:r for r in source['objects']};findings=json.loads((output/'source-contact-findings-review.json').read_text());fig=plt.figure(figsize=(12,10),layout='constrained');records=[]
    for row_index,identifier in enumerate(['FJ2095','FJ2204']):
        raw=gzip.decompress((output/lookup[identifier]['file']).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=lookup[identifier]['sha256']:raise ValueError('Original source differs')
        v,n,f,nf=read_obj(raw.decode());selected=[r for r in findings['within_object_findings'] if r['source_id']==identifier];face_ids=sorted({i for r in selected for i in r['source_face_indices']});points=v[f[face_ids]].reshape(-1,3)
        for col in [0,1]:
            ax=fig.add_subplot(2,2,row_index*2+col+1,projection='3d')
            if col==0:ax.add_collection3d(Poly3DCollection(v[f],facecolor='#72a7bc',edgecolors='none',alpha=.6,rasterized=True));bounds=v
            else:bounds=points
            ax.add_collection3d(Poly3DCollection(v[f[face_ids]],facecolor='#ef4c53',edgecolors='#75242b',alpha=.9));lo=bounds.min(0);hi=bounds.max(0);centre=(lo+hi)/2;radius=max(float((hi-lo).max()/2),.05)
            ax.set_xlim(centre[0]-radius,centre[0]+radius);ax.set_ylim(centre[1]-radius,centre[1]+radius);ax.set_zlim(centre[2]-radius,centre[2]+radius);ax.set_box_aspect((1,1,1));ax.set_proj_type('ortho');ax.view_init(elev=18,azim=45);ax.set_xlabel('Original X');ax.set_ylabel('Original Y');ax.set_zlabel('Original Z');ax.set_title(identifier+(' · complete original object' if col==0 else ' · exact isolated double-face components'))
        records.append({'source_id':identifier,'source_sha256':lookup[identifier]['sha256'],'source_triangles_displayed_in_full_view':len(f),'highlighted_original_face_indices':face_ids,'original_coordinates_changed':False})
    fig.suptitle('Exact original digital-artery source findings\nRed: isolated, opposite-winding coincident face pairs; all source faces retained\nClosed edge counts do not establish 3D tissue/lumen or clinical anatomical fidelity',fontsize=12)
    path=output/'original-digital-double-face-context.png';fig.savefig(path,dpi=130);plt.close(fig);proof={'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sources':records,'source_geometry_changed_or_defects_removed':False,'clinical_approval':False,'runtime_promoted':False,'license':'CC BY-SA 2.1 Japan','license_url':'https://creativecommons.org/licenses/by-sa/2.1/jp/','attribution':'BodyParts3D, Database Center for Life Science, version4.3.','adaptation':'Scientific display and highlighting of original source faces; source geometry unchanged.'};(output/'digital-contact-display-review.json').write_text(json.dumps(proof,indent=2)+'\n');print('Original digital double-face components displayed without source edits.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);render(p.parse_args().output)
