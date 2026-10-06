#!/usr/bin/env python3
"""Record source-object separation/proximity at named anatomical transitions without fusing vessels."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj

def box_distance(lo_a,hi_a,lo_b,hi_b):
    import numpy as np
    separation=np.maximum(np.maximum(lo_a-hi_b,lo_b-hi_a),0);return float(np.linalg.norm(separation))

def review(output):
    import numpy as np
    from scipy.spatial import cKDTree
    source=json.loads((output/'source-identity-review.json').read_text());meshes={};by_name={}
    for r in source['objects']:
        raw=gzip.decompress((output/r['file']).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=r['sha256']:raise ValueError('Original source object differs')
        v,n,f,nf=read_obj(raw.decode());used=np.unique(f);vertices=v[used];meshes[r['id']]={'row':r,'vertices':vertices,'original_vertex_indices':used,'tree':cKDTree(vertices),'lo':vertices.min(0),'hi':vertices.max(0),'position_set':set(map(tuple,vertices))}
        if r['matches_requested_mapping']:by_name[r['original_obj_header']['English name']]=r['id']
    # These are explicit review targets, not a source-derived claim of patent biological connections.
    transitions=[('Trunk of {s} femoral artery','{S} popliteal artery','femoral_to_popliteal'),('{S} popliteal artery','Trunk of {s} anterior tibial artery','popliteal_to_anterior_tibial'),('{S} popliteal artery','Trunk of {s} posterior tibial artery','popliteal_to_posterior_tibial_via_actual_trunk_if_present'),('{S} popliteal artery','{S} peroneal artery','popliteal_to_peroneal_via_actual_trunk_if_present'),('Trunk of {s} anterior tibial artery','{S} dorsalis pedis artery','anterior_tibial_to_dorsalis_pedis'),('Trunk of {s} posterior tibial artery','Trunk of {s} medial plantar artery','posterior_tibial_to_medial_plantar'),('Trunk of {s} posterior tibial artery','Trunk of {s} lateral plantar artery','posterior_tibial_to_lateral_plantar'),('{S} dorsalis pedis artery','{S} deep plantar artery','dorsalis_pedis_to_deep_plantar'),('Trunk of {s} lateral plantar artery','{S} plantar arch','lateral_plantar_to_arch'),('{S} deep plantar artery','{S} plantar arch','deep_plantar_to_arch')];pairs=[]
    for side in ['left','right']:
        for first,second,key in transitions:
            names=[t.format(s=side,S=side.capitalize()) for t in [first,second]]
            if any(name not in by_name for name in names):raise ValueError('Review target source label unavailable')
            ids=[by_name[name] for name in names];a,b=[meshes[i] for i in ids];dist,index=b['tree'].query(a['vertices']);i=int(np.argmin(dist));j=int(index[i]);lower=box_distance(a['lo'],a['hi'],b['lo'],b['hi'])
            pairs.append({'side':side,'review_target':key,'source_labels':names,'source_ids':ids,'source_sha256':[m['row']['sha256'] for m in [a,b]],'bounding_box_surface_distance_lower_bound_declared_mm':lower,'nearest_referenced_vertex_pair_distance_upper_bound_declared_mm':float(dist[i]),'closest_original_vertex_indices':[int(a['original_vertex_indices'][i]),int(b['original_vertex_indices'][j])],'closest_source_positions':[a['vertices'][i].tolist(),b['vertices'][j].tolist()],'exact_shared_position_count':len(a['position_set']&b['position_set']),'positive_AABB_bound_proves_these_two_objects_are_disjoint':lower>0,'vertex_distance_is_exact_continuous_surface_distance':False,'direct_biological_junction_or_missing_artery_diagnosed':False,'source_objects_merged_fitted_or_connected':False})
    overlaps=[];groups=source['source_groups']
    for a,b in [('FMA20732','FMA20797'),('FMA20731','FMA20796'),('FMA43917','FMA69515'),('FMA43916','FMA69514')]:
        overlaps.append({'requested_source_groups':[a,b],'source_labels':[source['requested_source_labels'][a],source['requested_source_labels'][b]],'shared_source_ids':sorted(set(groups[a])&set(groups[b])),'shared_membership_is_additional_vessel_or_patent_connection':False})
    proof={'source_identity_review_sha256':hashlib.sha256((output/'source-identity-review.json').read_bytes()).hexdigest(),'pairs':pairs,'requested_source_group_overlap_examples':overlaps,'all_original_source_objects_unchanged':True,'tibioperoneal_trunk_independently_resolved_in_selected_source_objects':False,'native_MRI_patient_registration_or_pathology_verified':False,'clinical_approval':False,'runtime_promoted':False,'limits':['A positive exact AABB lower bound proves these two original triangle objects are spatially separate, not that an actual biological connection or intervening segment is absent.','Nearest referenced vertices give only an upper bound on minimum continuous surface distance. A positive value alone does not prove a gap.','Shared source-group membership reuses the same native object IDs and is not a second artery, resolved branch or independent source sample.','Named transition targets are review questions, not universal variant topology or physiological patency claims.']};(output/'source-junction-proximity-review.json').write_text(json.dumps(proof,indent=2)+'\n');print(len(pairs),'named source transitions reviewed;',sum(r['positive_AABB_bound_proves_these_two_objects_are_disjoint'] for r in pairs),'have positive exact box-separation bounds.',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);review(p.parse_args().output)
