"""Inspect source model groups; names alone are not anatomical geometry."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.inspect_fbx import load_fbx
p=Path('/tmp/primer-msk-sources/z-anatomy-Joints100.fbx');_,nodes=load_fbx(p)
objects=next(n for n in nodes if n['name']=='Objects')['children'];models={o['properties'][0]:o for o in objects if o['name']=='Model'};geometries={o['properties'][0]:o for o in objects if o['name']=='Geometry'}
connections=next(n for n in nodes if n['name']=='Connections')['children'];children={};attached={}
for c in connections:
 props=c['properties']
 if len(props)<3 or props[0]!='OO':continue
 child,parent=props[1:3]
 if child in models and parent in models:children.setdefault(parent,[]).append(child)
 if child in geometries and parent in models:attached.setdefault(parent,[]).append(child)
rows=[]
for identifier in [752449604,778841545]:
 node=models[identifier];seen=set();todo=[identifier]
 while todo:
  child=todo.pop()
  if child in seen:continue
  seen.add(child);todo.extend(children.get(child,[]))
 rows.append({'id':identifier,'name':node['properties'][1].split('\0')[0],'node_type':node['properties'][2],'descendant_models':[{'id':k,'name':models[k]['properties'][1].split('\0')[0],'geometry_ids':attached.get(k,[])} for k in sorted(seen-{identifier})],'direct_geometry_ids':attached.get(identifier,[]),'geometry_ids_including_descendants':sorted({g for k in seen for g in attached.get(k,[])})})
cache=json.load(open('/tmp/primer-msk-sources/joints-world-inventory.json'))
broad=[{k:x[k] for k in ['name','source_model_id','bounds']} for x in cache['meshes'] if x['name'] in ['Anterior longitudinal ligament','Posterior longitudinal ligament','Nuchal ligament','Ligamenta flava','Interspinous ligaments']]
result={'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'groups':rows,'other_spinal_objects':broad,'decision':'Named median/lateral atlantoaxial groups cannot be promoted without actual mesh geometry. Generic spinal ligaments are not relabelled as alar, transverse or tectorial anatomy.','limits':'This checks the acquired joint FBX hierarchy, not every possible source file or external dataset. Broad spinal bounds are inventory evidence, not fine structure identification.','runtime_changed':False}
Path('docs/msk-atlantoaxial-source-review/hierarchy.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows,indent=2))
