#!/usr/bin/env python3
"""Audit every retained original source object without caps, welding, fitting or identity repair."""
import argparse,gzip,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj,topology

def audit(output):
    import numpy as np
    source=json.loads((output/'source-identity-review.json').read_text());records=[]
    for row in source['objects']:
        raw=gzip.decompress((output/row['file']).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Original source file changed')
        v,n,f,nf=read_obj(raw.decode());unique,inverse=np.unique(v,axis=0,return_inverse=True);areas=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)/2;declared=np.asarray([[float(v) for v in part.split(',')] for part in re.findall(r'\(([^)]+)\)',row['original_obj_header']['Bounds(mm)'])]);bounds=np.stack([v.min(axis=0),v.max(axis=0)])
        records.append({'id':row['id'],'source_file':row['file'],'source_sha256':row['sha256'],'original_vertices':len(v),'original_normals':len(n),'original_triangles':len(f),'original_bounds':bounds.tolist(),'header_bounds_declared_mm':declared.tolist(),'maximum_header_bounds_difference':float(np.abs(bounds-declared).max()),'source_positions_f64_sha256':hashlib.sha256(v.astype('<f8').tobytes()).hexdigest(),'source_face_indices_i64_sha256':hashlib.sha256(f.astype('<i8').tobytes()).hexdigest(),'source_normal_indices_i64_sha256':hashlib.sha256(nf.astype('<i8').tobytes()).hexdigest(),'source_normals_f64_sha256':hashlib.sha256(n.astype('<f8').tobytes()).hexdigest(),'degenerate_triangles':int((areas==0).sum()),'original_index_topology':topology(v,f),'exact_position_analysis_topology':topology(unique,inverse[f]),'exact_position_welding_is_analysis_only':True,'source_geometry_or_topology_repaired':False,'ontology_identity_held':not row['matches_requested_mapping'],'anatomical_vessel_connections_or_wall_volume_verified':False,'self_intersections_independently_audited':False})
        print('Original object audited',row['id'],flush=True)
    report={'source_identity_review_sha256':hashlib.sha256((output/'source-identity-review.json').read_bytes()).hexdigest(),'objects':records,'original_object_count':len(records),'original_triangles':sum(r['original_triangles'] for r in records),'held_identity_ids':[r['id'] for r in records if r['ontology_identity_held']],'source_positions_normals_faces_or_identities_changed':False,'independent_source_physical_calibration_or_patient_frame_verified':False,'native_MRI_registration_or_full_tree_coverage_verified':False,'clinical_approval':False,'runtime_promoted':False}
    (output/'original-geometry-review.json').write_text(json.dumps(report,indent=2)+'\n');print(len(records),'original arterial source objects audited,',report['original_triangles'],'triangles, source defects unchanged.',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);audit(p.parse_args().output)
