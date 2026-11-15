#!/usr/bin/env python3
"""Check cross-surface contacts in one registered source frame, without repair."""
import argparse
import hashlib
from itertools import combinations
import json
from pathlib import Path
import numpy as np
from tools.anatomy_sources.audit_massp_surface_intersections import candidate_pairs,triangle_contact,allowed_shared_contact,TOLERANCE_MM


def audit(root,output):
    manifest=json.loads((root/'surface-review.json').read_text());meshes=[]
    for row in manifest['records']:
        path=root/row['mesh_file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row['mesh_sha256']:
            raise ValueError('Source mesh changed')
        with np.load(path) as data:
            vertices=data['vertices'].copy();faces=data['faces'].copy()
        meshes.append((row,vertices,faces))
    records=[]
    for (row_a,v_a,f_a),(row_b,v_b,f_b) in combinations(meshes,2):
        name_a=row_a['code']+'-'+row_a['side'];name_b=row_b['code']+'-'+row_b['side']
        if np.any(np.maximum(v_a.min(0),v_b.min(0))>np.minimum(v_a.max(0),v_b.max(0))+TOLERANCE_MM):
            records.append({'first':name_a,'second':name_b,'disjoint_complete_bounds':True,'candidate_pairs':0,'unexpected_contact_count':0})
            continue
        vertices=np.concatenate([v_a,v_b]);faces=np.concatenate([f_a,f_b+len(v_a)])
        # Exact coincident source positions define a shared interface, without
        # modifying either stored surface or welding vertices in either file.
        _,position_index=np.unique(vertices,axis=0,return_inverse=True)
        geometry_faces=position_index[faces]
        triangles=vertices[faces];pairs=candidate_pairs(triangles)
        pairs=pairs[(pairs[:,0]<len(f_a)) & (pairs[:,1]>=len(f_a))]
        unexpected=[];shared_contacts=separated=opposite_coplanar_interfaces=0
        for a,b in pairs:
            points=triangle_contact(triangles[a],triangles[b])
            if not points:
                separated+=1;continue
            shared_ids=np.intersect1d(geometry_faces[a],geometry_faces[b])
            common=[]
            for ident in shared_ids:
                common.append(vertices[faces[a][np.flatnonzero(geometry_faces[a]==ident)[0]]])
            common=np.array(common).reshape(-1,3)
            if len(common)==3:
                n1=np.cross(triangles[a,1]-triangles[a,0],triangles[a,2]-triangles[a,0])
                n2=np.cross(triangles[b,1]-triangles[b,0],triangles[b,2]-triangles[b,0])
                if float(n1@n2)<0:
                    opposite_coplanar_interfaces+=1;continue
            if allowed_shared_contact(points,common):
                shared_contacts+=1;continue
            unexpected.append({'first_face':int(a),'second_face':int(b-len(f_a)),
                               'coincident_source_vertex_count':len(common),'contact_points_mm':[p.tolist() for p in points]})
        records.append({'first':name_a,'second':name_b,'disjoint_complete_bounds':False,
                        'candidate_pairs':len(pairs),'separated_triangle_pairs':separated,
                        'shared_vertex_or_edge_contacts':shared_contacts,'oppositely_oriented_coincident_triangle_interfaces':opposite_coplanar_interfaces,
                        'unexpected_contact_count':len(unexpected),'unexpected_contacts':unexpected})
        print(name_a,name_b,len(unexpected),flush=True)
    output.write_text(json.dumps({'mesh_manifest_sha256':hashlib.sha256((root/'surface-review.json').read_bytes()).hexdigest(),
                                  'comparison_tolerance_mm':TOLERANCE_MM,'records':records,
                                  'source_meshes_changed':False,'clinical_approval':False,
                                  'limits':'Triangle contact classification in the original atlas frame. Shared exact-position vertices/edges and oppositely oriented coincident triangles are retained as source interfaces; this does not establish clinical boundary accuracy, medullary lamina thickness or absence of continuous subvoxel volumetric overlap.'},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--meshes',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();audit(args.meshes,args.output)
