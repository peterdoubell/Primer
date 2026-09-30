"""Project the unchanged source OPL surface for bounded anatomical review."""
from pathlib import Path
import numpy as np,json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import struct
root=Path(__file__).resolve().parents[2];manifest=json.loads((root/'web/anatomy/msk-atlas/manifest.json').read_text());part=manifest['parts']['za-joints-711785439'];data=(root/'web'/part['file'].removeprefix('/app/')).read_bytes();assert hashlib.sha256(data).hexdigest()==part['sha256'];magic,n,k=struct.unpack('<4sII',data[:12]);assert magic==b'BP3D';native=np.frombuffer(data,'<f4',count=n*3,offset=12).reshape(-1,3).astype(float);points=np.column_stack((-native[:,0],native[:,2],native[:,1]))*10;faces=np.frombuffer(data,'<u4',count=k,offset=12+n*24).reshape(-1,3);center=(points.min(0)+points.max(0))/2;span=max(np.ptp(points,axis=0))*1.12
fig=plt.figure(figsize=(12,6))
for i,(title,azimuth) in enumerate([('Posterior',-90),('Right lateral',0),('Anterior',90)]):
 ax=fig.add_subplot(1,3,i+1,projection='3d');ax.set_proj_type('ortho');ax.add_collection3d(Poly3DCollection(points[faces],facecolors='#d6c89a',edgecolors='#6b6354',linewidths=.12))
 for method,index in [(ax.set_xlim,0),(ax.set_ylim,1),(ax.set_zlim,2)]:method(center[index]-span/2,center[index]+span/2)
 ax.set_box_aspect((1,1,1));ax.view_init(elev=12,azim=azimuth);ax.set_axis_off();ax.set_title(title)
fig.suptitle('Z-Anatomy · source-named right oblique popliteal ligament',fontsize=15)
fig.text(.5,.06,'186 source positions / 368 triangles. Source coordinates preserved; proper native-to-RAS basis change for display.\nClosed artist surface; not a measured tissue volume, attachment footprint or independently approved ligament course.\nZ-Anatomy / BodyParts3D source lineage, CC BY-SA 4.0. Review projection only; no geometry added, smoothing or fitting.',ha='center',fontsize=9)
fig.subplots_adjust(top=.85,bottom=.2,left=.02,right=.98);folder=root/'docs/msk-opl-native-course-review';folder.mkdir(exist_ok=True);out=folder/'source-opl-three-views.png';fig.savefig(out,dpi=170);plt.close(fig);print(out)

report={"source_mesh":part["file"],"source_sha256":part["sha256"],"source_vertices":part["source_vertices"],"triangles":part["triangles"],"source_basis":"Native x-left/y-superior/z-anterior centimetres","display_basis":"RAS millimetres; proper basis change for projection only","image":str(out.relative_to(root)),"image_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"geometry_changed":False,"clinical_approval":False};(folder/"projection-evidence.json").write_text(json.dumps(report,indent=2)+"\n")
