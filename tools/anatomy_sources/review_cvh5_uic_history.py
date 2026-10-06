#!/usr/bin/env python3
"""Test finite history hypotheses without treating numeric preference as encoder provenance."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.decode_rh_candidate import uic

HISTORIES={'reverse_rank':[(-i)%32 for i in range(32)],'all_zero':[0]*32,
           'forward_rank':list(range(32)),'reverse_rank_plus_one':[(-i)%32+1 for i in range(32)]}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def directions(v,f,indices,normals,mask):
    import numpy as np
    face=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);length=np.linalg.norm(face,axis=1)
    valid=mask&(length>0)
    if not valid.any():return {'faces':0,'median_corner_face_dot':None,'zero_area_faces':int((mask&(length==0)).sum())}
    dot=np.einsum('fci,fi->fc',normals[indices[valid]],face[valid]/length[valid,None]).ravel()
    return {'faces':int(valid.sum()),'median_corner_face_dot':float(np.median(dot)),
            'zero_area_faces':int((mask&(length==0)).sum()),'fraction_corner_dot_above_0_9':float((dot>.9).mean())}


def review(source,candidates,normal_source,output):
    import numpy as np
    inv_raw=(source/'original-model-inventory.json').read_bytes();inv=json.loads(inv_raw)
    original=gzip.decompress((source/'original-model.u3d.gz').read_bytes())
    if sha(original)!=inv['u3d_sha256']:raise ValueError('Source stream differs')
    candidate_raw=(candidates/'candidate-geometry-review.json').read_bytes();candidate=json.loads(candidate_raw)
    normal_raw=(normal_source/'normal-interpretation-review.json').read_bytes();normal=json.loads(normal_raw)
    if candidate['original_u3d_sha256']!=sha(original) or normal['candidate_geometry_review_sha256']!=sha(candidate_raw):raise ValueError('Source links differ')
    records=[]
    for row in candidate['resources']:
        stored=(candidates/row['file']).read_bytes()
        if sha(stored)!=row['sha256']:raise ValueError('Candidate differs')
        m=json.loads(gzip.decompress(stored));nr=next(r for r in normal['resources'] if r['resource_name']==row['resource_name'])
        nstored=(normal_source/nr['file']).read_bytes()
        if sha(nstored)!=nr['sha256']:raise ValueError('Normal candidate differs')
        nn=np.asarray(json.loads(gzip.decompress(nstored))['interpreted_normal_vectors'])
        block=next(c for c in inv['modifier_chains'] if c['chain_type']==1 and c['name']==row['resource_name'])['modifiers'][-1]
        payload=original[block['data_start']:block['data_end']]
        if sha(payload)!=m['source_payload_sha256']:raise ValueError('Resource differs')
        base_v=np.asarray(m['positions']);base_f=np.asarray(m['faces']);base_ni=np.asarray(m['normal_indices']).reshape(-1,3)
        prefix=np.arange(len(base_f))<128
        baseline=directions(base_v,base_f,base_ni,nn,prefix);comparisons=[]
        coded=[(i,b) for i,b in enumerate(m['integer_blocks']) if b['codec']==10]
        for label,history in HISTORIES.items():
            if not coded:
                comparisons.append({'history':label,'status':'not_applicable_no_uic1_blocks'});continue
            v=base_v.copy();f=base_f.copy();ni=base_ni.copy();changed=[]
            try:
                for index,b in coded:
                    t=payload[b['start']];width=(t>>6)+1;size=int.from_bytes(payload[b['start']+1:b['start']+1+width],'little')
                    start=b['start']+1+width;stop=start+size
                    if stop!=b['end'] or sha(payload[b['start']:stop])!=b['source_encoded_span_sha256']:raise ValueError('Encoded span differs')
                    values=uic(payload[start:stop],b['count'],True,initial_values=history)
                    if any(x>b['maximum'] for x in values):raise ValueError('History produces out-of-range source indices or quants')
                    if index<3:
                        control=m['float_blocks'][0]['axis_controls'][index]
                        q=np.asarray(values);v[:,index]=control['minimum']+q*(control['maximum']-control['minimum'])/control['quant_count']
                    elif index==3:f=np.asarray(values).reshape(-1,3)
                    elif index==4:ni=np.asarray(values).reshape(-1,3)
                    else:raise ValueError('Unreviewed source integer role')
                    changed.append({'source_block_start':b['start'],'decoded_values_sha256':sha(np.asarray(values,dtype='<u4').tobytes())})
                if label=='reverse_rank' and (not np.array_equal(f,base_f) or not np.array_equal(ni,base_ni) or not np.allclose(v,base_v,atol=1e-12,rtol=0)):raise ValueError('Default interpretation no longer matches retained candidate')
                vertex_changed=np.any(v!=base_v,axis=1)
                affected=np.any(f!=base_f,axis=1)|np.any(ni!=base_ni,axis=1)|np.any(vertex_changed[f],axis=1)
                comparisons.append({'history':label,'status':'source_ranges_and_spans_accounted','changed_positions':int(vertex_changed.sum()),
                                    'changed_position_index_values':int((f!=base_f).sum()),'changed_normal_index_values':int((ni!=base_ni).sum()),
                                    'affected_faces':int(affected.sum()),'first_128_faces':directions(v,f,ni,nn,prefix),
                                    'affected_face_directions':directions(v,f,ni,nn,affected),'decoded_blocks':changed,
                                    'is_clinical_acceptance_threshold':False})
            except ValueError as error:
                comparisons.append({'history':label,'status':'rejected_by_numeric_decode_constraints','reason':str(error),
                                    'rejection_is_original_source_defect':False})
        records.append({'resource_name':row['resource_name'],'candidate_file_sha256':row['sha256'],'normal_file_sha256':nr['sha256'],
                        'uic1_block_count':len(coded),'baseline_first_128_faces':baseline,'comparisons':comparisons,
                        'bootstrap_independently_verified':False,'clinical_approval':False})
        print('History checks',row['resource_name'],len(coded),flush=True)
    output.mkdir(parents=True,exist_ok=True)
    result={'source_u3d_sha256':sha(original),'source_inventory_sha256':sha(inv_raw),'candidate_review_sha256':sha(candidate_raw),
            'normal_review_sha256':sha(normal_raw),'histories':HISTORIES,'prefix_face_count':128,'resources':records,
            'resource_count':len(records),'finite_hypotheses_are_exhaustive':False,'bootstrap_independently_verified':False,
            'normal_direction_channel_is_independent_original_decoder':False,'source_arrays_changed':False,
            'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (output/'uic-history-review.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--candidates',type=Path,required=True);p.add_argument('--normal-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.source,a.candidates,a.normal_source,a.output)
