"""Show all numeric source surfaces and their retained crop edges for review."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection,Line3DCollection
ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/msk-vertebral-substructure-source-review'
def main():
 audit=json.loads((DOC/'lumase-numeric-surface-audit.json').read_text());meshes=[]
 colors=['#f6bd60','#84a59d','#f28482','#b8a5d1','#9fc8df','#dc9b42','#a3bf85']
 for row in audit['parts']:
  path=ROOT/row['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'];mesh=np.load(path);points=mesh['vertices_world_mm'];faces=mesh['faces'];edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);edges.sort(axis=1);unique,counts=np.unique(edges,axis=0,return_counts=True);boundary=unique[counts==1];assert len(boundary)==row['boundary_edges'];meshes.append((row,points,faces,boundary))
 lo=np.min([m[1].min(0) for m in meshes],axis=0);hi=np.max([m[1].max(0) for m in meshes],axis=0);center=(lo+hi)/2;size=max(hi-lo)*1.1
 fig=plt.figure(figsize=(16,8))
 for i,(title,azimuth) in enumerate([('Anterior',90),('Posterior',-90),('Right lateral',0)]):
  ax=fig.add_subplot(1,3,i+1,projection='3d');ax.set_proj_type('ortho')
  for row,points,faces,boundary in meshes:
   ax.add_collection3d(Poly3DCollection(points[faces],facecolors=colors[row['numeric_label']-1],edgecolors='none',linewidths=0))
   if len(boundary):ax.add_collection3d(Line3DCollection(points[boundary],colors='#c00000',linewidths=1.2))
  ax.set_xlim(center[0]-size/2,center[0]+size/2);ax.set_ylim(center[1]-size/2,center[1]+size/2);ax.set_zlim(center[2]-size/2,center[2]+size/2);ax.set_box_aspect((1,1,1));ax.view_init(elev=12,azim=azimuth);ax.set_axis_off();ax.set_title(title+' · 12° elevation',fontsize=13)
 fig.suptitle('LumASe L3 · original numeric-label surfaces',fontsize=18)
 fig.legend(handles=[Patch(facecolor=c,label='Label '+str(i+1)) for i,c in enumerate(colors)]+[Patch(facecolor='#c00000',label='Open crop edges')],loc='lower center',bbox_to_anchor=(.5,.12),ncol=8)
 fig.text(.5,.045,'238,484 triangles; all generated positions and topology retained. Native RAS coordinates; no cross-case registration.\nNo padding, closure caps, smoothing, decimation or mask edits. Numeric-to-anatomical meanings remain unverified.\nLiu et al. (2022), LumASe, doi:10.5281/zenodo.7181338, CC BY 4.0. Adaptation: isosurface extraction and review projections.\nBasic topology checks do not establish biological boundary accuracy, complete structures, normality or clinical approval.',ha='center',fontsize=10)
 fig.subplots_adjust(top=.86,bottom=.22,left=.02,right=.98,wspace=.02);out=DOC/'lumase-numeric-surfaces.png';fig.savefig(out,dpi=160);plt.close(fig)
 (DOC/'lumase-surface-rendering.json').write_text(json.dumps({'image':str(out.relative_to(ROOT)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_audit_sha256':hashlib.sha256((DOC/'lumase-numeric-surface-audit.json').read_bytes()).hexdigest(),'triangle_count':sum(m[0]['triangles'] for m in meshes),'open_crop_edges':sum(m[0]['boundary_edges'] for m in meshes),'all_source_surfaces_rendered':True,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')
 print('Rendered all seven source surfaces in three views, retaining open crop edges.')
if __name__=='__main__':main()
