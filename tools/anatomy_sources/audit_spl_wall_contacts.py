#!/usr/bin/env python3
"""Retain every nonordinary self contact and all between-model contacts in original SPL meshes."""
import argparse
from collections import Counter
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import zipfile


def sha(raw):return hashlib.sha256(raw).hexdigest()


def audit(archive,output):
    import numpy as np
    from tools.anatomy_sources.review_spl_wall_source import vtk
    from tools.anatomy_sources.audit_hra_renal_contacts import contact_arrays
    from tools.anatomy_sources.audit_zanatomy_wall_interfaces import candidates,compare_pair
    from tools.anatomy_sources.audit_massp_surface_intersections import TOLERANCE_MM
    source_raw=(output/'independent-wall-source-review.json').read_bytes();source=json.loads(source_raw)
    if sha(archive.read_bytes())!=source['archive_sha256']:raise ValueError('Original independent archive differs')
    parts=[];mapping={};models=[]
    with zipfile.ZipFile(archive) as z:
        for row in source['records']:
            raw=z.read(row['source_member'])
            if sha(raw)!=row['source_vtk_sha256']:raise ValueError('Original strip model changed')
            v,n,f,strips,*_=vtk(raw);identities=[]
            for strip_id,strip in enumerate(strips):
                for local_id in range(len(strip)-2):identities.append({'native_strip_index':strip_id,'triangle_index_within_strip':local_id})
            if len(identities)!=len(f):raise ValueError('Original strip expansion identities differ')
            key=str(row['label_value']);mapping[key]=identities;parts.append({'id':key,'vertices':v,'faces':f})
            models.append({'source_part':key,'source_name':row['source_name'],'source_vtk_sha256':row['source_vtk_sha256'],'native_strip_count':len(strips),'triangles':len(f)})
    vertices,faces,identities,preparation=contact_arrays(parts,source_units='millimetres')
    for identity in identities:identity.update(mapping[identity['source_part']][identity['source_face_index']])
    for identity in preparation['invalid_source_triangles']:identity.update(mapping[identity['source_part']][identity['source_face_index']])
    triangles=vertices[faces];pairs=candidates(triangles);normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
    print('All independent models:',len(triangles),'triangles;',len(pairs),'candidate pairs',flush=True)
    records=[];tested=resolved=ordinary=0
    for number,(a,b) in enumerate(pairs):
        points,same,analytic,allowed=compare_pair(vertices,faces,normals,identities,a,b)
        if analytic:
            resolved+=1
            if same:ordinary+=1;continue
        else:tested+=1
        if points and not allowed:
            records.append({'analysis_face_indices':[int(a),int(b)],'original_source_faces':[identities[a],identities[b]],
                'contact_points_ras_mm':[p.tolist() for p in points],'within_original_model':same,'anatomical_tissue_or_pathology_classified':False})
        elif points:ordinary+=1
        if number and number%200000==0:print('Compared',number,'candidates;',len(records),'retained contacts',flush=True)
    result={'source_review_sha256':sha(source_raw),'source_models':models,'preparation':preparation,'contacts':records,
        'candidate_pairs':len(pairs),'candidate_pairs_int64_sha256':sha(pairs.astype('<i8').tobytes()),'explicitly_tested_pairs':tested,
        'analytically_resolved_shared_edge_pairs':resolved,'ordinary_within_model_adjacency_contacts':ordinary,'comparison_tolerance_mm':TOLERANCE_MM,
        'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
        'limits':['Native strips are expanded only into their defined alternating oriented triangles; no smoothing, repair, pruning or source geometry changes.',
            'Adjacency is allowed only within one original model. Contacts between source labels are retained even at exact shared-coordinate vertices/edges.',
            'Numeric contacts do not approve tissue interfaces, annotation accuracy, clinical diagnosis or full wall coverage. Source models remain non-authoritative derivatives of source labels.']}
    raw=(json.dumps(result,indent=2)+'\n').encode();packed=gzip.compress(raw,mtime=0);file='complete-independent-wall-contacts.json.gz';(output/file).write_bytes(packed)
    counts=Counter(tuple(sorted(i['source_part'] for i in c['original_source_faces'])) for c in records)
    summary={'file':file,'compressed_sha256':sha(packed),'uncompressed_sha256':sha(raw),'source_models':models,
        'all_five_original_models_compared':len(parts)==5,'source_triangles':preparation['original_source_triangles'],
        'testable_triangles':preparation['numerically_testable_triangles'],'invalid_triangles':len(preparation['invalid_source_triangles']),
        'candidate_pairs':len(pairs),'explicitly_tested_pairs':tested,'analytically_resolved_shared_edge_pairs':resolved,
        'contact_count':len(records),'within_model_contacts':sum(c['within_original_model'] for c in records),
        'between_model_contacts':sum(not c['within_original_model'] for c in records),
        'within_models':[{'label_value':m['source_part'],'source_name':m['source_name'],'contact_count':counts[(m['source_part'],m['source_part'])]} for m in models],
        'pairs':[{'label_values':[a,b],'contact_count':counts[(a,b)]} for a,b in itertools.combinations(sorted(mapping),2)],
        'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False}
    (output/'independent-wall-contact-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Complete independent wall contact evidence retained;',len(records),'contacts.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.archive,a.output)
