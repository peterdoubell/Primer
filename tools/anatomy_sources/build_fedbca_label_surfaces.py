#!/usr/bin/env python3
"""Exact labelled-voxel cell boundaries; no fitting, smoothing or contour replacement."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


CASES = [('Center1','001'),('Center2','01'),('Center3','01'),('Center4','01')]


def cell_boundary(mask, affine):
    import numpy as np
    foreground = mask == 1; quads = []
    for axis in range(3):
        u, v = (axis+1)%3, (axis+2)%3
        for sign in [-1,1]:
            neighbour = np.zeros_like(foreground)
            here = [slice(None)]*3; there = [slice(None)]*3
            if sign == 1: here[axis]=slice(None,-1); there[axis]=slice(1,None)
            else: here[axis]=slice(1,None); there[axis]=slice(None,-1)
            neighbour[tuple(here)] = foreground[tuple(there)]
            coords = np.argwhere(foreground & ~neighbour)*2
            if not len(coords):continue
            corners = np.repeat(coords[:,None,:],4,axis=1);corners[:,:,axis]+=sign
            corners[:,:,u]+=np.array([-1,1,1,-1]);corners[:,:,v]+=np.array([-1,-1,1,1])
            if sign < 0:corners=corners[:,[0,3,2,1],:]
            quads.append(corners)
    original = np.concatenate(quads);points,inverse=np.unique(original.reshape(-1,3),axis=0,return_inverse=True)
    gridquads=inverse.reshape(-1,4);faces=np.concatenate([gridquads[:,[0,1,2]],gridquads[:,[0,2,3]]])
    grid=points.astype(float)/2
    positions=np.column_stack([sum(grid[:,k]*affine[j,k] for k in range(3))+affine[j,3] for j in range(3)])
    if np.linalg.det(affine[:3,:3]) < 0:faces=faces[:,[0,2,1]]
    origin=positions.mean(0);tri=positions[faces]-origin
    volume=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
    expected=float(foreground.sum()*abs(np.linalg.det(affine[:3,:3])))
    if not np.isclose(volume,expected,rtol=1e-10,atol=1e-7):raise ValueError('Exact cell volume differs from source labels')
    edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);_,count=np.unique(edges,axis=0,return_counts=True)
    return positions.astype('<f8'),faces.astype('<u4'),{'source_label_voxels':int(foreground.sum()),'original_exposed_cell_faces':len(original),
        'boundary_edges':int((count==1).sum()),'nonmanifold_edges':int((count>2).sum()),'signed_cell_boundary_volume_source_mm3':volume,
        'source_label_cell_volume_source_mm3':expected,'biological_tumour_volume_independently_measured':False,'positions_grid_half_indices':points.tolist()}


def build(root, output):
    import numpy as np
    from scipy import ndimage
    from tools.anatomy_sources.review_fedbca_sources import read_nifti
    raw=gzip.decompress((root/'full-fedbca-review/complete-source-review.json.gz').read_bytes());review=json.loads(raw)
    if review['all_source_files']!=496 or review['source_annotation_files']!=275:raise ValueError('Complete source cohort review required')
    output.mkdir(parents=True,exist_ok=True);rows=[]
    for center,case in CASES:
        image_member=f'{center}/{center}/T2WI/{case}.nii.gz';mask_member=f'{center}/{center}/Annotation/{case}.nii.gz'
        pair=next(p for p in review['complete_table_pairs'] if p['image_member']==image_member and p['mask_member']==mask_member)
        array,affine,header=read_nifti(root/'all-nifti'/mask_member)
        if header['compressed_sha256']!=review['complete_source_records'][mask_member]['compressed_sha256']:raise ValueError('Original annotation changed')
        cc,n=ndimage.label(array==1);sizes=np.bincount(cc.ravel())[1:]
        if np.any(np.concatenate([array.take(i,axis=ax).ravel() for ax in range(3) for i in [0,array.shape[ax]-1]])==1):
            raise ValueError('Source label reaches acquired field edge; no artificial closure allowed')
        positions,faces,proof=cell_boundary(array,affine)
        for idx in np.linspace(0,len(positions)-1,min(len(positions),97),dtype=int):
            grid=np.asarray(proof['positions_grid_half_indices'][idx],float)/2
            independent=[sum(float(affine[j,k])*float(grid[k]) for k in range(3))+float(affine[j,3]) for j in range(3)]
            if not np.allclose(positions[idx],independent,rtol=0,atol=1e-10):raise ValueError('Independent scalar geometry application differs')
        key=center.lower()+'-'+case
        pbytes=positions.tobytes();fbytes=faces.tobytes()
        (output/(key+'-positions.f64.gz')).write_bytes(gzip.compress(pbytes,mtime=0));(output/(key+'-triangles.u32.gz')).write_bytes(gzip.compress(fbytes,mtime=0))
        proof.pop('positions_grid_half_indices')
        row={'case_id':key,'source_image_member':image_member,'source_mask_member':mask_member,'source_fields':pair['source_fields'],
            'source_image_header':review['complete_source_records'][image_member],'source_mask_header':header,
            'source_grid_corner_difference_mm':pair['max_grid_corner_difference_mm'],'selected_source_affines_bit_identical':pair['selected_affines_bit_identical'],
            'components_6_connected':int(n),'component_voxel_counts':sizes.tolist(),'vertices':len(positions),'triangles':len(faces),
            'positions_sha256':hashlib.sha256(pbytes).hexdigest(),'triangles_sha256':hashlib.sha256(fbytes).hexdigest(),
            'bounds_source_NIfTI_RAS':[positions.min(0).tolist(),positions.max(0).tolist()],**proof,
            'source_labels_modified_or_components_deleted':False,'surface_smoothed_decimated_fitted_or_hole_repaired':False,
            'derivation':'Boundary of union of original label1 voxel cells, at integer index centres ±0.5; original mask affine; outward triangle orientation; no source-value changes.',
            'clinical_or_full_reportable_anatomy_approved':False,'runtime_promoted':False}
        rows.append(row);print('Original label-cell boundary reconstructed.',flush=True)
    (output/'source-surface-review.json').write_text(json.dumps(rows,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.root,a.output)
