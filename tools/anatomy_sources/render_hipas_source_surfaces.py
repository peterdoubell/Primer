#!/usr/bin/env python3
"""Render all retained source triangles in index coordinates, with no clinical transform or geometry repair."""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def render(root,out):
    proof=json.loads((root/'source-surface-review.json').read_text());fig=plt.figure(figsize=(14,8));panels=[]
    for i,row in enumerate(proof['surfaces']):
        vb=(root/row['vertices_file']).read_bytes();fb=(root/row['triangles_file']).read_bytes()
        if hashlib.sha256(vb).hexdigest()!=row['vertices_gzip_sha256'] or hashlib.sha256(fb).hexdigest()!=row['triangles_gzip_sha256']:raise ValueError('Reviewed geometry changed')
        vertices=np.frombuffer(gzip.decompress(vb),dtype='<f8').reshape(-1,3);faces=np.frombuffer(gzip.decompress(fb),dtype='<u4').reshape(-1,3);ax=fig.add_subplot(1,2,i+1,projection='3d');ax.add_collection3d(Poly3DCollection(vertices[faces],facecolors='#25805d' if i==0 else '#ae4444',linewidths=0,edgecolors='none'));low=vertices.min(axis=0);high=vertices.max(axis=0);ax.set_xlim(low[0],high[0]);ax.set_ylim(low[1],high[1]);ax.set_zlim(low[2],high[2]);ax.set_box_aspect(high-low);ax.view_init(elev=15,azim=55);ax.set_xlabel('Source array axis 0');ax.set_ylabel('Source array axis 1');ax.set_zlabel('Source array axis 2');ax.set_title(f"Original {row['source_class']} mask isosurface\n{len(faces):,} triangles / {row['topology']['connected_surface_components']} surface components");panels.append({'source_class':row['source_class'],'all_original_extracted_triangles_rendered':len(faces),'geometry_smoothing_or_decimation':False,'camera_elevation':15,'camera_azimuth':55})
    fig.suptitle('Source mask extraction — array-index coordinates only\nOverlaps, islands, cavities and topology findings retained; not native tissue or clinical approval',fontsize=13);fig.tight_layout(rect=[0,0,1,.9]);fig.savefig(out,dpi=120);plt.close(fig);result={'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_surface_review_sha256':hashlib.sha256((root/'source-surface-review.json').read_bytes()).hexdigest(),'panels':panels,'patient_orientation_or_physical_spacing_applied':False,'clinical_approval':False,'runtime_promoted':False};out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n');print(out)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();render(args.source_root,args.output)
