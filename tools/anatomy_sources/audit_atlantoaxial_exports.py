"""Compare fresh ufbx bone exports with independently decoded source vertices."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.inspect_fbx import load_fbx,child
ROOT=Path('/tmp/primer-msk-sources')
STAGE=ROOT/'atlantoaxial-staged'
source=ROOT/'z-anatomy-SkeletalSystem100.fbx'
version,nodes=load_fbx(source)
objects={x['properties'][0]:x for x in next(n for n in nodes if n['name']=='Objects')['children'] if x['properties']}
fresh=json.loads((STAGE/'world-inventory.json').read_text())
cached=json.loads((ROOT/'bones-world-inventory.json').read_text())
records=[]
for name in ['Atlas (C1)','Axis (C2)','Occipital bone']:
    entry=next(x for x in fresh['meshes'] if x['name']==name)
    previous=next(x for x in cached['meshes'] if x['source_model_id']==entry['source_model_id'])
    assert entry['world_transform_columns']==previous['world_transform_columns']
    assert entry['bounds']==previous['bounds']
    geo=objects[entry['source_geometry_id']]
    local=np.asarray(child(geo,'Vertices')['properties'][0]).reshape(-1,3)
    indices=np.asarray(child(geo,'PolygonVertexIndex')['properties'][0]); referenced=np.unique(np.where(indices<0,-indices-1,indices))
    matrix=np.array(entry['world_transform_columns']).T
    world=local@matrix[:,:3].T+matrix[:,3]
    path=Path(entry['file']);data=path.read_bytes();magic,n,k=struct.unpack('<4sII',data[:12])
    assert magic==b'BP3D' and len(data)==12+24*n+4*k
    vertices=np.frombuffer(data,dtype='<f4',count=n*3,offset=12).reshape(-1,3)
    faces=np.frombuffer(data,dtype='<u4',count=k,offset=12+24*n).reshape(-1,3)
    assert np.isfinite(vertices).all() and int(faces.max())<n and k//3==entry['triangles']
    forward=float(cKDTree(vertices).query(world[referenced])[0].max())
    reverse=float(cKDTree(world[referenced]).query(vertices)[0].max())
    assert max(forward,reverse)<0.00002
    records.append({'name':name,'source_model_id':entry['source_model_id'],'source_geometry_id':entry['source_geometry_id'],'file':str(path),'sha256':hashlib.sha256(data).hexdigest(),'triangles':k//3,'export_vertices':n,'source_referenced_vertices':len(referenced),'source_unreferenced_vertices':len(local)-len(referenced),'maximum_source_to_export_distance_cm':forward,'maximum_export_to_source_distance_cm':reverse,'bounds':entry['bounds'],'fresh_transform_matches_cache':True,'mirrored_winding_corrected':entry['mirrored_winding_corrected']})
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'exporter_sha256':hashlib.sha256((ROOT/'export_ufbx').read_bytes()).hexdigest(),'unit_meters':fresh['unit_meters'],'axes':fresh['axes'],'parts':records,'limits':['Independent source decoding verifies positions using the freshly exported transforms; it does not independently derive the FBX transform hierarchy.','Triangulation, normals and anatomical fidelity are not clinically validated by nearest-vertex agreement.','No alignment, mesh repair, smoothing or clinical approval performed.'],'runtime_promoted':False}
Path('docs/msk-atlantoaxial-source-review/export-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print([(r['name'],r['triangles'],max(r['maximum_source_to_export_distance_cm'],r['maximum_export_to_source_distance_cm'])) for r in records])
