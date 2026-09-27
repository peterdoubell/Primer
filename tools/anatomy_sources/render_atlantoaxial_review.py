from pathlib import Path
import json,struct
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
report=json.load(open('docs/msk-atlantoaxial-source-review/export-audit.json'));meshes=[]
for p in report['parts']:
 b=Path(p['file']).read_bytes();_,n,k=struct.unpack('<4sII',b[:12]);v=np.frombuffer(b,dtype='<f4',count=n*3,offset=12).reshape(-1,3)[:,[0,2,1]];f=np.frombuffer(b,dtype='<u4',count=k,offset=12+n*24).reshape(-1,3);meshes.append((p['name'],v,f))
allv=np.concatenate([v for _,v,_ in meshes]);lo=allv.min(0);hi=allv.max(0);center=(lo+hi)/2;radius=max(hi-lo)*.55
fig=plt.figure(figsize=(15,6),facecolor='white');colors=['#5f9ec5','#d9a164','#cfc5b2']
for i,(title,azim) in enumerate([('Anterior',90),('Posterior',-90),('Right lateral',180)]):
 ax=fig.add_subplot(1,3,i+1,projection='3d');ax.set_proj_type('ortho')
 for (name,v,f),color in zip(meshes,colors):ax.add_collection3d(Poly3DCollection(v[f],facecolor=color,edgecolor='#454545',linewidth=.07))
 ax.set(xlim=(center[0]-radius,center[0]+radius),ylim=(center[1]-radius,center[1]+radius),zlim=(center[2]-radius,center[2]+radius));ax.set_box_aspect((1,1,1));ax.view_init(elev=0,azim=azim);ax.set_axis_off();ax.set_title(title)
fig.suptitle('Native source geometry · C1 (blue), C2 (ochre), occipital bone (grey)',fontsize=15)
fig.text(.5,.04,'Z-Anatomy · CC BY-SA 4.0 · 12,059 source triangles · No alignment or repair\nOffline geometry review only; cartilage, ligaments and clinical accuracy unverified',ha='center',fontsize=10)
fig.savefig('docs/msk-atlantoaxial-source-review/native-geometry-review.png',dpi=150,bbox_inches='tight');plt.close(fig)
