#!/usr/bin/env python3
"""Classify exact original coincident face contacts and preserve source-pair locations without pruning."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj

def review(output):
    import numpy as np
    source=json.loads((output/'source-identity-review.json').read_text());by_id={r['id']:r for r in source['objects']};payload=gzip.decompress((output/'all-original-source-contacts.json.gz').read_bytes());contacts=json.loads(payload);cache={};within=[]
    def mesh(identifier):
        if identifier not in cache:
            r=by_id[identifier];raw=gzip.decompress((output/r['file']).read_bytes())
            if hashlib.sha256(raw).hexdigest()!=r['sha256']:raise ValueError('Original source changed')
            cache[identifier]=read_obj(raw.decode())
        return cache[identifier]
    for c in contacts['triangle_contact_audit']['unexpected_contacts']:
        if not c['same_original_object']:continue
        identifier=c['original_source_faces'][0]['source_part'];v,n,f,nf=mesh(identifier);indices=[r['source_face_index'] for r in c['original_source_faces']];triangles=v[f[indices]];same=set(map(tuple,triangles[0]))==set(map(tuple,triangles[1]));normal=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None]
        ids=set(np.flatnonzero(np.isin(f,f[indices].ravel()).any(axis=1)));isolated=ids==set(indices);within.append({'source_id':identifier,'source_sha256':by_id[identifier]['sha256'],'source_face_indices':indices,'original_triangle_positions':triangles.tolist(),'exactly_same_triangle_position_set':same,'opposite_face_winding':float(normal[0]@normal[1])<-1+1e-10,'source_face_normal_dot_product':float(normal[0]@normal[1]),'isolated_two_face_component_by_original_indices':isolated,'two_faces_are_resolved_vessel_wall_or_lumen':False,'source_faces_removed_or_repaired':False})
    pair_findings=[]
    for ids in [('FJ2087','FJ2093'),('FJ2172','FJ2197')]:
        selected=[c for c in contacts['triangle_contact_audit']['unexpected_contacts'] if set(r['source_part'] for r in c['original_source_faces'])==set(ids)];points=np.asarray([p for c in selected for p in c['contact_points_mm']]);pair_findings.append({'source_ids':list(ids),'source_labels':[by_id[i]['original_obj_header']['English name'] for i in ids],'numerical_contact_pairs':len(selected),'contact_point_bounds_original':np.stack([points.min(0),points.max(0)]).tolist(),'contact_centroid_original':points.mean(0).tolist(),'duplicated_common_trunk_or_true_biological_connection_verified':False,'intervention_or_disease_inferred':False})
    result={'all_source_contacts_uncompressed_sha256':hashlib.sha256(payload).hexdigest(),'within_object_findings':within,'posterior_tibial_peroneal_pair_findings':pair_findings,'original_source_geometry_changed':False,'zero_volume_components_deleted_as_noise':False,'clinical_approval':False,'runtime_promoted':False};(output/'source-contact-findings-review.json').write_text(json.dumps(result,indent=2)+'\n');print(len(within),'within-object contacts classified;',sum(r['exactly_same_triangle_position_set'] and r['opposite_face_winding'] for r in within),'exact opposite-winding coincident face pairs.',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);review(p.parse_args().output)
