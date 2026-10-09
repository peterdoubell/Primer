#!/usr/bin/env python3
"""Locate connectivity-dependent native cube configurations, never repair labels."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy import ndimage

CORNERS=np.array([(x,y,z) for x in (0,1) for y in (0,1) for z in (0,1)])


def cube_components():
    foreground=np.zeros(256,dtype=np.uint8);background=np.zeros(256,dtype=np.uint8)
    for code in range(256):
        cube=np.array([(code>>i)&1 for i in range(8)],dtype=bool).reshape(2,2,2)
        foreground[code]=ndimage.label(cube)[1];background[code]=ndimage.label(~cube)[1]
    return foreground,background


def localize(root,output):
    # Native volume I/O is separate from the reusable numerical cube lookup.
    import nibabel as nib
    output.mkdir(parents=True,exist_ok=True);acquisition=json.loads((root/'acquisition.json').read_text());name='1_CT_HR_label_airways.nii.gz'
    source=next(e for e in acquisition['files'] if e['name']==name);path=root/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:raise ValueError('Source label changed')
    image=nib.load(path);labels=np.asarray(image.dataobj);coords=np.argwhere(labels>0);lo=coords.min(0)-1;hi=coords.max(0)+2
    mask=labels[tuple(slice(a,b) for a,b in zip(lo,hi))]>0;shape=np.array(mask.shape)-1;codes=np.zeros(shape,dtype=np.uint8)
    for index,corner in enumerate(CORNERS):codes|=(mask[tuple(slice(c,c+n) for c,n in zip(corner,shape))].astype(np.uint8)<<index)
    foreground,background=cube_components();ambiguous=(foreground[codes]>1)|(background[codes]>1);origins=np.argwhere(ambiguous)+lo
    values=codes[ambiguous];np.savez_compressed(output/'adjacency-dependent-cubes.npz',native_origins=origins,configuration_codes=values)
    unique,counts=np.unique(values,return_counts=True)
    records=[]
    for code,count in zip(unique,counts):
        records.append({'configuration':int(code),'cube_count':int(count),'foreground_6_components':int(foreground[code]),'background_6_components':int(background[code])})
    # Group nearby configurations by occupied native Z plane for review. This
    # is an index of candidate sites, not a claimed count of anatomical handles.
    planes,zcounts=np.unique(origins[:,2],return_counts=True)
    result={'source_label_sha256':source['sha256'],'source_affine':image.affine.tolist(),'native_bounds_start':lo.tolist(),'native_bounds_stop_exclusive':hi.tolist(),
            'all_native_cubes_checked':int(codes.size),'connectivity_dependent_cube_count':len(origins),'foreground_disconnected_cube_count':int((foreground[codes]>1).sum()),'background_disconnected_cube_count':int((background[codes]>1).sum()),
            'configurations':records,'z_plane_counts':[{'native_z':int(z),'cubes':int(c)} for z,c in zip(planes,zcounts)],
            'location_array_sha256':hashlib.sha256((output/'adjacency-dependent-cubes.npz').read_bytes()).hexdigest(),'source_voxels_changed':False,'clinical_approval':False,
            'limits':'Exhaustive 2x2x2 source-cube adjacency classification. These configurations may explain topology sensitivity but are not one-to-one handles or proof of artefacts/pathology. Original CT/clinical review required.'}
    (output/'adjacency-review.json').write_text(json.dumps(result,indent=2)+'\n');print('Connectivity-dependent cubes:',len(origins),'of',codes.size,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();localize(args.source,args.output)
