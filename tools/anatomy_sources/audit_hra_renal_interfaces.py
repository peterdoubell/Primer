#!/usr/bin/env python3
"""Compare every open source renal mesh boundary by exact coordinates, without repairing geometry."""
import argparse
from collections import defaultdict,Counter
import hashlib
import json
from pathlib import Path


def boundary_edges(vertices,faces):
    import numpy as np
    vertices=np.asarray(vertices);faces=np.asarray(faces)
    if vertices.ndim!=2 or vertices.shape[1]!=3 or faces.ndim!=2 or faces.shape[1]!=3 or not np.issubdtype(faces.dtype,np.integer) or not len(faces) or faces.min()<0 or faces.max()>=len(vertices) or not np.isfinite(vertices).all():raise ValueError('Invalid source mesh')
    positions,inverse=np.unique(vertices,axis=0,return_inverse=True);f=inverse[faces]
    directed=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);undirected=np.sort(directed,axis=1)
    edges,first,count=np.unique(undirected,axis=0,return_index=True,return_counts=True)
    records=[]
    for edge,index in zip(edges[count==1],first[count==1]):
        a,b=directed[index]
        if a==b:raise ValueError('Degenerate isolated boundary edge')
        records.append({'coordinates':positions[edge].astype(float).tolist(),'direction':1 if a<b else -1})
    return records,{'indexed_vertices':len(vertices),'exact_unique_positions':len(positions),'exact_position_boundary_edges':int((count==1).sum()),
                    'exact_position_nonmanifold_edges':int((count>2).sum()),'analysis_welding_changes_source':False}



def boundary_components(records):
    """Index every unmatched exact-coordinate boundary graph without assigning anatomy."""
    import numpy as np
    per_part=defaultdict(list)
    for record in records:per_part[record['source_part']].append(record['coordinates_original_metres'])
    result=[]
    for part,edges in sorted(per_part.items()):
        adjacency=defaultdict(set)
        for a,b in edges:
            a,b=tuple(a),tuple(b);adjacency[a].add(b);adjacency[b].add(a)
        remaining=set(adjacency)
        while remaining:
            seed=min(remaining);remaining.remove(seed);selected={seed};frontier=[seed]
            while frontier:
                for other in adjacency[frontier.pop()]:
                    if other in remaining:remaining.remove(other);selected.add(other);frontier.append(other)
            selected_edges=[e for e in edges if tuple(e[0]) in selected and tuple(e[1]) in selected]
            points=np.asarray(sorted(selected));degrees=Counter(len(adjacency[p]) for p in selected)
            result.append({'source_part':part,'boundary_component':len(result)+1,'vertices':len(selected),
                           'edges':len(selected_edges),'vertex_degree_counts':{str(k):v for k,v in sorted(degrees.items())},
                           'is_closed_simple_graph_cycle':set(degrees)=={2},'bounds_original_metres':[points.min(0).tolist(),points.max(0).tolist()],
                           'total_boundary_length_metres':float(sum(np.linalg.norm(np.asarray(b)-a) for a,b in selected_edges)),
                           'coordinates_original_metres':selected_edges,'anatomical_role_assigned':False})
    return result


def compare_boundaries(parts):
    edges=defaultdict(list);part_records=[]
    for part in parts:
        records,stats=boundary_edges(part['vertices'],part['faces']);part_records.append({'id':part['id'],**stats})
        for index,r in enumerate(records):
            key=tuple(v for p in r['coordinates'] for v in p)
            edges[key].append({'source_part':part['id'],'local_boundary_index':index,'direction':r['direction']})
    pair_groups=defaultdict(list);unmatched=[];multiple=[]
    for coordinates,owners in edges.items():
        if len(owners)==1:unmatched.append({'coordinates_original_metres':[list(coordinates[:3]),list(coordinates[3:])],**owners[0]})
        elif len(owners)==2 and owners[0]['source_part']!=owners[1]['source_part']:
            pair=tuple(sorted(o['source_part'] for o in owners));pair_groups[pair].append({'coordinates_original_metres':[list(coordinates[:3]),list(coordinates[3:])],
                                                                                      'owners':owners,'opposing_edge_directions':sum(o['direction'] for o in owners)==0})
        else:multiple.append({'coordinates_original_metres':[list(coordinates[:3]),list(coordinates[3:])],'owners':owners})
    pairs=[]
    for names,records in sorted(pair_groups.items()):
        pairs.append({'source_parts':list(names),'exact_shared_boundary_edges':len(records),'opposing_direction_edges':sum(r['opposing_edge_directions'] for r in records),
                      'same_direction_edges':sum(not r['opposing_edge_directions'] for r in records),'edges':records,'anatomical_interface_verified':False})
    return {'source_parts':part_records,'source_boundary_edge_occurrences':sum(r['exact_position_boundary_edges'] for r in part_records),
            'exact_boundary_pair_edges':sum(r['exact_shared_boundary_edges'] for r in pairs),'unmatched_boundary_edges':len(unmatched),
            'multiple_owner_boundary_edges':len(multiple),'pairs':pairs,'unmatched':unmatched,'multiple_owners':multiple,'unmatched_boundary_components':boundary_components(unmatched),
            'source_meshes_modified_or_fused':False,'clinical_approval':False}


def audit(root,review_root,output):
    import numpy as np
    from tools.anatomy_sources.inspect_hra_renal_glb import read_glb,accessor
    inputs=[(root/'3d-vh-f-kidney-r.glb','kidney-female-right-v1.3'),(root/'ureter-female-right-v1.2/3d-vh-f-ureter-r.glb','ureter-female-right-v1.2')]
    parts=[];sources=[]
    for path,key in inputs:
        report_path=review_root/(key+'-geometry-inventory.json');report=json.loads(report_path.read_text());raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=report['source_glb_sha256']:raise ValueError('Original source GLB changed')
        d,binary=read_glb(raw)
        for record in report['records']:
            node=d['nodes'][record['node_index']];primitive=d['meshes'][node['mesh']]['primitives'][record['primitive_index']]
            vertices=accessor(d,binary,primitive['attributes']['POSITION']);indices=accessor(d,binary,primitive['indices']).reshape(-1)
            if hashlib.sha256(vertices.tobytes()).hexdigest()!=record['position_accessor_sha256'] or hashlib.sha256(indices.tobytes()).hexdigest()!=record['indices_accessor_sha256']:raise ValueError('Source primitive differs')
            parts.append({'id':key+':'+record['node_name'],'vertices':vertices,'faces':indices.reshape(-1,3)})
        sources.append({'source':key,'source_glb_sha256':report['source_glb_sha256'],'source_inventory_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest()})
    result=compare_boundaries(parts);result.update(sources=sources,standalone_duplicate_pelvis_excluded_from_anatomy_count=True,
        cross_asset_shared_coordinate_frame_is_clinical_registration=False,
        limits=['All original boundary-edge coordinates are checked with exact float values, no tolerance, snapping, fitting or pruning.',
                'Shared source edges show coordinate correspondence only; biological intent, lumen/wall identity and actual anatomy remain unverified.',
                'Unmatched edges may be intended open surfaces or unsupported interfaces; no defect or anatomical absence is inferred.',
                'Per-part nonmanifold/degenerate geometry remains original. Separate source parts are not fused into an approved solid.'])
    output.write_text(json.dumps(result,indent=2)+'\n')
    print('Boundary occurrences',result['source_boundary_edge_occurrences'],'; exact shared pair edges',result['exact_boundary_pair_edges'],'; unmatched',result['unmatched_boundary_edges'],'; multiple owners',result['multiple_owner_boundary_edges'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--review-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.source_root,a.review_root,a.output)
