from pathlib import Path
import gzip,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import argparse
parser=argparse.ArgumentParser(description='Render original triangle-plane intersections without fitted contours.');parser.add_argument('--review-root',type=Path,default=Path('docs/thoracic-zanatomy-candidate-review-20261013'));args=parser.parse_args();root=args.review_root;manifest=json.loads((root/'manifest.json').read_text());plane=1.30
fig,axes=plt.subplots(1,2,figsize=(12,6));colors=['#4c78a8','#f58518','#54a24b','#e45756','#b279a2','#ff9da6','#9d755d','#72b7b2','#eeca3b'];counts=[]
for i,r in enumerate(manifest['records']):
 o=json.loads(gzip.decompress((root/r['file']).read_bytes()));m=np.asarray(o['matrix_world']);v=np.asarray(o['evaluated_viewport_mesh']['positions_local']);f=np.asarray(o['evaluated_viewport_mesh']['triangle_corner_indices']);v=np.column_stack([v[:,0]*m[k,0]+v[:,1]*m[k,1]+v[:,2]*m[k,2]+m[k,3] for k in range(3)]);tri=v[f];d=tri[:,:,2]-plane;mask=(d.min(1)<0)&(d.max(1)>0);segments=[]
 for points,dist in zip(tri[mask],d[mask]):
  hits=[]
  for a,b in [(0,1),(1,2),(2,0)]:
   if dist[a]*dist[b]<0:hits.append(points[a]+(points[b]-points[a])*(-dist[a]/(dist[b]-dist[a])))
  if len(hits)==2:segments.append(np.asarray(hits)[:,:2]*1000)
 if segments:
  for ax in axes:ax.add_collection(LineCollection(segments,colors=colors[i],linewidths=.8,label=r['name']))
 counts.append({'name':r['name'],'intersected_triangles':int(mask.sum()),'segments':len(segments)})
for ax in axes:ax.set_aspect('equal');ax.grid(alpha=.25);ax.set_xlabel('Source X (mm)');ax.set_ylabel('Source Y (mm)')
axes[0].set_xlim(-145,145);axes[0].set_ylim(-115,100);axes[0].set_title('All preserved source intersections')
axes[1].set_xlim(102,122);axes[1].set_ylim(8,28);axes[1].set_title('Fixed source-coordinate detail; no contours fitted')
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=8)
fig.suptitle('Original Z-Anatomy viewport surfaces at source Z = 1300 mm\nGeometry comparison only; generated pleural shells are not independently sampled tissue layers',fontsize=11)
fig.tight_layout(rect=[0,.14,1,.93]);fig.savefig(root/'source-sections-z1300.png',dpi=150);plt.close(fig)
(root/'section-record.json').write_text(json.dumps({'plane_source_m':plane,'method':'Exact linear triangle-edge intersection; no surface repair, hull completion or source fitting','counts':counts,'clinical_approval':False},indent=2)+'\n')
