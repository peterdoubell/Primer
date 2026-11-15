#!/usr/bin/env python3
"""Retain experimental encoded-mesh interpretations without clearing decoder/anatomy holds."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.decode_rh_candidate import decode


def sha(raw):return hashlib.sha256(raw).hexdigest()


def review(source,output):
    import numpy as np
    inv_raw=(source/'original-model-inventory.json').read_bytes();inv=json.loads(inv_raw)
    packed=(source/inv['retained_file']).read_bytes();raw=gzip.decompress(packed)
    if sha(raw)!=inv['u3d_sha256'] or sha(packed)!=inv['retained_sha256']:raise ValueError('Original U3D differs')
    output.mkdir(parents=True,exist_ok=True);records=[]
    for number,chain in enumerate(c for c in inv['modifier_chains'] if c['chain_type']==1):
        declared=[b for b in chain['modifiers'] if b['type']=='0x100']
        if len(declared)!=1:raise ValueError('Ambiguous geometry resource')
        block=declared[0];payload=raw[block['data_start']:block['data_end']];mesh=decode(payload)
        if mesh['name']!=chain['name'] or mesh['source_payload_bytes_accounted']!=len(payload):raise ValueError('Incomplete resource accounting')
        mesh['source_u3d_changed']=False;mesh['decoder_interpretation_verified']=False
        mesh['resource_coordinates_scaled_or_fitted']=False
        mesh['source_block_offset']=block['offset'];mesh['source_block_sha256']=block['sha256']
        data=(json.dumps(mesh,indent=2)+'\n').encode();stored=gzip.compress(data,mtime=0);file=f'resource-{number:02d}-candidate.json.gz'
        (output/file).write_bytes(stored)
        v=np.asarray(mesh['positions']);f=np.asarray(mesh['faces'],dtype=np.int64)
        if not np.isfinite(v).all() or f.min()<0 or f.max()>=len(v):raise ValueError('Candidate coordinate/index range differs')
        edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
        zero=int((np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)==0).sum())
        nodes=[n for n in inv['model_nodes'] if n['resource_name']==chain['name']]
        records.append({'resource_name':chain['name'],'source_model_nodes':nodes,'source_payload_sha256':sha(payload),
                        'file':file,'sha256':sha(stored),'uncompressed_sha256':sha(data),
                        'positions':len(v),'triangles':len(f),'declared_normal_count':mesh['counts'][2],
                        'candidate_bounds_native_units':[v.min(0).tolist(),v.max(0).tolist()],
                        'candidate_boundary_edges':int((counts==1).sum()),'candidate_nonmanifold_edges':int((counts>2).sum()),
                        'candidate_zero_area_faces':zero,'source_geometry_defect_diagnosis_granted':False,
                        'normal_attributes_decoded':mesh['normal_attributes_decoded'],
                        'integer_encoding_counts':dict(Counter(b['codec'] for b in mesh['integer_blocks'])),
                        'decoder_interpretation_verified':False,'clinical_approval':False})
        print('Retained candidate',number,chain['name'],len(v),len(f),flush=True)
    result={'source_model_inventory_sha256':sha(inv_raw),'original_u3d_sha256':inv['u3d_sha256'],
            'resources':records,'resource_count':len(records),'positions':sum(r['positions'] for r in records),
            'triangles':sum(r['triangles'] for r in records),'declared_unit_scale_to_metres':inv['file_header']['units_to_metres'],
            'source_u3d_changed':False,'source_vertex_repair_or_smoothing_applied':False,'geometry_scaled_or_fitted':False,
            'decoder_interpretation_verified':False,'normal_attribute_decoding_complete':False,
            'uic1_bootstrap_independently_verified':False,'patient_axes_or_section_registration_verified':False,
            'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False,
            'holds':['UIC1 history initialization is experimental; range and byte checks alone cannot verify its semantics.',
                     'Type-3 normal attributes are retained opaque; candidate face-normal displays cannot substitute for source attributes.',
                     'Source layout differs from incomplete SDK examples in buffer lengths, scalar widths and material/normal field layout.',
                     'Candidate topology findings do not establish original source defects until decoding is independently validated.',
                     'Quantized coordinates cannot restore unavailable precompression authoring samples or acquired anatomical precision.',
                     'Source annotation partitions, clinical anatomy, missing-course completeness and registration remain unapproved.']}
    (output/'candidate-geometry-review.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.source,a.output)
