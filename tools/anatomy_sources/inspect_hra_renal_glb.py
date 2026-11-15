#!/usr/bin/env python3
"""Inventory static source HRA GLB primitives without changing geometry or assigning clinical coverage."""
import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
import struct


def read_glb(raw):
    if len(raw)<20:raise ValueError('Truncated source GLB')
    magic,version,length=struct.unpack_from('<4sII',raw)
    if magic!=b'glTF' or version!=2 or length!=len(raw):raise ValueError('Invalid GLB header')
    offset=12;chunks=[]
    while offset<len(raw):
        if offset+8>len(raw):raise ValueError('Truncated GLB chunk')
        size,kind=struct.unpack_from('<II',raw,offset);offset+=8
        if size%4 or offset+size>len(raw):raise ValueError('Invalid GLB chunk extent')
        chunks.append((kind,raw[offset:offset+size]));offset+=size
    if len(chunks)!=2 or chunks[0][0]!=0x4e4f534a or chunks[1][0]!=0x004e4942:raise ValueError('Need one JSON and embedded BIN chunk')
    document=json.loads(chunks[0][1]);binary=chunks[1][1]
    if len(document.get('buffers',[]))!=1 or 'uri' in document['buffers'][0] or document['buffers'][0]['byteLength']>len(binary):raise ValueError('External or invalid source buffer')
    if any(document.get(k) for k in ['skins','animations','extensionsRequired']):raise ValueError('Unreviewed dynamic/extension geometry')
    return document,binary


def accessor(document,binary,index):
    import numpy as np
    a=document['accessors'][index]
    if 'sparse' in a or a.get('normalized',False):raise ValueError('Unreviewed sparse/normalized accessor')
    types={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'};widths={'SCALAR':1,'VEC3':3}
    if a['componentType'] not in types or a['type'] not in widths:raise ValueError('Unsupported source accessor type')
    dtype=np.dtype(types[a['componentType']]);width=widths[a['type']];v=document['bufferViews'][a['bufferView']]
    if v['buffer']!=0:raise ValueError('Source buffer differs')
    start=v.get('byteOffset',0)+a.get('byteOffset',0);packed=dtype.itemsize*width;stride=v.get('byteStride',packed)
    if a['count']<=0 or stride<packed or a.get('byteOffset',0)+(a['count']-1)*stride+packed>v['byteLength'] or v.get('byteOffset',0)+v['byteLength']>len(binary):raise ValueError('Source accessor leaves buffer view')
    result=np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=start,strides=(stride,dtype.itemsize)).copy()
    if not np.isfinite(result).all():raise ValueError('Nonfinite source accessor')
    return result


def ontology_uri(identifier):
    if re.fullmatch(r'UBERON:[0-9]{7}', identifier):
        return 'http://purl.obolibrary.org/obo/' + identifier.replace(':', '_')
    if re.fullmatch(r'FMA:[0-9]+', identifier):
        return 'http://purl.org/sig/ont/fma/fma' + identifier.split(':')[1]
    raise ValueError('Unreviewed source ontology namespace')


def inspect(path,crosswalk_path):
    import numpy as np
    document,binary=read_glb(path.read_bytes());crosswalk=list(csv.DictReader(crosswalk_path.open()))
    names=[row['node_name'] for row in crosswalk]
    if len(names)!=len(set(names)):raise ValueError('Duplicate source crosswalk node')
    cross={row['node_name']:row for row in crosswalk};nodes=document['nodes'];visited=set();parents={}
    def walk(index):
        if index in visited:raise ValueError('Repeated/cyclic scene node')
        visited.add(index);node=nodes[index]
        if any(k in node for k in ['matrix','translation','scale','rotation','skin','weights']):raise ValueError('Source transforms need explicit separate review; do not ignore them')
        for child in node.get('children',[]):
            if child in parents:raise ValueError('Shared source node parent')
            parents[child]=index;walk(child)
    for index in document['scenes'][document.get('scene',0)]['nodes']:walk(index)
    if len(visited)!=len(nodes):raise ValueError('Uninspected source scene nodes')
    records=[];unmapped_groups=[]
    for index,node in enumerate(nodes):
        name=node.get('name');c=cross.get(name)
        if not c:
            if 'mesh' in node:raise ValueError('Source mesh node is absent from crosswalk')
            unmapped_groups.append({'node_index':index,'node_name':name,'anatomical_identity_assigned':False});continue
        extras=node.get('extras',{})
        semantic_match=(extras.get('label')==c['label'] and extras.get('representation_of')==ontology_uri(c['OntologyID']))
        if 'mesh' not in node:continue
        mesh=document['meshes'][node['mesh']]
        for part,primitive in enumerate(mesh['primitives']):
            if primitive.get('mode',4)!=4 or primitive.get('targets') or 'indices' not in primitive:raise ValueError('Unreviewed source primitive topology')
            vertices=accessor(document,binary,primitive['attributes']['POSITION']);indices=accessor(document,binary,primitive['indices']).reshape(-1)
            if vertices.shape[1]!=3 or len(indices)%3 or not np.issubdtype(indices.dtype,np.integer) or indices.max()>=len(vertices):raise ValueError('Invalid source triangles')
            faces=indices.reshape(-1,3);tri=vertices[faces].astype(float)
            edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
            positions,inverse=np.unique(vertices,axis=0,return_inverse=True);wf=inverse[faces]
            welded_edges=np.sort(np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]),axis=1);_,wc=np.unique(welded_edges,axis=0,return_counts=True)
            area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
            records.append({'node_index':index,'node_name':name,'mesh_name':mesh.get('name'),'primitive_index':part,
                            'source_label':c['label'],'source_ontology_id':c['OntologyID'],'glb_source_label':extras.get('label'),'source_representation_of':extras.get('representation_of'),
                            'semantic_metadata_exact_match':semantic_match,'semantic_specialization_or_conflict_reviewed':False,
                            'vertices':len(vertices),'triangles':len(faces),'position_accessor_sha256':hashlib.sha256(vertices.tobytes()).hexdigest(),
                            'indices_accessor_sha256':hashlib.sha256(indices.tobytes()).hexdigest(),'bounds_original_gltf_metres':[vertices.min(0).tolist(),vertices.max(0).tolist()],
                            'indexed_boundary_edges':int((counts==1).sum()),'indexed_nonmanifold_edges':int((counts>2).sum()),
                            'exact_duplicate_positions':len(vertices)-len(positions),'exact_position_boundary_edges':int((wc==1).sum()),
                            'exact_position_nonmanifold_edges':int((wc>2).sum()),'zero_area_triangles':int((area==0).sum()),
                            'source_geometry_modified':False,'exact_position_welding_is_analysis_only':True,'clinical_approval':False})
    return {'source_glb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_crosswalk_sha256':hashlib.sha256(crosswalk_path.read_bytes()).hexdigest(),
            'source_asset_generator':document['asset'].get('generator'),'scene_nodes':len(nodes),'source_meshes':len(document['meshes']),
            'all_scene_nodes_inspected':True,'all_source_meshes_inspected':len({nodes[r['node_index']]['mesh'] for r in records})==len(document['meshes']),
            'source_coordinate_system':'glTF right-handed +Y up; declared linear unit metres. No patient RAS registration or fitted transform.',
            'records':records,'unmapped_nonmesh_groups':unmapped_groups,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Source labels and original reviewer metadata are not independent approval of this conversion or every reporting structure.',
                      'Raw and exact-coordinate edge counts distinguish exported seams; analysis welding does not edit source meshes.',
                      'No continuous self/inter-part contact audit or complete acquisition-derived anatomical accuracy is claimed.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--glb',type=Path,required=True);p.add_argument('--crosswalk',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.write_text(json.dumps(inspect(a.glb,a.crosswalk),indent=2)+'\n')
