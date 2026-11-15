"""Compare source polygon boundary incidence against the unmodified export."""
from pathlib import Path
import sys,json,struct,hashlib
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.inspect_fbx import load_fbx,child
root=Path('/tmp/primer-msk-sources');source=root/'z-anatomy-SkeletalSystem100.fbx'
_,nodes=load_fbx(source);objects={n['properties'][0]:n for n in next(x for x in nodes if x['name']=='Objects')['children'] if n['properties']}
geo=objects[251520306];raw=child(geo,'Vertices')['properties'][0];vertices=list(zip(raw[0::3],raw[1::3],raw[2::3]));indices=child(geo,'PolygonVertexIndex')['properties'][0]
record=next(p for p in json.load(open('docs/msk-atlantoaxial-source-review/export-audit.json'))['parts'] if p['name']=='Occipital bone');world=next(p for p in json.load(open(root/'atlantoaxial-staged/world-inventory.json'))['meshes'] if p['name']=='Occipital bone');m=world['world_transform_columns']
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
# Match the export's precision, without changing connectivity or source files.
positions=[tuple(f32(sum(p[j]*m[j][a] for j in range(3))+m[3][a]) for a in range(3)) for p in vertices]
source_edges=Counter();face=[];sizes=Counter()
for x in indices:
 face.append(x if x>=0 else -x-1)
 if x<0:
  sizes[len(face)]+=1
  for a,b in zip(face,face[1:]+face[:1]):source_edges[tuple(sorted((positions[a],positions[b])))]+=1
  face=[]
assert not face
path=Path(record['file']);data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==record['sha256'];_,n,k=struct.unpack('<4sII',data[:12]);v=list(struct.iter_unpack('<fff',data[12:12+n*12]));faces=list(struct.iter_unpack('<III',data[12+n*24:]));export_edges=Counter()
for face in faces:
 for a,b in zip(face,face[1:]+face[:1]):export_edges[tuple(sorted((v[a],v[b])))]+=1
source_bad={e:c for e,c in source_edges.items() if c!=2};export_bad={e:c for e,c in export_edges.items() if c!=2}
assert source_bad==export_bad
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'export_sha256':record['sha256'],'source_geometry_id':251520306,'source_polygon_sizes':dict(sizes),'source_boundary_edges':sum(c==1 for c in source_bad.values()),'source_nonmanifold_edges':sum(c>2 for c in source_bad.values()),'exact_world_endpoint_and_incidence_match':True,'comparison_precision':'Source polygon positions evaluated with fresh source world matrix and rounded to float32, matching export encoding.','defects':[{'world_endpoints_cm':e,'incident_source_polygons':c} for e,c in sorted(source_bad.items())],'conclusion':'All exported abnormal edge incidences are already present at the same endpoints in source polygon connectivity. This pass identifies source topology, not a clinical bone defect.','geometry_changed':False}
Path('docs/msk-atlantoaxial-source-review/occipital-source-topology.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['defects']})
