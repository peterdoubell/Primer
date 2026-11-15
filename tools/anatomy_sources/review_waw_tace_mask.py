#!/usr/bin/env python3
"""Decode the narrowly supported source NRRD mask without editing its values."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re


def decode_mask(data):
    import numpy as np
    if b'\n\n' not in data: raise ValueError('Missing NRRD header boundary')
    header,payload=data.split(b'\n\n',1)
    text=header.decode('ascii');fields={}
    for line in text.splitlines():
        if not line or line.startswith('#') or line.startswith('NRRD'):continue
        if ':=' in line:key,value=line.split(':=',1)
        else:key,value=line.split(':',1)
        if key in fields:raise ValueError('Repeated source header field')
        fields[key]=value.strip()
    if (fields.get('type')!='short' or fields.get('dimension')!='3' or fields.get('encoding')!='gzip'
            or fields.get('endian')!='little' or fields.get('space')!='left-posterior-superior'):
        raise ValueError('Unsupported source mask encoding or coordinates')
    shape=tuple(map(int,fields['sizes'].split()))
    if len(shape)!=3 or any(n<=0 for n in shape):raise ValueError('Invalid dimensions')
    raw=gzip.decompress(payload)
    if len(raw)!=2*shape[0]*shape[1]*shape[2]:raise ValueError('Source voxel byte count differs')
    labels=np.frombuffer(raw,dtype='<i2').reshape(shape,order='F')
    directions=[list(map(float,m.split(','))) for m in re.findall(r'\(([^)]+)\)',fields['space directions'])]
    origin=list(map(float,fields['space origin'].strip('()').split(',')))
    affine=np.eye(4);affine[:3,:3]=np.asarray(directions).T;affine[:3,3]=origin
    if len(directions)!=3 or not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3,:3]))<1e-12:
        raise ValueError('Invalid source geometry')
    return labels,affine,fields


def review(path,output):
    import numpy as np
    data=path.read_bytes();labels,affine,fields=decode_mask(data);points=np.argwhere(labels>0)
    values=np.unique(labels)
    if not len(points) or set(values)!={0,1}:raise ValueError('Source binary selection differs')
    extent=list(map(int,fields['Segment0_Extent'].split()))
    measured=[int(v) for pair in zip(points.min(0),points.max(0)) for v in pair]
    if extent!=measured:raise ValueError('Original declared extent and decoded voxels differ')
    record={'source_doi':'10.5281/zenodo.12741586','patient_id':'10','source_phase_index':'2',
      'mask_file':path.name,'mask_sha256':hashlib.sha256(data).hexdigest(),'source_shape_ijk':list(labels.shape),
      'source_affine_lps':affine.tolist(),'source_spacing_mm':np.linalg.norm(affine[:3,:3],axis=0).tolist(),
      'positive_voxels':len(points),'source_label_values':values.tolist(),'declared_and_verified_extent_ijk':extent,
      'source_segment_name':fields.get('Segment0_Name'),'source_segment_tags':fields.get('Segment0_Tags'),
      'original_ct_acquired':False,'source_ct_mask_grid_match_verified':False,'phase_name_assigned':False,
      'source_values_changed':False,'commercial_reuse_cleared':False,'clinical_approval':False,'runtime_promoted':False,
      'limits':['Publisher describes expert correction after interpolation and 3 mm Gaussian smoothing; these are processed boundary labels, not unsmoothed measured capsule/feature extent.',
                'Numeric phase index is retained; exact source CT and explicit code/phase correspondence still require verification.',
                'Generic Tissue and inprogress export tags are source metadata, not a diagnosis or independent final-review approval.',
                'Native CT geometry, clinical boundary accuracy and competing reuse wording remain unresolved.']}
    output.write_text(json.dumps(record,indent=2)+'\n');print('Source mask voxels',len(points),'shape',labels.shape,'extent',extent)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mask',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.mask,a.output)
