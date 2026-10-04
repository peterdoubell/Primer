#!/usr/bin/env python3
"""Inspect every original upstream pancreatic OBJ without repairing or fitting geometry."""
import argparse
from collections import Counter
import hashlib
import json
import re
from pathlib import Path


def read_obj(text):
    import numpy as np
    positions=[];normals=[];faces=[];normal_faces=[]
    for line in text.splitlines():
        fields=line.split()
        if not fields or fields[0].startswith('#'):continue
        kind=fields[0]
        if kind in ('v','vn'):
            if len(fields)!=4:raise ValueError('Unreviewed vertex/normal coordinate record')
            target=positions if kind=='v' else normals;target.append([float(v) for v in fields[1:]])
        elif kind=='f':
            if len(fields)!=4:raise ValueError('Original non-triangle requires explicit preservation policy')
            ids=[];nids=[]
            for token in fields[1:]:
                parts=token.split('/')
                if len(parts)!=3 or parts[1] or not parts[0] or not parts[2]:raise ValueError('Unreviewed OBJ face attributes')
                v,n=int(parts[0]),int(parts[2])
                if v==0 or n==0:raise ValueError('OBJ indices are not zero-based')
                ids.append(v-1 if v>0 else len(positions)+v)
                nids.append(n-1 if n>0 else len(normals)+n)
            faces.append(ids);normal_faces.append(nids)
        elif kind not in ('g','usemtl','mtllib','o','s'):
            raise ValueError('Unreviewed source OBJ record '+kind)
    v=np.asarray(positions,float);n=np.asarray(normals,float);f=np.asarray(faces,np.int64);nf=np.asarray(normal_faces,np.int64)
    if v.ndim!=2 or v.shape[1]!=3 or n.ndim!=2 or n.shape[1]!=3 or f.ndim!=2 or f.shape[1]!=3 or not len(f):raise ValueError('Missing original geometry')
    if not np.isfinite(v).all() or not np.isfinite(n).all() or f.min()<0 or f.max()>=len(v) or nf.min()<0 or nf.max()>=len(n):
        raise ValueError('Original source indices/coordinates are invalid')
    return v,n,f,nf


def topology(v,f):
    import numpy as np
    edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
    unique,counts=np.unique(edges,axis=0,return_counts=True)
    adjacency={int(i):set() for i in np.unique(f)}
    for a,b in unique:adjacency[int(a)].add(int(b));adjacency[int(b)].add(int(a))
    remaining=set(adjacency);components=[]
    while remaining:
        first=min(remaining);remaining.remove(first);selected={first};front=[first]
        while front:
            for other in adjacency[front.pop()]:
                if other in remaining:remaining.remove(other);selected.add(other);front.append(other)
        indices=sorted(selected);selected_faces=np.isin(f[:,0],indices)
        points=v[indices]
        components.append({'referenced_vertices':len(indices),'faces':int(selected_faces.sum()),
                           'bounds_original_mm':[points.min(0).tolist(),points.max(0).tolist()]})
    return {'referenced_vertices':len(adjacency),'unreferenced_vertices':len(v)-len(adjacency),
            'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),'components':components}


def review(root,output):
    import numpy as np
    receipt_path=root/'upstream-acquisition.json';receipt=json.loads(receipt_path.read_text());records=[]
    for row in receipt['objects']:
        raw=(root/'objects'/(row['id']+'.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Original source OBJ changed')
        v,n,f,nf=read_obj(raw.decode())
        if len(v)!=row['vertices'] or len(f)!=row['faces']:raise ValueError('Original record count differs')
        positions,inverse=np.unique(v,axis=0,return_inverse=True);welded=inverse[f]
        areas=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)/2
        declared=np.asarray([[float(v) for v in part.split(',')] for part in re.findall(r'\(([^)]+)\)',row['original_obj_header']['Bounds(mm)'])])
        if declared.shape!=(2,3) or not np.isfinite(declared).all():raise ValueError('Unreviewed declared source bounds')
        observed=np.stack([v.min(0),v.max(0)])
        record={'id':row['id'],'source_label':row['source_label'],'source_fma':row['source_fma'],'source_sha256':row['sha256'],
                'vertices':len(v),'normals':len(n),'triangles':len(f),'positions_float64_le_sha256':hashlib.sha256(v.astype('<f8').tobytes()).hexdigest(),
                'face_indices_int64_le_sha256':hashlib.sha256(f.astype('<i8').tobytes()).hexdigest(),
                'normal_indices_int64_le_sha256':hashlib.sha256(nf.astype('<i8').tobytes()).hexdigest(),
                'normals_float64_le_sha256':hashlib.sha256(n.astype('<f8').tobytes()).hexdigest(),
                'maximum_source_declared_vs_actual_bounds_difference_mm':float(np.max(np.abs(observed-declared))),
                'declared_bounds_corrected_or_used_to_fit_mesh':False,
                'bounds_original_mm':[v.min(0).tolist(),v.max(0).tolist()],'source_declared_bounds_mm':row['original_obj_header'].get('Bounds(mm)'),
                'source_declared_volume_cm3':row['original_obj_header'].get('Volume(cm3)'),
                'indexed_topology':topology(v,f),'exact_position_analysis_topology':topology(positions,welded),
                'exact_duplicate_position_records':len(v)-len(positions),'zero_area_triangles':int((areas==0).sum()),
                'minimum_triangle_area_mm2':float(areas.min()),'maximum_triangle_area_mm2':float(areas.max()),
                'source_positions_faces_or_normals_changed':False,'analysis_welding_changes_source':False,'clinical_approval':False}
        records.append(record)
        print(row['id'],len(f),'triangles; exact position boundary/nonmanifold',record['exact_position_analysis_topology']['boundary_edges'],record['exact_position_analysis_topology']['nonmanifold_edges'],'components',len(record['exact_position_analysis_topology']['components']),flush=True)
    groups=[]
    for code,ids in receipt['source_groups'].items():
        selected=[r for r in records if r['id'] in ids]
        if len(selected)!=len(ids):raise ValueError('Source group missing an original element')
        groups.append({'source_fma':code,'source_target_label':receipt['target_labels'][code],'element_ids':ids,
                       'source_triangle_count':sum(r['triangles'] for r in selected),'compound_fused_or_given_fine_structure_credit':False})
    result={'original_acquisition_sha256':hashlib.sha256(receipt_path.read_bytes()).hexdigest(),'records':records,'source_groups':groups,
            'all_25_original_objects_inspected':len(records)==25,'source_coordinate_units':'millimetres as declared in original OBJ headers; no patient registration or fitted scale.',
            'source_meshes_merged_repaired_or_smoothed':False,'source_resolution_verified':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Exact-position topology is a diagnostic analysis index, not a source weld or proof of anatomical identity.',
                      'Disconnected components are source geometry facts; no ducts, walls, lumina or named branch identities are assigned automatically.',
                      'Matching source labels and more vertices do not establish source acquisition resolution or complete reporting anatomy.',
                      'Original volume/bounds fields remain source assertions; no clinically validated lumen/wall volume or pathological state is inferred.']}
    output.mkdir(parents=True,exist_ok=True);(output/'original-obj-geometry-review.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.source_root,a.output)
