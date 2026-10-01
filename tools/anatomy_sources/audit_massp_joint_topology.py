#!/usr/bin/env python3
"""Check closed edges, oriented volume and every vertex link without repairs."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np


def audit(root,output):
    manifest=json.loads((root/'surface-review.json').read_text());rows=[]
    for row in manifest['records']:
        path=root/row['mesh_file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row['mesh_sha256']:raise ValueError('Mesh changed')
        with np.load(path) as data:vertices=data['vertices'].copy();faces=data['faces'].copy()
        triangles=vertices[faces]
        edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
        _,counts=np.unique(edges,axis=0,return_counts=True)
        areas=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)/2
        volume=float(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6)
        links=defaultdict(list)
        for a,b,c in faces:links[int(a)].append((int(b),int(c)));links[int(b)].append((int(c),int(a)));links[int(c)].append((int(a),int(b)))
        defects=[]
        for vertex,link_edges in links.items():
            adjacency=defaultdict(list)
            for a,b in link_edges:adjacency[a].append(b);adjacency[b].append(a)
            remaining=set(adjacency);components=0
            while remaining:
                components+=1;frontier=[remaining.pop()]
                while frontier:
                    for other in adjacency[frontier.pop()]:
                        if other in remaining:remaining.remove(other);frontier.append(other)
            bad_degree=sum(len(neighbours)!=2 for neighbours in adjacency.values())
            if components!=1 or bad_degree:defects.append({'vertex':vertex,'link_components':components,'non_cycle_link_nodes':bad_degree})
        result={'code':row['code'],'side':row['side'],'mesh_sha256':row['mesh_sha256'],
                'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),
                'zero_area_triangles':int((areas<=0).sum()),'signed_volume_mm3':volume,
                'vertices_checked':len(links),'nonmanifold_vertex_count':len(defects),'vertex_defects':defects}
        rows.append(result);print(row['code'],row['side'],len(defects),flush=True)
    output.write_text(json.dumps({'mesh_manifest_sha256':hashlib.sha256((root/'surface-review.json').read_bytes()).hexdigest(),
                                  'records':rows,'source_geometry_changed':False,'clinical_approval':False,
                                  'method':'Every vertex link must be one connected cycle; edge incidence two, positive face areas and signed volume also recorded. Topology does not establish anatomy.'},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--meshes',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();audit(args.meshes,args.output)
