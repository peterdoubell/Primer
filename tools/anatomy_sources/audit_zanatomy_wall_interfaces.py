#!/usr/bin/env python3
"""Retain all wall source-instance contacts with explicit native-polygon tessellation limits."""
import argparse
from collections import Counter
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import subprocess


def sha(raw):return hashlib.sha256(raw).hexdigest()


def candidates(triangles):
    """Conservative AABB sweep, avoiding voxel-grid expansion of large fascia faces."""
    import numpy as np
    from tools.anatomy_sources.audit_massp_surface_intersections import TOLERANCE_MM
    low=triangles.min(1);high=triangles.max(1)
    order=np.argsort(low[:,0],kind='stable');active=np.empty(0,dtype=np.int64);rows=[]
    for current in order:
        active=active[high[active,0]+TOLERANCE_MM>=low[current,0]]
        overlap=active[np.all(np.maximum(low[active,1:],low[current,1:])<=np.minimum(high[active,1:],high[current,1:])+TOLERANCE_MM,axis=1)]
        if len(overlap):rows.append(np.sort(np.column_stack([overlap,np.full(len(overlap),current)]),axis=1))
        active=np.append(active,current)
    result=np.concatenate(rows) if rows else np.empty((0,2),dtype=np.int64)
    return result[np.lexsort((result[:,1],result[:,0]))]


def tessellate(root,output,report):
    import numpy as np
    from tools.anatomy_sources.render_zanatomy_wall_source import decode
    from tools.anatomy_sources.review_zanatomy_wall_source import native_polygons
    source=Path(__file__).with_name('export_zanatomy_wall_triangles.c')
    executable=root/'wall_triangles'
    subprocess.run(['clang','-O2','-I'+str(root),str(source),str(root/'ufbx.c'),'-lm','-o',str(executable)],check=True)
    raw=subprocess.check_output([str(executable),str(root/'MuscularSystem100.fbx')]+[str(g['geometry_id']) for g in report['geometries']])
    result=json.loads(raw);by_id={g['geometry_id']:g for g in result['geometries']};arrays={}
    if set(by_id)!={g['geometry_id'] for g in report['geometries']}:raise ValueError('Native tessellation geometry set differs')
    for g in report['geometries']:
        packed=(output/g['file']).read_bytes();payload=gzip.decompress(packed)
        if sha(packed)!=g['compressed_sha256'] or sha(payload)!=g['uncompressed_sha256']:raise ValueError('Native geometry evidence changed')
        e=json.loads(payload);local=np.asarray(decode(e['positions'])).reshape(-1,3)
        encoded=decode(e['polygon_vertex_index']);polygons=native_polygons(encoded,len(local));corner_ids=[int(i) if i>=0 else -int(i)-1 for i in encoded]
        row=by_id[g['geometry_id']];tri=np.asarray(row['triangles'],dtype=np.int64)
        offsets=np.cumsum([0]+[len(p) for p in polygons]);counts=Counter(tri[:,0]);edges={i:Counter() for i in range(len(polygons))}
        if len(tri)!=g['derived_triangulation_count_only'] or row['native_faces']!=len(polygons):raise ValueError('Native face tessellation count differs')
        for fid,a,b,c,va,vb,vc in tri:
            if not all(offsets[fid]<=i<offsets[fid+1] for i in [a,b,c]) or [corner_ids[i] for i in [a,b,c]]!=[va,vb,vc]:raise ValueError('Original face/corner identity differs')
            for x,y in [(va,vb),(vb,vc),(vc,va)]:edges[fid][(int(x),int(y))]+=1
        for fid,p in enumerate(polygons):
            if counts[fid]!=len(p)-2:raise ValueError('Original polygon is incomplete')
            for a,b in zip(p,p[1:]+p[:1]):
                if edges[fid][(a,b)]!=1:raise ValueError('Native oriented boundary differs')
                edges[fid][(a,b)]-=1
            if any(n!=edges[fid][(b,a)] for (a,b),n in edges[fid].items()):raise ValueError('Tessellation internal edges are unpaired')
        arrays[g['geometry_id']]={'local':local,'triangles':tri[:,4:7],'source_face_ids':tri[:,0],'polygons':polygons}
    proof={'geometries':result['geometries'],'exporter_sha256':sha(source.read_bytes()),
        'ufbx_inputs':json.loads((output/'ufbx-acquisition.json').read_text()),
        'source_fbx_sha256':report['source_fbx_sha256'],'native_review_sha256':sha((output/'native-wall-review.json').read_bytes()),
        'all_native_oriented_boundaries_preserved':True,'source_arrays_changed':False,'tessellation_is_anatomically_approved':False}
    raw=(json.dumps(proof,indent=2)+'\n').encode();packed=gzip.compress(raw,mtime=0)
    (output/'analysis-tessellation.json.gz').write_bytes(packed)
    return arrays,sha(raw)



def compare_pair(vertices,faces,normals,identities,a,b):
    import numpy as np
    from tools.anatomy_sources.audit_massp_surface_intersections import triangle_contact,allowed_shared_contact
    same=identities[a]['source_part']==identities[b]['source_part'];shared=np.intersect1d(faces[a],faces[b])
    analytic=len(shared)==2 and np.linalg.norm(np.cross(normals[a],normals[b]))>1e-12
    if analytic:
        return ([] if same else list(vertices[shared])),same,True,same
    points=triangle_contact(vertices[faces[a]],vertices[faces[b]])
    return points,same,False,bool(same and allowed_shared_contact(points,vertices[shared]))


def audit(root,output):
    import numpy as np
    from tools.anatomy_sources.audit_hra_renal_contacts import contact_arrays
    from tools.anatomy_sources.audit_massp_surface_intersections import triangle_contact,allowed_shared_contact,TOLERANCE_MM
    report=json.loads((output/'native-wall-review.json').read_text())
    if sha((root/'MuscularSystem100.fbx').read_bytes())!=report['source_fbx_sha256']:raise ValueError('Pinned original FBX changed')
    arrays,tess_sha=tessellate(root,output,report);parts=[];native={}
    for instance in report['instances']:
        a=arrays[instance['source_geometry_id']];matrix=np.asarray(instance['world_transform_columns']).T
        world=np.column_stack([a['local'],np.ones(len(a['local']))])@matrix.T
        if sha(world.astype('<f8').tobytes())!=instance['world_positions_float64_cm_sha256']:raise ValueError('Source instance transform changed')
        key=str(instance['source_model_id']);parts.append({'id':key,'vertices':world*10,'faces':a['triangles']})
        native[key]={'name':instance['name'],'geometry_id':instance['source_geometry_id'],'source_face_ids':a['source_face_ids']}
    vertices,faces,identities,preparation=contact_arrays(parts,source_units='millimetres')
    for identity in identities:identity['native_face_index']=int(native[identity['source_part']]['source_face_ids'][identity['source_face_index']])
    for identity in preparation['invalid_source_triangles']:identity['native_face_index']=int(native[identity['source_part']]['source_face_ids'][identity['source_face_index']])
    triangles=vertices[faces];pairs=candidates(triangles);print('Conservative candidates',len(pairs),'; testable',len(faces),flush=True)
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
    findings=[];resolved=0;tested=0;ordinary=0
    for count,(a,b) in enumerate(pairs):
        points,same,analytic,allowed=compare_pair(vertices,faces,normals,identities,a,b)
        if analytic:
            resolved+=1
            if same:ordinary+=1;continue
        else:tested+=1
        if points and not allowed:
            findings.append({'analysis_face_indices':[int(a),int(b)],'original_source_faces':[identities[a],identities[b]],
                'contact_points_mm':[p.tolist() for p in points],'within_source_instance':same,
                'same_native_source_geometry':native[identities[a]['source_part']]['geometry_id']==native[identities[b]['source_part']]['geometry_id'],
                'includes_nontriangle_native_polygon':any(len(arrays[native[i['source_part']]['geometry_id']]['polygons'][i['native_face_index']])!=3 for i in [identities[a],identities[b]])})
        elif points:ordinary+=1
        if count and count%200000==0:print('Compared',count,'candidate pairs;',len(findings),'retained contacts',flush=True)
    result={'source_native_review_sha256':sha((output/'native-wall-review.json').read_bytes()),'analysis_tessellation_uncompressed_sha256':tess_sha,
        'preparation':preparation,'comparison_tolerance_mm':TOLERANCE_MM,'candidate_pairs':len(pairs),
        'candidate_pairs_int64_sha256':sha(pairs.astype('<i8').tobytes()),'explicitly_tested_pairs':tested,
        'analytically_resolved_shared_edge_pairs':resolved,'ordinary_within_instance_adjacency_contacts':ordinary,
        'contacts':findings,'source_instances':[{k:v for k,v in i.items() if k!='source_face_ids'}|{'model_id':key} for key,i in native.items()],
        'clinical_approval':False,'source_geometry_changed':False,'runtime_promoted':False,
        'limits':['Original nonplanar fascia polygons have explicit ufbx analysis tessellation; contacts involving them depend on this surface choice.',
            'Ordinary adjacency is allowed only within the same native source instance. All detected between-instance contacts are retained, including exact shared-coordinate edge/point contacts.',
            'Numerical contacts and proximity do not approve tissue boundaries, muscle attachments, hernia pathology or independent patient sides. Invalid analysis triangles are retained as explicit holds, never pruned from source geometry.']}
    raw=(json.dumps(result,indent=2)+'\n').encode();packed=gzip.compress(raw,mtime=0);file='complete-wall-interface-contacts.json.gz';(output/file).write_bytes(packed)
    pair_counts=Counter(tuple(sorted(i['source_part'] for i in c['original_source_faces'])) for c in findings)
    summary={'file':file,'compressed_sha256':sha(packed),'uncompressed_sha256':sha(raw),
        'source_instances':len(parts),'native_faces_across_instances':sum(i['original_polygon_count'] for i in report['instances']),
        'analysis_triangles':preparation['original_source_triangles'],'testable_triangles':preparation['numerically_testable_triangles'],
        'invalid_triangles':len(preparation['invalid_source_triangles']),'candidate_pairs':len(pairs),'explicitly_tested_pairs':tested,
        'analytically_resolved_shared_edge_pairs':resolved,'contact_count':len(findings),
        'within_instance_contacts':sum(c['within_source_instance'] for c in findings),'between_instance_contacts':sum(not c['within_source_instance'] for c in findings),
        'contacts_including_nontriangle_native_polygon':sum(c['includes_nontriangle_native_polygon'] for c in findings),
        'pairs':[{'source_model_ids':[a,b],'contact_count':pair_counts[(a,b)]} for a,b in itertools.combinations(sorted(native),2)],
        'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False}
    (output/'wall-interface-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Complete wall interface evidence retained;',len(findings),'contacts.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.source_root,a.output)
