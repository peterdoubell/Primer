"""Inspect each native T1-L5 export without modifying source geometry."""
from pathlib import Path
import sys,json,hashlib,struct,math
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.check_atlantoaxial_topology import topology
ROOT=Path('/tmp/primer-msk-sources');STAGE=ROOT/'thoracolumbar-staged'
fresh=json.loads((STAGE/'world-inventory.json').read_text());cached=json.loads((ROOT/'bones-world-inventory.json').read_text());names=[f'Vertebra T{i}' for i in range(1,13)]+[f'Vertebra L{i}' for i in range(1,6)];rows=[]
for name in names:
    matching=[x for x in fresh['meshes'] if x['name']==name]
    if len(matching)!=1:raise ValueError('Ambiguous source vertebral level')
    p=matching[0];old=next(x for x in cached['meshes'] if x['source_model_id']==p['source_model_id'])
    assert p['source_geometry_id']==old['source_geometry_id'] and p['world_transform_columns']==old['world_transform_columns']
    path=Path(p['file']);b=path.read_bytes();magic,n,k=struct.unpack('<4sII',b[:12]);assert magic==b'BP3D' and len(b)==12+n*24+k*4 and k//3==p['triangles']
    v=list(struct.iter_unpack('<fff',b[12:12+n*12]));f=list(struct.iter_unpack('<III',b[12+n*24:]));assert all(math.isfinite(x) for pnt in v for x in pnt) and all(0<=i<n for face in f for i in face)
    bounds=[[min(pnt[a] for pnt in v) for a in range(3)],[max(pnt[a] for pnt in v) for a in range(3)]]
    error=max(abs(bounds[e][a]-p['bounds'][e][a]) for e in range(2) for a in range(3));assert error<.00002
    check=topology(v,f)
    rows.append({'name':name,'source_model_id':p['source_model_id'],'source_geometry_id':p['source_geometry_id'],'file':str(path),'sha256':hashlib.sha256(b).hexdigest(),'bounds':bounds,'source_bounds':p['bounds'],'maximum_bound_rounding_cm':error,'world_transform_columns':p['world_transform_columns'],**check})
result={'source_sha256':hashlib.sha256((ROOT/'z-anatomy-SkeletalSystem100.fbx').read_bytes()).hexdigest(),'unit_meters':fresh['unit_meters'],'axes':fresh['axes'],'parts':rows,'runtime_promoted':False,'clinical_approval':False,'limits':['Fresh transform evaluation agrees with cache; independent transform-hierarchy derivation is not established.','Topology checks do not establish anatomical accuracy, endplate/facet fidelity or absence of self-intersections.','No alignment, smoothing or mesh repair performed.']}
Path('docs/msk-thoracolumbar-source-review/export-audit.json').write_text(json.dumps(result,indent=2)+'\n')
for p in rows:print(p['name'],p['triangles'],p['boundary_edges'],p['nonmanifold_edges'],p['degenerate_triangles'])
