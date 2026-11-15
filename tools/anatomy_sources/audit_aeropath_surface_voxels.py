#!/usr/bin/env python3
"""Full native source-label extent comparison with an offline airway surface."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import nibabel as nib
from tools.anatomy_sources.audit_massp_mesh_voxels import section,raster_section


def audit(root,mesh_root,output):
    manifest=json.loads((mesh_root/'surface-review.json').read_text())
    path=root/manifest['source_annotation_file']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['source_annotation_sha256']:raise ValueError('Annotation changed')
    image=nib.load(path);labels=np.asarray(image.dataobj)
    path=mesh_root/manifest['mesh_file']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['mesh_sha256']:raise ValueError('Surface changed')
    with np.load(path) as mesh:vertices=nib.affines.apply_affine(np.linalg.inv(image.affine),mesh['vertices']);faces=mesh['faces'].copy()
    triangles=vertices[faces];lo=np.floor(vertices.min(0)).astype(int)-1;hi=np.ceil(vertices.max(0)).astype(int)+2
    if np.any(lo<0) or np.any(hi>np.array(labels.shape)):raise ValueError('Model beyond source grid')
    xs=np.arange(lo[0],hi[0]);ys=np.arange(lo[1],hi[1]);rows=[];total=fp=fn=source_total=surface_total=0
    for z in range(lo[2],hi[2]):
        predicted=raster_section(section(triangles,2,z,0,1),xs,ys)
        expected=labels[lo[0]:hi[0],lo[1]:hi[1],z].T>0
        a=int(np.count_nonzero(predicted & ~expected));b=int(np.count_nonzero(expected & ~predicted))
        fp+=a;fn+=b;source_total+=int(expected.sum());surface_total+=int(predicted.sum());total+=expected.size
        rows.append({'native_z_index':z,'source_label_voxels':int(expected.sum()),'surface_interior_voxels':int(predicted.sum()),'false_positive':a,'false_negative':b})
        if z%100==0:print('Source plane',z,flush=True)
    full=int(np.count_nonzero(labels))
    if source_total!=full:raise ValueError('Not every source foreground voxel was compared')
    result={'source_dataset_doi':manifest['source_dataset_doi'],'source_annotation_sha256':manifest['source_annotation_sha256'],'source_surface_sha256':manifest['mesh_sha256'],
            'comparison_start':lo.tolist(),'comparison_stop_exclusive':hi.tolist(),'compared_voxel_centres':total,'full_source_label_voxels':full,
            'surface_interior_voxels':surface_total,'false_positive':fp,'false_negative':fn,'exact_voxel_centre_match':fp==0 and fn==0,
            'planes':rows,'source_data_changed':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':'Export/source consistency at all native voxel centres within complete model bounds; not independent clinical accuracy, subvoxel fidelity, named-branch identity, wall anatomy or complete acquisition coverage.'}
    output.write_text(json.dumps(result,indent=2)+'\n');print(total,fp,fn,full,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--meshes',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();audit(args.source,args.meshes,args.output)
