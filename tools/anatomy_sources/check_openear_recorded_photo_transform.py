#!/usr/bin/env python3
"""Compare recorded transform directions using the original template canvas; no registration fitting."""
import argparse,hashlib,json,struct,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

def source_sampling_coordinates(width,height,target_width,target_height,matrix,direction):
    if min(width,height,target_width,target_height)<1:raise ValueError('Invalid original canvas dimensions')
    matrix=np.asarray(matrix,float)
    if matrix.shape!=(3,3) or not np.isfinite(matrix).all() or abs(np.linalg.det(matrix))<1e-12:raise ValueError('Invalid recorded source matrix')
    if direction not in ['raw_to_template','template_to_raw']:raise ValueError('Source transform direction must be explicit')
    y,x=np.mgrid[:target_height,:target_width];canvas=np.stack([(x+.5)*width/target_width-.5,(y+.5)*height/target_height-.5,np.ones_like(x)],axis=-1)
    operator=np.linalg.inv(matrix) if direction=='raw_to_template' else matrix
    coords=canvas@operator.T
    if np.any(abs(coords[:,:,2])<1e-12):raise ValueError('Original projective source coordinates are undefined')
    return coords[:,:,:2]/coords[:,:,2,None]

def check(root,proof_dir):
    source_path=proof_dir/'ZETA-original-photo-reconstruction-review.json';proof=json.loads(source_path.read_text());selected=proof['selected_raw_and_reconstructed_planes'];acquisition=json.loads((proof_dir/'ZETA-original-acquisition.json').read_text());records={r['member']:r for r in acquisition['members']}
    with zipfile.ZipFile(root/'ZETA.zip') as archive:
        name='04_Reconstruction_Microslicing/Materials_for_Reconstruction/Target_Zeta_110.xcf';raw=archive.read(name)
        if hashlib.sha256(raw).hexdigest()!=records[name]['sha256'] or raw[:14]!=b'gimp xcf file\0':raise ValueError('Original XCF template interpretation differs')
        width,height,kind=struct.unpack_from('>3I',raw,14)
    paths=[root/'ZETA-photo-reference'/selected['lossless_original_frame_file'],root/'ZETA-photo-reference'/selected['reconstructed_plane_file']]
    expected=[selected['lossless_original_frame_sha256'],selected['reconstructed_plane_sha256']]
    for path,digest in zip(paths,expected):
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Original decoded display pixels changed')
    original=np.array(Image.open(paths[0]).convert('RGB'));target=np.array(Image.open(paths[1]).convert('RGB'));h,w=target.shape[:2]
    M=np.array(selected['original_transform_matrix']);reviews=[]
    for label,direction in [('recorded_matrix_maps_raw_to_template','raw_to_template'),('recorded_matrix_maps_template_to_raw','template_to_raw')]:
        coords=source_sampling_coordinates(width,height,w,h,M,direction);inside=(coords[:,:,0]>=0)&(coords[:,:,0]<=original.shape[1]-1)&(coords[:,:,1]>=0)&(coords[:,:,1]<=original.shape[0]-1);sampled=np.empty(target.shape,dtype=float)
        for channel in range(3):sampled[:,:,channel]=map_coordinates(original[:,:,channel],np.stack([coords[:,:,1],coords[:,:,0]]),order=1,output=np.float64,prefilter=False,mode='constant',cval=0)
        difference=sampled-target.astype(float);reviews.append({'direction_hypothesis':label,'source_inside_raw_frame_sample_centres':int(inside.sum()),'target_pixels':int(inside.size),
            'RGB_RMS_all_target_pixels':float(np.sqrt(np.mean(difference*difference))),'RGB_mean_absolute_error_all_target_pixels':float(np.mean(np.abs(difference))),
            'RGB_RMS_inside_raw_source_domain':float(np.sqrt(np.mean(difference[inside]**2))),'new_fitted_transform_or_anatomical_geometry_applied':False})
    result={'case':'ZETA','source_photo_review_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),'source_template_member':name,'source_template_sha256':hashlib.sha256(raw).hexdigest(),
        'original_XCF_canvas_width_height':[width,height],'original_XCF_base_type':kind,'selected_original_photo':selected['member'],'selected_reconstructed_layer':selected['nearest_reconstructed_original_layer'],
        'diagnostic_sampling_policy':'Original template canvas and centre-aligned pixel scale; recorded matrix or its inverse only, bilinear diagnostic samples, no fitted translation/rotation/scale.',
        'comparisons':reviews,'exact_author_canvas_resampling_interpolation_and_transform_direction_verified':False,'diagnostic_pixel_difference_is_anatomical_distance_or_accuracy':False,
        'clinical_approval':False,'runtime_promoted':False,'new_texture_or_source_volume_applied':False}
    (proof_dir/'ZETA-recorded-photo-transform-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print('Original template canvas',width,height);print(reviews)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();check(a.source_root,a.proof_dir)
