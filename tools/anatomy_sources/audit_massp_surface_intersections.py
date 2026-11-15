#!/usr/bin/env python3
"""Conservative broad phase and explicit triangle contacts for source surfaces."""
import argparse
from collections import defaultdict
import hashlib
from itertools import combinations, product
import json
from pathlib import Path

import numpy as np

TOLERANCE_MM = 1e-9


def plane_segment(triangle, normal, origin, tolerance):
    distances = (triangle-origin) @ normal
    if np.all(distances>tolerance) or np.all(distances<-tolerance):
        return []
    points = [point for point,distance in zip(triangle,distances) if abs(distance)<=tolerance]
    for a,b in ((0,1),(1,2),(2,0)):
        if distances[a]*distances[b]<0 and abs(distances[a])>tolerance and abs(distances[b])>tolerance:
            fraction = distances[a]/(distances[a]-distances[b])
            points.append(triangle[a]+fraction*(triangle[b]-triangle[a]))
    return points


def cross2(first, second):
    return first[0]*second[1]-first[1]*second[0]


def coplanar_polygon(first, second, normal, tolerance):
    axes = [axis for axis in range(3) if axis!=int(np.argmax(np.abs(normal)))]
    clip = second[:,axes]
    signed = cross2(clip[1]-clip[0],clip[2]-clip[0])
    orientation = 1 if signed>=0 else -1
    polygon = [point.copy() for point in first]
    for a,b in ((0,1),(1,2),(2,0)):
        result=[]
        if not polygon:
            break
        edge=clip[b]-clip[a]
        for previous,current in zip(polygon[-1:]+polygon[:-1],polygon):
            dp=orientation*cross2(edge,previous[axes]-clip[a])/np.linalg.norm(edge)
            dc=orientation*cross2(edge,current[axes]-clip[a])/np.linalg.norm(edge)
            inside_previous=dp>=-tolerance;inside_current=dc>=-tolerance
            if inside_previous != inside_current:
                result.append(previous+(dp/(dp-dc))*(current-previous))
            if inside_current:
                result.append(current)
        polygon=result
    return polygon


def triangle_contact(first, second, tolerance=TOLERANCE_MM):
    normals=[]
    for triangle in (first,second):
        normal=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0])
        length=np.linalg.norm(normal)
        if length<=tolerance*tolerance:
            raise ValueError('Degenerate triangle in intersection input')
        normals.append(normal/length)
    n1,n2=normals;direction=np.cross(n1,n2)
    if np.linalg.norm(direction)<=1e-12:
        if np.max(np.abs((second-first[0])@n1))>tolerance:
            return []
        return coplanar_polygon(first,second,n1,tolerance)
    segment1=plane_segment(first,n2,second[0],tolerance)
    segment2=plane_segment(second,n1,first[0],tolerance)
    if not segment1 or not segment2:
        return []
    axis=int(np.argmax(np.abs(direction)))
    segment1=sorted(segment1,key=lambda p:p[axis]);segment2=sorted(segment2,key=lambda p:p[axis])
    lower=max(segment1[0][axis],segment2[0][axis]);upper=min(segment1[-1][axis],segment2[-1][axis])
    if lower>upper+tolerance:
        return []
    if abs(segment1[-1][axis]-segment1[0][axis])<=tolerance:
        return [segment1[0]]
    return [segment1[0]+((value-segment1[0][axis])/(segment1[-1][axis]-segment1[0][axis]))*(segment1[-1]-segment1[0])
            for value in (lower,upper)]


def allowed_shared_contact(points, shared, tolerance=TOLERANCE_MM):
    if not points:
        return True
    if len(shared)==0:
        return False
    if len(shared)==1:
        return all(np.linalg.norm(point-shared[0])<=tolerance for point in points)
    if len(shared)==2:
        edge=shared[1]-shared[0];squared=float(edge@edge)
        if squared==0:
            raise ValueError('Coincident source edge endpoints')
        for point in points:
            fraction=float((point-shared[0])@edge/squared)
            nearest=shared[0]+np.clip(fraction,0,1)*edge
            if np.linalg.norm(point-nearest)>tolerance:
                return False
        return True
    return False  # Duplicate faces are never an ordinary adjacency.


def candidate_pairs(triangles, cell_size=.5):
    cells=defaultdict(list)
    low=triangles.min(1);high=triangles.max(1)
    for index,(start,stop) in enumerate(zip(np.floor((low-TOLERANCE_MM)/cell_size).astype(int),np.floor((high+TOLERANCE_MM)/cell_size).astype(int))):
        for key in product(*(range(a,b+1) for a,b in zip(start,stop))):
            cells[key].append(index)
    candidates=set()
    for indices in cells.values():
        candidates.update(combinations(indices,2))
    pairs=np.array(sorted(candidates),dtype=np.int64).reshape(-1,2)
    overlap=np.all(np.maximum(low[pairs[:,0]],low[pairs[:,1]])<=np.minimum(high[pairs[:,0]],high[pairs[:,1]])+TOLERANCE_MM,axis=1)
    return pairs[overlap]


def inspect(vertices, faces):
    triangles=vertices[faces]
    pairs=candidate_pairs(triangles)
    failures=[];shared_edge_nonparallel=0;tested=0
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    norms=np.linalg.norm(normals,axis=1)
    if np.any(norms<=TOLERANCE_MM*TOLERANCE_MM):
        raise ValueError('Degenerate source triangle')
    normals=normals/norms[:,None]
    for a,b in pairs:
        common=np.intersect1d(faces[a],faces[b])
        # Noncoplanar triangle planes intersect only along their shared edge.
        # Each triangle meets that line at exactly its edge, so no extra contact
        # is possible. Coplanar pairs and all single-vertex pairs are evaluated.
        if len(common)==2 and np.linalg.norm(np.cross(normals[a],normals[b]))>1e-12:
            shared_edge_nonparallel+=1
            continue
        points=triangle_contact(triangles[a],triangles[b]);tested+=1
        if not allowed_shared_contact(points,vertices[common]):
            failures.append({'face_indices':[int(a),int(b)],'shared_vertex_count':len(common),
                             'contact_points_mm':[point.tolist() for point in points]})
    return {'triangles':len(faces),'conservative_aabb_candidate_pairs':len(pairs),
            'noncoplanar_shared_edge_pairs_resolved_geometrically':shared_edge_nonparallel,
            'pairs_explicitly_intersection_tested':tested,'unexpected_contact_count':len(failures),
            'unexpected_contacts':failures,'comparison_tolerance_mm':TOLERANCE_MM}


def audit(mesh_root, output):
    manifest=json.loads((mesh_root/'surface-review.json').read_text());records=[]
    for row in manifest['records']:
        if not row['output_mesh_created']:
            raise ValueError('Held source cannot enter geometric audit')
        path=mesh_root/row['mesh_file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row['mesh_sha256']:
            raise ValueError('Source mesh changed')
        with np.load(path) as data:
            result=inspect(data['vertices'],data['faces'])
        records.append({'code':row['code'],'side':row['side'],'mesh_sha256':row['mesh_sha256'],**result})
        print(row['code'],row['side'],result['unexpected_contact_count'],flush=True)
    output.write_text(json.dumps({'mesh_manifest_sha256':hashlib.sha256((mesh_root/'surface-review.json').read_bytes()).hexdigest(),
                                  'records':records,'source_meshes_changed':False,'clinical_approval':False,
                                  'limits':'Floating-point triangle contact audit at stated tolerance. Does not establish anatomical accuracy, MRI validity or interactions between different structure surfaces.'},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--meshes',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();audit(args.meshes,args.output)
