#!/usr/bin/env python3
"""Inspect original peritoneal source objects and compare repeated geometry without deduplication."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def review(root,output):
    import numpy as np
    from scipy.spatial import cKDTree
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import review as inspect,read_obj
    inspect(root,output,expected_object_count=4)
    path=output/'original-obj-geometry-review.json';report=json.loads(path.read_text());objects={}
    for r in report['records']:
        raw=(root/'objects'/(r['id']+'.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=r['source_sha256']:raise ValueError('Original source changed')
        v,n,f,nf=read_obj(raw.decode());tri=v[f]
        # Analysis only: exact unordered geometric triangles, retaining duplicate multiplicity.
        vertices=np.sort(tri.view([('',tri.dtype)]*3).reshape(tri.shape[:2]),axis=1)
        flat=np.ascontiguousarray(vertices).view(tri.dtype).reshape(-1,9)
        order=np.lexsort(flat[:,::-1].T[::-1]);canonical=flat[order]
        objects[r['id']]={'vertices':v,'faces':f,'triangles':tri,'canonical_triangles':canonical}
    comparisons=[]
    for a,b in [('FJ3396','FJ4650'),('FJ3398','FJ4651')]:
        first,second=objects[a],objects[b]
        comparisons.append({'source_ids':[a,b],'position_records_exactly_equal':bool(np.array_equal(first['vertices'],second['vertices'])),
         'indexed_faces_exactly_equal':bool(np.array_equal(first['faces'],second['faces'])),
         'ordered_geometric_triangles_exactly_equal':bool(np.array_equal(first['triangles'],second['triangles'])),
         'unordered_geometric_triangles_with_multiplicity_exactly_equal':bool(np.array_equal(first['canonical_triangles'],second['canonical_triangles'])),
         'source_meshes_deduplicated_or_roles_reassigned':False,'biological_identity_independently_verified':False,
         'maximum_first_vertex_to_second_vertex_distance_mm':float(cKDTree(second['vertices']).query(first['vertices'])[0].max()),
         'maximum_second_vertex_to_first_vertex_distance_mm':float(cKDTree(first['vertices']).query(second['vertices'])[0].max()),
         'nearest_vertex_distances_are_continuous_surface_bounds':False,
         'same_index_continuous_triangle_displacement_upper_bound_mm':float(np.linalg.norm(first['vertices']-second['vertices'],axis=1).max()) if first['vertices'].shape==second['vertices'].shape and np.array_equal(first['faces'],second['faces']) else None})
    result={'source_geometry_review_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'comparisons':comparisons,
            'complete_peritoneal_anatomy_verified':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Repeated source geometry is a source fact, not proof that distinct labels denote distinct structures or complete extent.',
                      'Original objects/normal/index records remain preserved; no deduplication, fusion or fitted transformation edits them.',
                      'Greater/lesser omentum, named ligaments/recesses and complete visceral/parietal surfaces remain unsupported by this four-object packet.']}
    (output/'source-geometry-correspondence.json').write_text(json.dumps(result,indent=2)+'\n')
    payload=path.read_bytes();compressed=gzip.compress(payload,compresslevel=9,mtime=0)
    target=output/'original-obj-geometry-review.json.gz';target.write_bytes(compressed)
    if gzip.decompress(target.read_bytes())!=payload:raise ValueError('Complete inventory compression changed content')
    (output/'complete-inventory-compression.json').write_text(json.dumps({'file':target.name,'compressed_sha256':hashlib.sha256(compressed).hexdigest(),
        'uncompressed_sha256':hashlib.sha256(payload).hexdigest(),'uncompressed_bytes':len(payload),'compressed_bytes':len(compressed),'complete_component_records_preserved':True},indent=2)+'\n')
    path.unlink()
    print(comparisons,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.source_root,a.output)
