#!/usr/bin/env python3
"""Inspect every testable original biliary triangle without merging source representations."""
import argparse,gzip,hashlib,json
from pathlib import Path


def audit(root,output):
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    from tools.anatomy_sources.audit_hra_renal_contacts import contact_arrays
    from tools.anatomy_sources.audit_massp_surface_intersections import inspect
    inventory_path=output/'original-obj-geometry-review.json';payload=inventory_path.read_bytes();inventory=json.loads(payload)
    inventory_sha256=hashlib.sha256(payload).hexdigest()
    summary=[]
    for r in inventory['records']:
        path=root/'objects'/(r['id']+'.obj');raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=r['source_sha256']:raise ValueError('Original source changed')
        v,n,f,nf=read_obj(raw.decode())
        if hashlib.sha256(v.astype('<f8').tobytes()).hexdigest()!=r['positions_float64_le_sha256'] or hashlib.sha256(f.astype('<i8').tobytes()).hexdigest()!=r['face_indices_int64_le_sha256']:
            raise ValueError('Source vertex/index values differ')
        vertices,faces,identities,preparation=contact_arrays([{'id':r['id'],'vertices':v,'faces':f}],source_units='millimetres')
        print(r['id'],'testing',len(faces),'triangles; invalid',len(preparation['invalid_source_triangles']),flush=True)
        contacts=inspect(vertices,faces)
        for row in contacts['unexpected_contacts']:row['original_source_faces']=[identities[i] for i in row['face_indices']]
        result={'element_id':r['id'],'source_label':r['source_label'],'source_obj_sha256':r['source_sha256'],
                'source_inventory_sha256':inventory_sha256,'preparation':preparation,'triangle_contact_audit':contacts,
                'source_coordinate_units':'millimetres','source_positions_faces_normals_changed':False,'other_source_objects_compared_or_fused':False,
                'clinical_approval':False,'runtime_promoted':False,
                'limits':['Each original source object is tested alone; nearly repeated objects/labels are not treated as simultaneous distinct anatomy.',
                          'Conservative candidate pairs and explicit numerical checks retain original face identities; ordinary exact shared-vertex/edge adjacency is allowed.',
                          'Contact/fragmentation findings are source geometry facts, not automatically biological junctions, pathological invasion or grounds for deleting tissue.',
                          'Numerical tolerance is not native acquired resolution; source accuracy, complete surfaces and independent anatomy review remain separate requirements.']}
        raw_result=(json.dumps(result,indent=2)+'\n').encode();packed=gzip.compress(raw_result,compresslevel=9,mtime=0);target=output/(r['id']+'-complete-self-contacts.json.gz');target.write_bytes(packed)
        if gzip.decompress(target.read_bytes())!=raw_result:raise ValueError('Complete contact evidence compression changed content')
        summary.append({'element_id':r['id'],'file':target.name,'compressed_sha256':hashlib.sha256(packed).hexdigest(),'uncompressed_sha256':hashlib.sha256(raw_result).hexdigest(),
                        'compressed_bytes':len(packed),'uncompressed_bytes':len(raw_result),'source_triangles':preparation['original_source_triangles'],
                        'testable_triangles':preparation['numerically_testable_triangles'],'invalid_source_faces':len(preparation['invalid_source_triangles']),
                        'candidate_pairs':contacts['conservative_aabb_candidate_pairs'],'explicitly_tested_pairs':contacts['pairs_explicitly_intersection_tested'],
                        'resolved_noncoplanar_shared_edge_pairs':contacts['noncoplanar_shared_edge_pairs_resolved_geometrically'],'contact_count':contacts['unexpected_contact_count']})
        print(r['id'],'finished; contacts',contacts['unexpected_contact_count'],'candidate pairs',contacts['conservative_aabb_candidate_pairs'],flush=True)
        # This progress record is updated only after a complete, losslessly preserved object result.
        (output/'complete-self-contact-summary.json').write_text(json.dumps({'records':summary,'all_twenty_original_objects_complete':len(summary)==20,
            'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.source_root,a.output)
