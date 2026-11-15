#!/usr/bin/env python3
"""Audit original OBJ contacts in separate parenchymal contexts and declared millimetres."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path


def contexts(ids):
    if not {'FJ1895','FJ2629'}.issubset(ids):raise ValueError('Missing original parenchymal alternatives')
    return {parent:sorted(set(ids)-({'FJ1895','FJ2629'}-{parent})) for parent in ['FJ1895','FJ2629']}


def audit(root,output):
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    from tools.anatomy_sources.audit_hra_renal_contacts import contact_arrays
    from tools.anatomy_sources.audit_massp_surface_intersections import inspect
    inventory_path=output/'original-obj-geometry-review.json';inventory=json.loads(inventory_path.read_text());parts={}
    for r in inventory['records']:
        raw=(root/'objects'/(r['id']+'.obj')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=r['source_sha256']:raise ValueError('Original source changed')
        v,n,f,nf=read_obj(raw.decode())
        if hashlib.sha256(v.astype('<f8').tobytes()).hexdigest()!=r['positions_float64_le_sha256'] or hashlib.sha256(f.astype('<i8').tobytes()).hexdigest()!=r['face_indices_int64_le_sha256']:
            raise ValueError('Source coordinate/index values differ from audit')
        parts[r['id']]={'id':r['id'],'vertices':v,'faces':f}
    results=[]
    for parent,ids in contexts(parts).items():
        v,f,identities,preparation=contact_arrays([parts[i] for i in ids],source_units='millimetres')
        print(parent,'testing',len(f),'source triangles; invalid',len(preparation['invalid_source_triangles']),flush=True)
        contacts=inspect(v,f);categories=Counter();pairs=Counter()
        for row in contacts['unexpected_contacts']:
            a,b=(identities[i] for i in row['face_indices']);row['original_source_faces']=[a,b]
            row['same_source_element']=a['source_part']==b['source_part']
            categories['within_source_element' if row['same_source_element'] else 'between_source_elements']+=1
            pairs[tuple(sorted([a['source_part'],b['source_part']]))]+=1
        result={'parenchymal_context':parent,'source_inventory_sha256':hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
                'included_source_element_ids':ids,'source_coordinate_units':'millimetres','source_coordinate_unit_conversion_performed':False,
                'alternative_parenchyma_compared_as_one_biological_context':False,'preparation':preparation,'triangle_contact_audit':contacts,
                'contact_categories':dict(categories),'affected_source_element_pairs':[{'elements':list(k),'contact_pairs':n} for k,n in sorted(pairs.items())],
                'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
                'limits':['Each original parenchymal alternative is checked separately with every other requested source element; alternatives are not merged or treated as two organs.',
                          'All nondegenerate source faces are tested in native millimetres with 1e-9 mm numerical tolerance; exact position indexing is analysis only.',
                          'Geometric contacts can involve intended interfaces, source components, construction artifacts or invalid anatomy; they are not pathological invasion or automatic permission to remove parts.',
                          'Contained but nonintersecting geometry is not evaluated by this surface-contact audit; biological containment and acquisition-derived accuracy remain separate requirements.',
                          'Source-defined artery/duct compounds and alternative source versions do not establish exact reporting structure coverage.']}
        payload=(json.dumps(result,indent=2)+'\n').encode();compressed=gzip.compress(payload,compresslevel=9,mtime=0)
        path=output/(parent+'-complete-contacts.json.gz');path.write_bytes(compressed)
        if gzip.decompress(path.read_bytes())!=payload:raise ValueError('Contact evidence compression changed content')
        results.append({'parenchymal_context':parent,'file':path.name,'compressed_sha256':hashlib.sha256(compressed).hexdigest(),
                        'uncompressed_sha256':hashlib.sha256(payload).hexdigest(),'compressed_bytes':len(compressed),'uncompressed_bytes':len(payload),
                        'source_triangle_count':preparation['original_source_triangles'],'testable_triangles':len(f),'invalid_source_triangles':len(preparation['invalid_source_triangles']),
                        'candidate_pairs':contacts['conservative_aabb_candidate_pairs'],'explicitly_tested_pairs':contacts['pairs_explicitly_intersection_tested'],
                        'resolved_noncoplanar_shared_edge_pairs':contacts['noncoplanar_shared_edge_pairs_resolved_geometrically'],
                        'contact_count':contacts['unexpected_contact_count'],'contact_categories':dict(categories),
                        'affected_source_element_pairs':result['affected_source_element_pairs']})
        print(parent,'finished; contacts',contacts['unexpected_contact_count'],'candidate pairs',contacts['conservative_aabb_candidate_pairs'],flush=True)
    (output/'complete-contact-summary.json').write_text(json.dumps({'records':results,'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.source_root,a.output)
