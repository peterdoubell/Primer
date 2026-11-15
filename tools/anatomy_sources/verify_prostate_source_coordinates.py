#!/usr/bin/env python3
"""Check source STL/SEG correspondence in the delivered T2 frame without fitting."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from tools.anatomy_sources.review_prostate_biopsy0001 import binary_stl,OUT,SOURCE

def raster_at_source_centres(corners,affine,shape):
    """Independent half-open triangle/plane and scanline-parity containment."""
    inverse=np.linalg.inv(np.asarray(affine,float))
    pts=np.asarray(corners,float)@inverse[:3,:3].T+inverse[:3,3]
    result=np.zeros(shape,'u1');a=pts[:,[0,1,2],:];b=pts[:,[1,2,0],:]
    for sl in range(shape[0]):
        crossing=((a[:,:,0]<=sl)&(sl<b[:,:,0]))|((b[:,:,0]<=sl)&(sl<a[:,:,0]))
        indices=np.flatnonzero(crossing.sum(1)==2);aa=a[indices];bb=b[indices]
        alpha=np.divide(sl-aa[:,:,0],bb[:,:,0]-aa[:,:,0],out=np.zeros(aa.shape[:2]),where=bb[:,:,0]!=aa[:,:,0])
        segments=(aa+(bb-aa)*alpha[:,:,None])[:,:,1:][crossing[indices]].reshape(-1,2,2)
        if not len(segments):continue
        p=segments[:,0];q=segments[:,1]
        for row in range(shape[1]):
            crossed=((p[:,0]<=row)&(row<q[:,0]))|((q[:,0]<=row)&(row<p[:,0]))
            p0=p[crossed];q0=q[crossed]
            xs=p0[:,1]+(row-p0[:,0])/(q0[:,0]-p0[:,0])*(q0[:,1]-p0[:,1])
            result[sl,row]=np.count_nonzero(xs[:,None]>np.arange(shape[2])[None,:],axis=0)%2
    return result

def distance_to_original_triangles(points,corners):
    """Euclidean source-coordinate distance, not biological boundary error."""
    a,b,c=np.moveaxis(np.asarray(corners,float),1,0);v0=b-a;v1=c-a
    normal=np.cross(v0,v1);n2=np.einsum('ij,ij->i',normal,normal)
    if np.any(n2==0):raise ValueError('Degenerate original source face')
    d00=np.einsum('ij,ij->i',v0,v0);d01=np.einsum('ij,ij->i',v0,v1);d11=np.einsum('ij,ij->i',v1,v1);denom=d00*d11-d01*d01
    distances=[]
    for point in np.asarray(points,float):
        v2=point-a;dot=np.einsum('ij,ij->i',v2,normal);proj=v2-normal*(dot/n2)[:,None]
        d20=np.einsum('ij,ij->i',proj,v0);d21=np.einsum('ij,ij->i',proj,v1)
        u=(d11*d20-d01*d21)/denom;v=(d00*d21-d01*d20)/denom;inside=(u>=0)&(v>=0)&(u+v<=1)
        best=np.where(inside,np.abs(dot)/np.sqrt(n2),np.inf)
        for start,end in [(a,b),(b,c),(c,a)]:
            edge=end-start;fraction=np.clip(np.einsum('ij,ij->i',point-start,edge)/np.einsum('ij,ij->i',edge,edge),0,1)
            best=np.minimum(best,np.linalg.norm(point-start-fraction[:,None]*edge,axis=1))
        distances.append(float(best.min()))
    return np.array(distances)

def verify():
    review=json.loads((OUT/'original-source-review.json').read_text());t2=next(r for r in review['MRI_series'] if r['role']=='T2')
    affine=np.array(t2['geometry']['index_to_dicom_lps_mm']);shape=t2['geometry']['shape'];rows=[]
    for role in ['prostate','suspicious_target1']:
        raw=(OUT/(role+'-original.stl')).read_bytes();corners=binary_stl(raw)['vertices']
        source=np.fromfile(SOURCE/(role+'-derived-SEG-u8.bin'),'u1').reshape(shape)
        declared=next(r for r in review['derived_segmentations'] if r['role']==role)
        if hashlib.sha256(source.tobytes()).hexdigest()!=declared['stored_samples_sha256']:raise ValueError('Source mask changed')
        independent=raster_at_source_centres(corners,affine,shape);different=np.argwhere(independent!=source)
        world=different@affine[:3,:3].T+affine[:3,3];distances=distance_to_original_triangles(world,corners)
        intersection=int(np.count_nonzero(independent&source));dice=2*intersection/(int(independent.sum())+int(source.sum()))
        row={'role':role,'original_STL_sha256':hashlib.sha256(raw).hexdigest(),'all_original_voxel_centres_compared':int(np.prod(shape)),
             'source_foreground':int(source.sum()),'independent_foreground':int(independent.sum()),'mismatched_voxel_centres':len(different),
             'Dice':dice,'maximum_mismatch_distance_source_coordinate_units':float(distances.max()) if len(distances) else 0,
             'mismatch_voxel_indices_sha256':hashlib.sha256(different.astype('<u4').tobytes()).hexdigest(),
             'actor_fit_flip_resample_or_repair_applied':False,'every_source_mask_value_and_original_face_retained':True,
             'agreement_is_anatomical_or_histological_accuracy':False}
        if dice<.99 or row['maximum_mismatch_distance_source_coordinate_units']>.5:raise ValueError('Source association needs additional investigation')
        rows.append(row)
    proof={'reviewed_on':'2026-10-08','source_frame':'Delivered shared MRI/M3D/SEG DICOM LPS frame; source transforms unchanged',
           'DICOM_STL_frame_meaning_source':'https://dicom.nema.org/medical/dicom/2022e/output/chtml/part03/sect_A.85.html',
           'DICOM_model_units_requirement_source':'https://dicom.nema.org/medical/dicom/2022e/output/chtml/part03/sect_C.35.html',
           'historical_Slicer_5_4_default_LPS_source':'https://raw.githubusercontent.com/Slicer/Slicer/v5.4.0/Libs/MRML/Core/vtkMRMLModelStorageNode.cxx',
           'producer_conversion_commit':'8d0af5ec221ad6c92e12f66e515ce17feecc4ab2',
           'source_original_model_measurement_units_code_missing':True,
           'source_model_full_DICOM_IOD_conformance_claimed':False,
           'display_millimetre_scale_basis':'Inference from the producer-delivered MRI/SEG affine and numeric STL/SEG correspondence; not an encoded STL unit tag',
           'source_MRI_model_frame_association_numerically_verified':True,
           'source_clinical_native_registration_or_fine_tissue_accuracy_independently_approved':False,
           'comparison':rows,'actor_registration_transform_applied':np.eye(4).tolist(),
           'mismatch_source_masks_changed_or_replaced':False,'source_US_registration_verified':False,
           'clinical_anatomical_or_full_reporting_approval_granted':False}
    (OUT/'coordinate-correspondence-review.json').write_text(json.dumps(proof,indent=2)+'\n')
    (OUT/'coordinate-authority-acquisition.json').write_bytes((SOURCE/'coordinate-authority-acquisition.json').read_bytes())
    print([(r['role'],r['mismatched_voxel_centres'],r['maximum_mismatch_distance_source_coordinate_units']) for r in rows])
    return proof

if __name__=='__main__':verify()
