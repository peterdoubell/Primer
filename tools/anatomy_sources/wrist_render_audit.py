#!/usr/bin/env python3
"""Visual and attachment QA for the downloaded forearm candidate only."""
import csv,hashlib,json,pathlib
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ROOT=pathlib.Path('/tmp/primer-msk-sources/wrist-next');BASE=ROOT/'hamze-2020/forearm_model'

def mesh(name,kind):return trimesh.load(BASE/kind/name,force='mesh',process=False)

def weld(m):
 vertices,ix=np.unique(m.vertices,axis=0,return_inverse=True)
 return trimesh.Trimesh(vertices=vertices,faces=ix[m.faces],process=False)

items={};notes=[]
for category in ['bones','ligaments','discs']:
 for path in (BASE/category).iterdir():
  if path.suffix not in ['.obj','.ply']:continue
  obj=weld(trimesh.load(path,force='mesh',process=False));items[path.stem]=obj
  normals=np.cross(obj.triangles[:,1]-obj.triangles[:,0],obj.triangles[:,2]-obj.triangles[:,0])
  notes.append({'name':path.stem,'category':category,'exact_unique_positions':len(obj.vertices),'triangles':len(obj.faces),'watertight_after_exact_weld':bool(obj.is_watertight),'consistent_winding':bool(obj.is_winding_consistent),'zero_area_faces':int((np.linalg.norm(normals,axis=1)==0).sum()),'bounds':obj.bounds.tolist()})
attachments=[]
for path in (BASE/'landmarks').glob('*.csv'):
 tissue=path.stem.removeprefix('IOM_landmarks_')
 with path.open() as stream:
  for row in csv.DictReader(stream):
   row={k.strip():v.strip() for k,v in row.items()};point=np.array([float(row[a]) for a in ['X','Y','Z']])
   candidates=[]
   for name,obj in items.items():
    if (BASE/'bones'/(name+'.obj')).exists():candidates.append((float(np.min(np.linalg.norm(obj.vertices-point,axis=1))),name))
   distance,bone=min(candidates)
   distance_tissue=float(np.min(np.linalg.norm(items[tissue].vertices-point,axis=1))) if tissue in items else None
   attachments.append({'landmark':row['name'],'mesh':tissue,'nearest_bone_vertex':bone,'nearest_bone_vertex_distance_source_units':distance,'nearest_tissue_vertex_distance_source_units':distance_tissue,'mesh_present':tissue in items})
report={'note':'Distances are nearest-vertex checks in unconverted source coordinates, not distances to a validated anatomical footprint or proof of clinical fidelity.','meshes':notes,'landmark_checks':attachments}
(ROOT/'hamze-geometry-qa.json').write_text(json.dumps(report,indent=2)+'\n')
fig=plt.figure(figsize=(15,5),facecolor='white')
for index,(title,names) in enumerate([
 ('Downloaded TFCC region with bone context',['Radius','Ulna','Lunate','Triquetrum','Scaphoid','disc_pt609','DRUL1','DRUL2','PRUL1','PRUL2']),
 ('Disc and radius/ulna cartilage surfaces',['disc_pt609','radius_cartilage_pt609','ulna_cartilage_pt609']),
 ('Dorsal/palmar RUL branches + disc',['DRUL1','DRUL2','PRUL1','PRUL2','disc_pt609'])
]):
 ax=fig.add_subplot(1,3,index+1,projection='3d');box=[]
 for name in names:
  obj=items[name];bone=(BASE/'bones'/(name+'.obj')).exists();color='#c8c8bf' if bone else '#35a4a4' if name.endswith('pt609') else '#cf9538'
  # The native source frame is only viewed, never anatomically re-registered.
  tris=obj.triangles
  if index==0:
   center=np.array([-1.,142.,-167.]);half=np.array([22.,25.,22.]);keep=((tris>=center-half)&(tris<=center+half)).all(2).any(1);tris=tris[keep]
  else:box.append(obj.vertices)
  ax.add_collection3d(Poly3DCollection(tris,facecolor=color,edgecolor='#2c7777' if name=='disc_pt609' else 'none',linewidth=.1,alpha=.16 if bone else .8))
 if index!=0:
  points=np.concatenate(box);center=(points.min(0)+points.max(0))/2;half=np.repeat(max(np.ptp(points,axis=0))*.62,3)
 ax.set_xlim(center[0]-half[0],center[0]+half[0]);ax.set_ylim(center[1]-half[1],center[1]+half[1]);ax.set_zlim(center[2]-half[2],center[2]+half[2]);ax.set_box_aspect(half);ax.view_init(elev=25,azim=40);ax.set_axis_off();ax.set_title(title,fontsize=11)
fig.suptitle('Hamze et al. 2020 forearm source — geometric QA, not clinical approval',fontsize=14)
fig.text(.5,.02,'Source coordinates retained. Teal: disc/cartilage · Gold: ligament surfaces · Gray: bones. Missing SL/LT geometry remains unresolved.',ha='center',fontsize=10);fig.tight_layout(rect=(0,.06,1,.94));fig.savefig(ROOT/'hamze-wrist-source-qa.png',dpi=150)
print('Inspected',len(notes),'tissue meshes and',len(attachments),'attachment landmarks; saved QA figure')
print('Disc',next(n for n in notes if n['name']=='disc_pt609'))
print('Missing tissue objects:',sorted({a['mesh'] for a in attachments if not a['mesh_present']}))
print('Attachment nearest-bone distance min/max',min(a['nearest_bone_vertex_distance_source_units'] for a in attachments),max(a['nearest_bone_vertex_distance_source_units'] for a in attachments))
