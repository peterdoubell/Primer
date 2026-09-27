"""Render the unchanged CT-mask isosurface for offline source inspection."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
out=Path('docs/msk-verse-source-review');audit=json.loads((out/'t8-surface-audit.json').read_text());path=Path(audit['surface_file']);assert hashlib.sha256(path.read_bytes()).hexdigest()==audit['surface_sha256'];data=np.load(path);v=data['vertices_world_mm'];f=data['faces'];tri=v[f];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1)[:,None];light=np.array([.3,.7,.5]);light/=np.linalg.norm(light);shade=.5+.45*np.abs(n@light);colors=shade[:,None]*np.array([.78,.72,.6])[None,:]
lo=v.min(0);hi=v.max(0);center=(lo+hi)/2;r=max(hi-lo)*.55
fig=plt.figure(figsize=(14,5),facecolor='white')
for i,(title,azim) in enumerate([('Anterior · camera +A',90),('Posterior · camera −A',-90),('Right lateral · camera +R',0)]):
 ax=fig.add_subplot(1,3,i+1,projection='3d');ax.set_proj_type('ortho');ax.add_collection3d(Poly3DCollection(tri,facecolors=colors,edgecolor='#655f53',linewidth=.035));ax.set(xlim=(center[0]-r,center[0]+r),ylim=(center[1]-r,center[1]+r),zlim=(center[2]-r,center[2]+r));ax.set_box_aspect((1,1,1));ax.view_init(elev=0,azim=azim);ax.set_axis_off();ax.set_title(title)
fig.suptitle('VerSe sub-verse521 · T8 source-label surface · 38,516 triangles',fontsize=14)
fig.text(.5,.025,'Original CT RAS world coordinates · no smoothing, filling, decimation or component removal\nDerived review artifact · CC BY-SA 4.0 · segmentation and clinical accuracy unverified',ha='center',fontsize=10)
fig.savefig(out/'t8-surface-review.png',dpi=160,bbox_inches='tight');plt.close(fig)
