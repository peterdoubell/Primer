#!/usr/bin/env python3
"""Audit every testable original pancreatic triangle, preserving invalid source faces."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path


def audit(root,output):
    from tools.anatomy_sources.inspect_hra_renal_glb import read_glb,accessor
    from tools.anatomy_sources.audit_hra_renal_contacts import contact_arrays
    from tools.anatomy_sources.audit_massp_surface_intersections import inspect
    summary=[]
    for sex in ['female','male']:
        key='pancreas-'+sex+'-v1.3';inventory_path=output/(key+'-original-primitives.json');inventory=json.loads(inventory_path.read_text())
        raw=(root/key/('3d-vh-'+sex[0]+'-pancreas.glb')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=inventory['source_glb_sha256']:raise ValueError('Original GLB changed')
        doc,binary=read_glb(raw);parts=[]
        for r in inventory['records']:
            node=doc['nodes'][r['node_index']];p=doc['meshes'][node['mesh']]['primitives'][r['primitive_index']]
            vertices=accessor(doc,binary,p['attributes']['POSITION']);indices=accessor(doc,binary,p['indices']).reshape(-1)
            if hashlib.sha256(vertices.tobytes()).hexdigest()!=r['position_accessor_sha256'] or hashlib.sha256(indices.tobytes()).hexdigest()!=r['indices_accessor_sha256']:
                raise ValueError('Original primitive changed')
            parts.append({'id':r['node_name'],'vertices':vertices,'faces':indices.reshape(-1,3)})
        vertices,faces,identities,preparation=contact_arrays(parts)
        print('Testing original anatomy source triangles.',flush=True)
        contacts=inspect(vertices,faces);categories=Counter();part_pairs=Counter()
        for row in contacts['unexpected_contacts']:
            a,b=(identities[i] for i in row['face_indices']);row['original_source_faces']=[a,b]
            row['same_source_part']=a['source_part']==b['source_part']
            categories['within_source_part' if row['same_source_part'] else 'between_source_parts']+=1
            part_pairs[tuple(sorted([a['source_part'],b['source_part']]))]+=1
        result={'sex':sex,'version':'v1.3','source_glb_sha256':inventory['source_glb_sha256'],
                'source_inventory_sha256':hashlib.sha256(inventory_path.read_bytes()).hexdigest(),'source_part_ids':[p['id'] for p in parts],
                'all_five_source_regions_included':len(parts)==5,'preparation':preparation,'triangle_contact_audit':contacts,
                'nonshared_or_overlapping_contact_categories':dict(categories),
                'affected_source_part_pairs':[{'parts':list(k),'contact_pairs':n} for k,n in sorted(part_pairs.items())],
                'source_geometry_edited_repaired_or_fitted':False,'clinical_approval':False,'runtime_promoted':False,
                'status':'held_for_source_topology_and_independent_anatomical_review',
                'limits':['Original Float32 coordinates/index identities are preserved; exact-coordinate indexing and metre-to-mm conversion are analysis only.',
                          'Every nondegenerate original triangle enters conservative candidates and explicit numerical checks; invalid faces are retained with original identity, not removed from the model.',
                          'Shared vertex/edge adjacency is distinguished from contacts beyond that adjacency; contacts do not establish pathological invasion or biological interface intent.',
                          'The 1e-9 mm numerical tolerance does not describe source acquisition resolution or clinical anatomical accuracy.',
                          'Boundary defects, region partition provenance, full reporting structures and independent clinical review remain separate holds.']}
        payload=(json.dumps(result,indent=2)+'\n').encode();compressed=gzip.compress(payload,compresslevel=9,mtime=0)
        path=output/(key+'-complete-contacts.json.gz');path.write_bytes(compressed)
        assert gzip.decompress(path.read_bytes())==payload
        summary.append({'sex':sex,'file':path.name,'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'uncompressed_sha256':hashlib.sha256(payload).hexdigest(),
                        'compressed_bytes':len(compressed),'uncompressed_bytes':len(payload),'original_source_triangles':preparation['original_source_triangles'],
                        'testable_triangles':preparation['numerically_testable_triangles'],'held_invalid_triangles':len(preparation['invalid_source_triangles']),
                        'candidate_pairs':contacts['conservative_aabb_candidate_pairs'],'explicitly_tested_pairs':contacts['pairs_explicitly_intersection_tested'],
                        'shared_edge_nonparallel_pairs':contacts['noncoplanar_shared_edge_pairs_resolved_geometrically'],
                        'contact_count':contacts['unexpected_contact_count'],'contact_categories':dict(categories),'affected_part_pairs':result['affected_source_part_pairs']})
        print('Complete anatomy contact evidence preserved.',flush=True)
    (output/'complete-contact-summary.json').write_text(json.dumps({'records':summary,'source_meshes_changed':False,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.source_root,a.output)
