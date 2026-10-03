#!/usr/bin/env python3
"""Audit original HRA renal triangle contacts with exact-coordinate analysis indexing and explicit invalid-source holds."""
import argparse
import gzip
from collections import Counter
import hashlib
import json
from pathlib import Path


def contact_arrays(parts):
    """Prepare an analysis index only; retain every original source face and invalid-face identity."""
    import numpy as np
    vertices=[];faces=[];owners=[];face_ids=[];offset=0
    for part in parts:
        v=np.asarray(part['vertices']);f=np.asarray(part['faces'])
        if v.ndim!=2 or v.shape[1]!=3 or f.ndim!=2 or f.shape[1]!=3 or not np.issubdtype(f.dtype,np.integer) or not np.isfinite(v).all() or not len(f) or f.min()<0 or f.max()>=len(v):raise ValueError('Invalid source triangle arrays')
        vertices.append(v);faces.append(f.astype(np.int64)+offset);owners.extend([part['id']]*len(f));face_ids.extend(range(len(f)));offset+=len(v)
    full_vertices=np.concatenate(vertices);full_faces=np.concatenate(faces)
    positions,inverse=np.unique(full_vertices,axis=0,return_inverse=True);indexed=inverse[full_faces]
    # Metres to millimetres is the declared format unit conversion, never a registration or fitted scale.
    mm=positions.astype(float)*1000;tri=mm[indexed];length=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
    usable=length>1e-18;invalid=[{'source_part':owners[i],'source_face_index':int(face_ids[i]),'source_face_vertices_metres':full_vertices[full_faces[i]].tolist(),
                               'cross_product_norm_mm2':float(length[i]),'reason':'zero_or_numerically_degenerate_source_triangle'} for i in np.flatnonzero(~usable)]
    identities=[{'source_part':owners[i],'source_face_index':int(face_ids[i])} for i in np.flatnonzero(usable)]
    return mm,indexed[usable],identities,{'original_source_triangles':len(full_faces),'numerically_testable_triangles':int(usable.sum()),
        'invalid_source_triangles':invalid,'invalid_source_triangles_removed_from_model':False,'source_positions_changed':False,
        'exact_coordinate_indexing_is_analysis_only':True}


def audit(root,review_root,output):
    from tools.anatomy_sources.inspect_hra_renal_glb import read_glb,accessor
    from tools.anatomy_sources.audit_massp_surface_intersections import inspect
    inputs=[(root/'3d-vh-f-kidney-r.glb','kidney-female-right-v1.3'),(root/'ureter-female-right-v1.2/3d-vh-f-ureter-r.glb','ureter-female-right-v1.2')]
    parts=[];sources=[]
    for path,key in inputs:
        report_path=review_root/(key+'-geometry-inventory.json');report=json.loads(report_path.read_text());raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=report['source_glb_sha256']:raise ValueError('Original source GLB changed')
        d,binary=read_glb(raw)
        for r in report['records']:
            node=d['nodes'][r['node_index']];primitive=d['meshes'][node['mesh']]['primitives'][r['primitive_index']]
            v=accessor(d,binary,primitive['attributes']['POSITION']);indices=accessor(d,binary,primitive['indices']).reshape(-1)
            if hashlib.sha256(v.tobytes()).hexdigest()!=r['position_accessor_sha256'] or hashlib.sha256(indices.tobytes()).hexdigest()!=r['indices_accessor_sha256']:raise ValueError('Source primitive changed')
            parts.append({'id':key+':'+r['node_name'],'vertices':v,'faces':indices.reshape(-1,3)})
        sources.append({'source':key,'source_glb_sha256':report['source_glb_sha256'],'inventory_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest()})
    vertices,faces,identities,preparation=contact_arrays(parts)
    print('Testing',len(faces),'triangles; original invalid source faces retained separately:',len(preparation['invalid_source_triangles']),flush=True)
    contacts=inspect(vertices,faces);categories=Counter();pairs=Counter()
    for row in contacts['unexpected_contacts']:
        a,b=(identities[i] for i in row['face_indices']);row['original_source_faces']=[a,b]
        same=a['source_part']==b['source_part'];row['same_source_part']=same
        categories['within_source_part' if same else 'between_source_parts']+=1;pairs[tuple(sorted([a['source_part'],b['source_part']]))]+=1
    result={'sources':sources,'preparation':preparation,'triangle_contact_audit':contacts,
            'nonshared_or_overlapping_contact_categories':dict(categories),
            'affected_source_part_pairs':[{'parts':list(k),'contact_pairs':n} for k,n in sorted(pairs.items())],
            'standalone_duplicate_pelvis_excluded':True,'all_nonduplicate_source_parts_included':len(parts)==39,
            'source_meshes_edited_repaired_or_fitted':False,'clinical_approval':False,'runtime_promoted':False,
            'status':'held_source_geometry_contacts_and_invalid_triangles_require_review',
            'limits':['Exact-coordinate indexing permits numerical shared vertex/edge adjacency without welding or editing an exported source model.',
                      'All nondegenerate triangles enter conservative candidate and explicit numerical contact checks; original invalid triangle identities remain held, not deleted as a fix.',
                      'Non-shared/overlapping geometric contact is not a pathological finding, proof of anatomy or grounds to remove a tissue layer.',
                      'Metre-to-mm conversion and 1e-9 mm numerical tolerance do not establish acquisition-derived resolution or clinical anatomical accuracy.',
                      'Version/semantic provenance, complete structures, source interfaces and clinical review remain separate holds.']}
    payload=(json.dumps(result,indent=2)+'\n').encode()
    if output.suffix=='.gz':output.write_bytes(gzip.compress(payload,compresslevel=9,mtime=0))
    else:output.write_bytes(payload)
    print('Contacts beyond shared vertex/edge adjacency:',contacts['unexpected_contact_count'],'; candidate pairs',contacts['conservative_aabb_candidate_pairs'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--review-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.source_root,a.review_root,a.output)
