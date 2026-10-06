#!/usr/bin/env python3
"""Interpret encoded normal angles while retaining whole-decoder and anatomical holds."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.decode_rh_candidate import R


def sha(raw):return hashlib.sha256(raw).hexdigest()


def angle_vectors(alpha,theta,quants):
    import numpy as np
    a=np.asarray(alpha,dtype=float)*(2*np.pi/quants);t=np.asarray(theta,dtype=float)*(2*np.pi/quants)
    return np.column_stack([np.sin(t)*np.cos(a),np.sin(t)*np.sin(a),np.cos(t)])


def review(source,candidates,output):
    import numpy as np
    inv_raw=(source/'original-model-inventory.json').read_bytes();inv=json.loads(inv_raw)
    raw=gzip.decompress((source/'original-model.u3d.gz').read_bytes())
    if sha(raw)!=inv['u3d_sha256']:raise ValueError('Original source differs')
    cand_raw=(candidates/'candidate-geometry-review.json').read_bytes();cand=json.loads(cand_raw)
    if cand['original_u3d_sha256']!=sha(raw):raise ValueError('Candidate source differs')
    output.mkdir(parents=True,exist_ok=True);records=[]
    for number,row in enumerate(cand['resources']):
        packed=(candidates/row['file']).read_bytes()
        if sha(packed)!=row['sha256']:raise ValueError('Candidate arrays differ')
        mesh=json.loads(gzip.decompress(packed));chain=next(c for c in inv['modifier_chains'] if c['chain_type']==1 and c['name']==row['resource_name'])
        block=next(b for b in chain['modifiers'] if b['type']=='0x100');payload=raw[block['data_start']:block['data_end']]
        if sha(payload)!=mesh['source_payload_sha256']:raise ValueError('Source resource differs')
        start=mesh['float_blocks'][-1]['end'];reader=R(payload);reader.p=start
        dtype=reader.u();quants=reader.u(4)
        if dtype!=3 or quants<=0:raise ValueError('Unreviewed normal format')
        count=mesh['counts'][2];q=reader.ints(count*2,quants);end=reader.p
        if end!=mesh['integer_blocks'][3]['start']:raise ValueError('Normal payload accounting differs')
        alpha,theta=q[:count],q[count:];vectors=angle_vectors(alpha,theta,quants)
        lengths=np.linalg.norm(vectors,axis=1)
        if not np.isfinite(vectors).all() or not np.allclose(lengths,1,atol=1e-14,rtol=0):raise ValueError('Invalid interpreted normals')
        v=np.asarray(mesh['positions']);f=np.asarray(mesh['faces']);indices=np.asarray(mesh['normal_indices']).reshape(-1,3)
        if indices.min()<0 or indices.max()>=count:raise ValueError('Candidate normal index range differs')
        face=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);area=np.linalg.norm(face,axis=1);valid=area>0;unit=face[valid]/area[valid,None]
        dots=np.einsum('fci,fi->fc',vectors[indices[valid]],unit).ravel()
        if number==0:
            hypotheses=[]
            for alphabet in [quants,quants+1]:
                alternate=R(payload);alternate.p=start+5;values=np.asarray(alternate.ints(count*2,alphabet-1))
                for layout in ['planar','interleaved']:
                    a,t=(values[:count],values[count:]) if layout=='planar' else (values[::2],values[1::2])
                    for swap in [False,True]:
                        for denominator in [quants,quants+1]:
                            test_vectors=angle_vectors(t,a,denominator) if swap else angle_vectors(a,t,denominator)
                            dot=np.einsum('fci,fi->fc',test_vectors[indices[valid]],unit).ravel()
                            hypotheses.append({'alphabet':alphabet,'layout':layout,'swap':swap,'denominator':denominator,
                                               'median_dot':float(np.median(dot)),'p05_dot':float(np.percentile(dot,5)),
                                               'fraction_above_0_9':float((dot>.9).mean())})
            (output/'development-hypotheses.json').write_text(json.dumps(hypotheses,indent=2)+'\n')
        stats={'nonzero_candidate_faces':int(valid.sum()),'excluded_zero_area_candidate_faces':int((~valid).sum()),
               'median_corner_face_dot':float(np.median(dots)),'p05_corner_face_dot':float(np.percentile(dots,5)),
               'fraction_corner_face_dot_above_0_9':float((dots>.9).mean()),'is_clinical_acceptance_threshold':False}
        data={'resource_name':row['resource_name'],'source_model_nodes':row['source_model_nodes'],
              'source_payload_sha256':sha(payload),'normal_span_start':start,'normal_span_end':end,
              'normal_span_sha256':sha(payload[start:end]),'stored_quants_value':quants,'integer_alphabet_size':quants+1,
              'angle_layout':'planar_alpha_then_theta_single_integer_stream','quantized_alpha':alpha,'quantized_theta':theta,
              'interpreted_normal_vectors':vectors.tolist(),'interpreted_vectors_float64_sha256':sha(vectors.astype('<f8').tobytes()),
              'normal_integer_block':reader.log[0],'face_direction_consistency':stats,
              'normal_attribute_interpretation_verified':False,'whole_decoder_independently_verified':False,
              'original_authoring_normals_restored':False,'anatomical_accuracy_verified':False,
              'source_bytes_changed':False,'clinical_approval':False,'runtime_promoted':False}
        content=(json.dumps(data,indent=2)+'\n').encode();stored=gzip.compress(content,mtime=0);file=f'resource-{number:02d}-normal-candidate.json.gz';(output/file).write_bytes(stored)
        records.append({'resource_name':row['resource_name'],'file':file,'sha256':sha(stored),'uncompressed_sha256':sha(content),
                        'normal_count':count,'normal_span_sha256':data['normal_span_sha256'],**stats,
                        'normal_attribute_interpretation_verified':False,'clinical_approval':False})
        print('Interpreted normals',number,row['resource_name'],count,round(stats['median_corner_face_dot'],4),flush=True)
    result={'original_u3d_sha256':sha(raw),'source_inventory_sha256':sha(inv_raw),'candidate_geometry_review_sha256':sha(cand_raw),
            'resources':records,'resource_count':len(records),'normal_count':sum(r['normal_count'] for r in records),
            'hypothesis_development_resource':'mesh','held_out_resource_count':len(records)-1,
            'candidate_normal_arrays_present':True,'normal_attribute_interpretation_verified':False,
            'whole_decoder_independently_verified':False,'uic1_bootstrap_independently_verified':False,
            'patient_axes_or_section_registration_verified':False,'source_bytes_changed':False,
            'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False,
            'limits':['Face-direction agreement is a numerical consistency check, not independent source decoder or anatomical truth.',
                      'Candidate positions and indices still share an experimental UIC1 bootstrap interpretation.',
                      'Quantized angles cannot restore unavailable precompression authoring normals.',
                      'No coordinate fitting, smoothing, orientation repair or anatomical inference is introduced.']}
    (output/'normal-interpretation-review.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--candidates',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.source,a.candidates,a.output)
