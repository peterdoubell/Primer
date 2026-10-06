#!/usr/bin/env python3
"""Audit all retained original surface contacts, keeping conflicts and ordinary adjacency distinct."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
from tools.anatomy_sources.audit_hra_renal_contacts import contact_arrays
from tools.anatomy_sources.audit_massp_surface_intersections import inspect

def audit(output):
    source_path=output/'source-identity-review.json';source=json.loads(source_path.read_text());parts=[];metadata={}
    for row in source['objects']:
        raw=gzip.decompress((output/row['file']).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Original object changed')
        v,n,f,nf=read_obj(raw.decode());parts.append({'id':row['id'],'vertices':v,'faces':f});metadata[row['id']]=row
    vertices,faces,identities,preparation=contact_arrays(parts,source_units='millimetres');print('Confirmed live audit: all',len(parts),'original objects,',len(faces),'triangles. Building conservative candidates.',flush=True);result=inspect(vertices,faces);pairs={}
    for contact in result['unexpected_contacts']:
        originals=[identities[index] for index in contact['face_indices']];ids=[r['source_part'] for r in originals];contact['original_source_faces']=originals;contact['same_original_object']=ids[0]==ids[1];contact['includes_identity_held_object']=any(not metadata[i]['matches_requested_mapping'] for i in ids);key=tuple(sorted(ids));pairs[key]=pairs.get(key,0)+1
    proof={'source_identity_review_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),'preparation':preparation,'triangle_contact_audit':result,'source_pair_counts':[{'source_ids':list(k),'numerical_contact_pairs':count,'biological_junction_or_pathology_verified':False} for k,count in sorted(pairs.items())],'all_70_original_objects_included':len(parts)==70,'identity_held_objects_included_only_as_source_evidence':['FJ2127'],'original_geometry_changed_or_repaired':False,'continuous_vessel_lumens_or_wall_layers_verified':False,'native_MRI_patient_registration_verified':False,'clinical_approval':False,'runtime_promoted':False,'limits':['All nondegenerate original triangles enter conservative AABB candidates and explicit contacts, except ordinary noncoplanar shared-edge adjacency resolved analytically.','Exact coincident-position indexing is numerical analysis only, not exported welding, source repair or vessel fusion.','Numerical contact or overlap does not prove a patent biological junction, correct vessel identity or pathological contact.','A stated numerical tolerance is not independent source acquisition resolution or scanner calibration.']}
    payload=(json.dumps(proof,indent=2)+'\n').encode();path=output/'all-original-source-contacts.json.gz';path.write_bytes(gzip.compress(payload,compresslevel=9,mtime=0));summary={'file':path.name,'compressed_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'uncompressed_sha256':hashlib.sha256(payload).hexdigest(),'source_objects':len(parts),'source_triangles':preparation['original_source_triangles'],'testable_triangles':len(faces),'candidate_pairs':result['conservative_aabb_candidate_pairs'],'contact_count':result['unexpected_contact_count'],'within_object_contact_count':sum(c['same_original_object'] for c in result['unexpected_contacts']),'between_object_contact_count':sum(not c['same_original_object'] for c in result['unexpected_contacts']),'held_identity_contact_count':sum(c['includes_identity_held_object'] for c in result['unexpected_contacts']),'source_pair_count':len(pairs),'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False};(output/'source-contact-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);audit(p.parse_args().output)
