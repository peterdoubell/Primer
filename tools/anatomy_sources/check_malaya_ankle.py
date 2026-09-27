#!/usr/bin/env python3
"""Independent, non-mutating source audit of the staged Malaya ankle set.

Checks original ZIP members as well as staged source copies; verifies every
rendered facet/normal and inventories topology without repairing any component.
Optional --render creates audit images in /tmp only.
"""
import argparse, collections, hashlib, json, pathlib, struct, zipfile
import numpy as np

ROOT=pathlib.Path('/tmp/primer-msk-sources/high-fidelity')
OUT=ROOT/'malaya-ankle'
EXPECTED={
 'Bone_Tibia','Bone_Fibula','Bone_Talus','Bone_Calcaneus','Bone_Navicular','Bone_Cuboid',
 'Bone_Medial Cuneiform','Bone_Intermediate Cuneiform','Bone_Lateral Cuneiform',
 'Tendon_Archilles','Muscle_Tibialis Anterior','Muscle_Tibialis Posterior',
 'Muscle_Peroneus Longus','Muscle_Flexor Digitorum Longus','Muscle_Flexor Hallucis Longus',
 'Muscle_Extensor Digitorum Longus','Muscle_Extensor Hallucis Longus',
 'Muscle_Gastrocnemius Medial','Muscle_Gastrocnemius Lateral','Muscle_Soleus',
}

def read_binary(path):
 raw=pathlib.Path(path).read_bytes();assert raw[:4]==b'BP3D'
 nv,ni=struct.unpack_from('<II',raw,4);assert ni%3==0 and len(raw)==12+nv*24+ni*4
 p=np.frombuffer(raw,dtype='<f4',offset=12,count=nv*3).reshape(-1,3)
 n=np.frombuffer(raw,dtype='<f4',offset=12+nv*12,count=nv*3).reshape(-1,3)
 i=np.frombuffer(raw,dtype='<u4',offset=12+nv*24,count=ni).reshape(-1,3)
 assert i.max()<nv
 return raw,p,n,i

def read_source(raw):
 assert raw[:80].startswith(b'3D Slicer output. SPACE=LPS')
 count=struct.unpack_from('<I',raw,80)[0];assert len(raw)==84+50*count
 dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
 a=np.frombuffer(raw,dtype=dtype,count=count,offset=84)
 return a['vertices'],a['normal']

def topology(tri):
 v,ids=np.unique(tri.reshape(-1,3),axis=0,return_inverse=True);faces=ids.reshape(-1,3)
 edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
 edges,counts=np.unique(edges,axis=0,return_counts=True)
 parents=list(range(len(v)))
 def find(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 for a,b in edges:
  ra,rb=find(int(a)),find(int(b))
  if ra!=rb:parents[rb]=ra
 groups=collections.defaultdict(list)
 for i,f in enumerate(faces):groups[find(int(f[0]))].append(i)
 components=[]
 for face_ids in groups.values():
  ids=np.array(face_ids);t=tri[ids].astype('f8');verts=np.unique(t.reshape(-1,3),axis=0)
  twice_area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
  component_faces=faces[ids]
  oriented=np.concatenate([component_faces[:,[0,1]],component_faces[:,[1,2]],component_faces[:,[2,0]]])
  edge_key=np.sort(oriented,axis=1);_,inverse,edge_counts=np.unique(edge_key,axis=0,return_inverse=True,return_counts=True)
  balances=np.bincount(inverse,weights=np.where(oriented[:,0]<oriented[:,1],1,-1))
  components.append({'triangles':len(ids),'first_render_facet':int(ids.min()),'bounds':[verts.min(0).tolist(),verts.max(0).tolist()],'dimensions_mm':np.ptp(verts,axis=0).tolist(),'surface_area_mm2':float(twice_area.sum()/2),'minimum_twice_triangle_area_mm2':float(twice_area.min()),'exact_zero_area_triangles':int((twice_area==0).sum()),'boundary_edges':int((edge_counts==1).sum()),'non_manifold_edges':int((edge_counts>2).sum()),'watertight_component':bool(np.all(edge_counts==2)),'opposed_edge_directions_where_paired':bool(np.all(balances[edge_counts==2]==0)),'face_indices':ids.tolist()})
 components.sort(key=lambda c:c['triangles'],reverse=True)
 return {'exact_unique_positions':len(v),'boundary_edges':int((counts==1).sum()),'non_manifold_edges':int((counts>2).sum()),'maximum_edge_incidence':int(counts.max()),'non_manifold_edge_bounds':None if not np.any(counts>2) else [v[edges[counts>2]].reshape(-1,3).min(0).tolist(),v[edges[counts>2]].reshape(-1,3).max(0).tolist()],'component_count':len(components),'components':components}

def run():
 manifest_bytes=(OUT/'manifest.json').read_bytes();m=json.loads(manifest_bytes)
 assert set(p['source_name'] for p in m['parts'].values())==EXPECTED
 assert m['coordinate_system']['basis']=='LPS' and m['coordinate_system']['units']=='millimeters'
 assert not m['clinical_image_pair']['available']
 assert 'paired_T2_FS_exported_grid_mm' not in m['sampling_limits']
 assert 'local_image' not in m['clinical_image_pair']
 archive=ROOT/'um-final-model-stl.zip';assert hashlib.sha256(archive.read_bytes()).hexdigest()==m['source_archive_sha256']
 evidence=pathlib.Path(m['omission_evidence']['file']).read_bytes();evidence_sha=hashlib.sha256(evidence).hexdigest();assert evidence_sha==m['omission_evidence']['sha256']
 results=[];geometry={}
 with zipfile.ZipFile(archive) as z:
  for p in m['parts'].values():
   source=z.read(p['source_member']);assert hashlib.sha256(source).hexdigest()==p['source_sha256']
   assert pathlib.Path(p['stl_file']).read_bytes()==source
   tri,n=read_source(source);assert len(tri)==p['source_triangles']
   q=tri.astype('f8');zero=np.all(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0])==0,axis=1)
   repeated=np.all(q[:,0]==q[:,1],1)|np.all(q[:,1]==q[:,2],1)|np.all(q[:,0]==q[:,2],1)
   eligible=np.flatnonzero(zero&repeated).tolist();assert eligible==p['omitted_source_facet_indices']
   keep=~(zero&repeated);render_tri=tri[keep];render_n=n[keep]
   raw,positions,normals,ix=read_binary(p['file'])
   assert hashlib.sha256(raw).hexdigest()==p['sha256'] and len(raw)==p['bytes']
   assert len(ix)==p['triangles'] and len(positions)==p['export_vertices']
   assert np.array_equal(positions[ix],render_tri)
   assert np.array_equal(normals[ix],np.repeat(render_n[:,None,:],3,axis=1))
   assert np.isfinite(positions).all() and np.isfinite(normals).all()
   bounds=np.array([positions[ix].min((0,1)),positions[ix].max((0,1))]);assert np.array_equal(bounds,np.array(p['bounds'],dtype='f4'))
   assert p['omission_evidence_sha256']==evidence_sha and p['regions']==['ankle']
   assert p['world_transform_columns']==[[1,0,0],[0,1,0],[0,0,1],[0,0,0]]
   top=topology(render_tri);assert sorted((c['triangles'] for c in top['components']),reverse=True)==p['component_triangles']
   results.append({'id':p['id'],'name':p['name'],'source_name':p['source_name'],'source_triangles':len(tri),'render_triangles':len(ix),'omitted_exact_empty_facets':len(eligible),'retained_source_positions_exact':True,'retained_source_normals_exact':True,'bounds':bounds.tolist(),**top})
   geometry[p['source_name']]=(render_tri,top)
 assert sum(r['omitted_exact_empty_facets'] for r in results)==m['omission_evidence']['total_facets']
 result={'status':'technical source audit; not clinical certification','objects':len(results),'source_triangles':sum(r['source_triangles'] for r in results),'render_triangles':sum(r['render_triangles'] for r in results),'omitted_exact_empty_facets':sum(r['omitted_exact_empty_facets'] for r in results),'all_retained_facets_and_normals_exact':True,'manifest_sha256_at_audit':hashlib.sha256(manifest_bytes).hexdigest(),'no_geometry_changed_by_audit':True,'records':results}
 path=OUT/'independent-source-audit.json';path.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='records'}))
 for r in results:
  if r['component_count']>1 or r['non_manifold_edges'] or r['boundary_edges']:
   print(r['name'],'components',[c['triangles'] for c in r['components']],'boundary edges',r['boundary_edges'],'nonmanifold edges',r['non_manifold_edges'])
 return m,result,geometry

def render(m,result,geometry):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from mpl_toolkits.mplot3d.art3d import Poly3DCollection
 def draw(ax,name,color,alpha=1,box=None,component=None,wire=False):
  tri,top=geometry[name]
  if component is not None:tri=tri[np.array(top['components'][component]['face_indices'])]
  if box is not None:tri=tri[((tri>=box[0])&(tri<=box[1])).all(2).any(1)]
  if len(tri):ax.add_collection3d(Poly3DCollection(tri,facecolor=color,edgecolor='#46383e' if wire else 'none',linewidth=.7 if wire else 0,alpha=alpha,zsort='average'))
 def frame(ax,box,elev=16,azim=10):
  lo,hi=np.array(box);ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect(hi-lo);ax.view_init(elev=elev,azim=azim);ax.set_axis_off()
 ach=next(r for r in result['records'] if r['source_name']=='Tendon_Archilles')
 box=np.array(ach['bounds']);box[0]-=[18,20,12];box[1]+=[18,15,12]
 distal=np.array([[-120,-15,-785],[-15,125,-630]])
 fig=plt.figure(figsize=(15,7),facecolor='white');a=fig.add_subplot(1,3,1,projection='3d');b=fig.add_subplot(1,3,2,projection='3d');c=fig.add_subplot(1,3,3,projection='3d')
 for ax,view in [(a,box),(b,distal)]:
  for name in ['Bone_Tibia','Bone_Fibula','Bone_Calcaneus','Bone_Talus','Bone_Navicular','Bone_Cuboid']:draw(ax,name,'#b8b6ab',.18,view)
  draw(ax,'Tendon_Archilles','#bc692e',.95,view)
 frame(a,box,18,15);frame(b,distal,18,10)
 a.set_title('Full source Achilles with lower-leg context',fontsize=11);b.set_title('Distal tendon and calcaneus\nNative source frame; no fitted transform',fontsize=11)
 draw(c,'Tendon_Archilles','#ab4c88',1,component=1,wire=True);small=ach['components'][1];sb=np.array(small['bounds']);center=sb.mean(0);half=max(sb[1]-sb[0])*.65;frame(c,[center-half,center+half],25,40)
 c.set_title('Retained 12-facet nonzero component\nMagnified independently for topology review',fontsize=11)
 fig.suptitle('Malaya ankle source audit — source shapes retained, anatomical adequacy not certified',fontsize=14)
 fig.text(.5,.025,'Orange: Achilles · Gray: bone context · Purple: separate nonzero source component\nNo small nonzero component is removed; source sampling is approximately 1.15 × 1.15 × 1.2 mm.',ha='center',fontsize=10)
 fig.tight_layout(rect=(0,.07,1,.94));fig.savefig(OUT/'independent-achilles-audit.png',dpi=150)
 # Muscle units: show their actual extent relative to ankle, without inventing tendons.
 fig=plt.figure(figsize=(14,6),facecolor='white')
 for i,name in enumerate(['Muscle_Tibialis Anterior','Muscle_Tibialis Posterior','Muscle_Flexor Digitorum Longus']):
  ax=fig.add_subplot(1,3,i+1,projection='3d');tri,top=geometry[name];bb=np.array([tri.min((0,1)),tri.max((0,1))]);bb[0]-=4;bb[1]+=4
  draw(ax,name,'#a5534b',.75)
  for j in range(1,len(top['components'])):draw(ax,name,'#693da0',1,component=j,wire=True)
  frame(ax,bb,15,15);ax.set_title(name.replace('Muscle_','')+' source unit\n'+str(len(top['components']))+' retained components',fontsize=11)
 fig.text(.5,.02,'Whole source muscle units are not separately delineated distal tendons or sheaths. Small nonzero components remain visible in source data.',ha='center',fontsize=10);fig.tight_layout(rect=(0,.07,1,.95));fig.savefig(OUT/'independent-muscle-units-audit.png',dpi=150)
 print('Saved independent ankle QA images in',OUT)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');args=parser.parse_args()
 m,result,geometry=run()
 if args.render:render(m,result,geometry)
