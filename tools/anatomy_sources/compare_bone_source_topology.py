"""Trace abnormal exported edges to source polygons without mesh repair."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.inspect_fbx import load_fbx,child

def incidence(positions,faces):
    edges=Counter()
    for face in faces:
        for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((positions[a],positions[b])))]+=1
    return {edge:count for edge,count in edges.items() if count!=2}

def compare(source,audit_path,world_path,name):
    audit=json.loads(audit_path.read_text());raw_bytes=source.read_bytes()
    if hashlib.sha256(raw_bytes).hexdigest()!=audit['source_sha256']:raise ValueError('Source changed after export audit')
    record=next(p for p in audit['parts'] if p['name']==name)
    world=next(p for p in json.loads(world_path.read_text())['meshes'] if p['source_model_id']==record['source_model_id'])
    if world['source_geometry_id']!=record['source_geometry_id']:raise ValueError('Geometry identity mismatch')
    _,nodes=load_fbx(source);objects={n['properties'][0]:n for n in next(x for x in nodes if x['name']=='Objects')['children'] if n['properties']}
    geo=objects[record['source_geometry_id']];raw=child(geo,'Vertices')['properties'][0];local=list(zip(raw[0::3],raw[1::3],raw[2::3]));indices=child(geo,'PolygonVertexIndex')['properties'][0]
    faces=[];face=[]
    for index in indices:
        value=index if index>=0 else -index-1
        if not 0<=value<len(local):raise ValueError('Invalid source index')
        face.append(value)
        if index<0:faces.append(face);face=[]
    if face:raise ValueError('Unterminated source polygon')
    m=world['world_transform_columns']
    def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
    positions=[tuple(f32(sum(p[j]*m[j][a] for j in range(3))+m[3][a]) for a in range(3)) for p in local]
    native_bad=incidence(local,faces);source_bad=incidence(positions,faces)
    data=Path(record['file']).read_bytes()
    if hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('Export changed')
    magic,n,k=struct.unpack('<4sII',data[:12])
    if magic!=b'BP3D' or len(data)!=12+n*24+k*4:raise ValueError('Invalid export')
    v=list(struct.iter_unpack('<fff',data[12:12+n*12]));triangles=list(struct.iter_unpack('<III',data[12+n*24:]));export_bad=incidence(v,triangles)
    return {'name':name,'source_sha256':audit['source_sha256'],'export_sha256':record['sha256'],'source_model_id':record['source_model_id'],'source_geometry_id':record['source_geometry_id'],'source_polygon_sizes':dict(Counter(map(len,faces))),'native_precision_abnormal_edge_incidence_histogram':dict(Counter(native_bad.values())),'float32_source_abnormal_edge_incidence_histogram':dict(Counter(source_bad.values())),'export_abnormal_edge_incidence_histogram':dict(Counter(export_bad.values())),'exact_world_endpoint_and_incidence_match':source_bad==export_bad,'source_edges':[{'world_endpoints_cm':e,'incident_source_polygons':c} for e,c in sorted(source_bad.items())],'geometry_changed':False,'clinical_approval':False,'limits':'Vertex-position edge incidence, not clinical pathology or independent validation of the source transform hierarchy.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['source','audit','world','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--name',required=True);a=p.parse_args();r=compare(a.source,a.audit,a.world,a.name);a.output.write_text(json.dumps(r,indent=2)+'\n');print({k:v for k,v in r.items() if k!='source_edges'})
