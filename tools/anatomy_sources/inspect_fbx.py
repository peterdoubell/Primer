#!/usr/bin/env python3
"""Read named FBX source geometry for a bounded, non-publishing anatomy audit.

Supports binary FBX 7.x nodes, typed properties, compressed arrays and object
connections. Does not execute embedded scripts or modify published assets.
"""
import argparse, array, hashlib, json, math, pathlib, struct, zlib


def load_fbx(path):
    data = pathlib.Path(path).read_bytes()
    if not data.startswith(b'Kaydara FBX Binary  \0\x1a\0'):
        raise ValueError('Expected binary FBX')
    version = struct.unpack_from('<I', data, 23)[0]
    wide = version >= 7500
    header_format = '<QQQB' if wide else '<IIIB'
    header_size = struct.calcsize(header_format)
    scalar = {'Y':'h', 'C':'?', 'I':'i', 'F':'f', 'D':'d', 'L':'q'}
    arrays = {'f':'f', 'd':'d', 'l':'q', 'i':'i', 'b':'b', 'c':'b'}

    def prop(offset):
        kind=chr(data[offset]); offset+=1
        if kind in scalar:
            fmt='<'+scalar[kind]
            return struct.unpack_from(fmt,data,offset)[0],offset+struct.calcsize(fmt)
        if kind in {'S','R'}:
            length=struct.unpack_from('<I',data,offset)[0]; offset+=4
            value=data[offset:offset+length]
            return (value.decode('utf8','replace') if kind=='S' else value),offset+length
        if kind in arrays:
            length,encoding,size=struct.unpack_from('<III',data,offset); offset+=12
            payload=data[offset:offset+size]
            raw=zlib.decompress(payload) if encoding==1 else payload
            values=array.array(arrays[kind]); values.frombytes(raw)
            if len(values)!=length: raise ValueError('Invalid array length')
            return values,offset+size
        raise ValueError('Unsupported FBX property '+kind)

    def node(offset):
        end,count,prop_bytes,name_len=struct.unpack_from(header_format,data,offset)
        offset+=header_size
        if not end:return None,offset
        if end>len(data) or end<offset:raise ValueError('Invalid node end offset')
        name=data[offset:offset+name_len].decode('utf8');offset+=name_len
        properties=[]
        for _ in range(count):value,offset=prop(offset);properties.append(value)
        children=[]
        while offset<end:
            child,next_offset=node(offset)
            offset=next_offset
            if child is None:break
            children.append(child)
        return {'name':name,'properties':properties,'children':children},end

    nodes=[];offset=27
    while offset<len(data)-header_size:
        entry,offset=node(offset)
        if entry is None:break
        nodes.append(entry)
    return version,nodes


def child(node,name):
    return next((x for x in node['children'] if x['name']==name),None)


def inventory(path):
    version,nodes=load_fbx(path)
    objects=next(n for n in nodes if n['name']=='Objects')['children']
    object_map={n['properties'][0]:n for n in objects if n['properties']}
    connections=next(n for n in nodes if n['name']=='Connections')['children']
    parents={}
    for c in connections:
        if len(c['properties'])>=3 and c['properties'][0]=='OO':
            parents[c['properties'][1]]=c['properties'][2]
    records=[]
    for geometry in objects:
        if geometry['name']!='Geometry' or not child(geometry,'Vertices'):continue
        gid=geometry['properties'][0];model=object_map.get(parents.get(gid))
        props={}
        if model:
            p70=child(model,'Properties70')
            if p70:props={p['properties'][0]:p['properties'][4:] for p in p70['children'] if p['name']=='P'}
        vertices=child(geometry,'Vertices')['properties'][0]
        indices=child(geometry,'PolygonVertexIndex')['properties'][0]
        triangles=0;current=0;max_index=-1
        for i in indices:
            index=i if i>=0 else -i-1;max_index=max(index,max_index);current+=1
            if i<0:triangles+=current-2;current=0
        count=len(vertices)//3
        if not count or max_index>=count:raise ValueError('Invalid mesh indices')
        record={
            'geometry_id':gid,'geometry_name':geometry['properties'][1].split('\0')[0],
            'model_name':model['properties'][1].split('\0')[0] if model else None,
            'model_id':model['properties'][0] if model else None,
            'parent_model_id':parents.get(model['properties'][0]) if model else None,
            'vertices':count,'triangles':triangles,
            'bounds_local':[[min(vertices[a::3]) for a in range(3)],[max(vertices[a::3]) for a in range(3)]],
            'transforms':{k:v for k,v in props.items() if k.startswith(('Lcl ','Geometric','PreRotation','PostRotation'))},
            'finite':all(math.isfinite(v) for v in vertices),
        }
        records.append(record)
    return {'file':str(path),'bytes':pathlib.Path(path).stat().st_size,'sha256':hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest(),'fbx_version':version,'mesh_count':len(records),'total_vertices':sum(r['vertices'] for r in records),'total_triangles':sum(r['triangles'] for r in records),'meshes':records}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=pathlib.Path);parser.add_argument('--output',type=pathlib.Path);args=parser.parse_args()
    result=inventory(args.source)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='meshes'},indent=2))
    for m in result['meshes']:
        print(m['model_name'],m['vertices'],m['triangles'])
