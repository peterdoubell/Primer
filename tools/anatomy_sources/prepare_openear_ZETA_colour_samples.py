#!/usr/bin/env python3
"""Prepare bounded source-reconstructed RGB samples, never extrapolate outside original volume."""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
from tools.anatomy_sources.decode_openear_ZETA_volumes import verified_memmap
from tools.anatomy_sources.review_openear_ZETA_geometry import ply
from tools.anatomy_sources.review_openear_colour_support import support

def sample(volume,vertices,affine):
    if volume.ndim!=4 or volume.shape[-1]!=3 or volume.dtype!=np.uint8:raise ValueError('Original three-channel source vector required')
    shape=np.array(volume.shape[:3][::-1]);valid=support(vertices,affine,shape);inverse=np.linalg.inv(affine)
    colors=np.full((len(vertices),3),128,dtype=np.uint8)
    if valid.any():
        xyz=np.asarray(vertices[valid],float)@inverse[:3,:3].T+inverse[:3,3]
        values=np.stack([map_coordinates(volume[:,:,:,c],xyz[:,::-1].T,order=1,output=np.float64,prefilter=False,mode='constant',cval=np.nan) for c in range(3)],axis=1)
        if not np.isfinite(values).all() or (values<0).any() or (values>255).any():raise ValueError('Original bounded source colour sample invalid')
        colors[valid]=np.rint(values).astype(np.uint8)
    return colors,valid

def prepare(root,proof_dir,out):
    p=proof_dir/'ZETA-original-volume-readback.json';volumes=json.loads(p.read_text());record=next(v for v in volumes['volumes'] if 'Microslicing' in v['member']);volume=verified_memmap(root/'ZETA-volume-review/Microslicing_Zeta.nrrd.raw',record);affine=np.array(record['equivalent_RAS_affine']);models=json.loads((proof_dir/'ZETA-original-geometry-header-review.json').read_text())['meshes'];rows=[];out.mkdir(parents=True,exist_ok=True)
    for model in models:
        raw=(root/'ZETA-selected'/Path(model['member']).name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=model['original_member_sha256']:raise ValueError('Original source mesh changed')
        vertices,faces,_=ply(raw);colors=[];valids=[]
        for first in range(0,len(vertices),100000):
            rgb,valid=sample(volume,vertices[first:first+100000],affine);colors.append(rgb);valids.append(valid)
        colors=np.concatenate(colors);valid=np.concatenate(valids);name=Path(model['member']).stem;rgb_path=out/(name+'-source-RGB.u8.gz');valid_path=out/(name+'-source-support.u8.gz');rgb_path.write_bytes(gzip.compress(colors.tobytes(),mtime=0));valid_path.write_bytes(gzip.compress(valid.astype(np.uint8).tobytes(),mtime=0))
        if gzip.decompress(rgb_path.read_bytes())!=colors.tobytes() or gzip.decompress(valid_path.read_bytes())!=valid.astype(np.uint8).tobytes():raise ValueError('Written RGB/support sample readback differs')
        # Display rule: colour only faces wholly inside the original convex sample domain.
        fully_supported=valid[faces].all(axis=1)
        row={'member':model['member'],'source_mesh_sha256':model['original_member_sha256'],'original_vertices':len(vertices),'original_triangles':len(faces),
            'RGB_file':rgb_path.name,'RGB_gzip_sha256':hashlib.sha256(rgb_path.read_bytes()).hexdigest(),'RGB_decoded_sha256':hashlib.sha256(colors.tobytes()).hexdigest(),
            'support_file':valid_path.name,'support_gzip_sha256':hashlib.sha256(valid_path.read_bytes()).hexdigest(),'support_decoded_sha256':hashlib.sha256(valid.astype(np.uint8).tobytes()).hexdigest(),
            'vertices_inside_declared_colour_domain':int(valid.sum()),'vertices_outside_declared_colour_domain':int((~valid).sum()),
            'whole_triangles_inside_declared_colour_domain':int(fully_supported.sum()),'triangles_requiring_neutral_display':int((~fully_supported).sum()),
            'whole_triangle_count_is_not_measured_surface_area_coverage':True,'neutral_RGB_for_unsupported_vertices':[128,128,128],
            'RAS_interpretation_for_non_declared_meshes_still_requires_registration_review':not bool(model['source_comment_coordinate_declaration']),
            'anatomically_valid_raw_photo_support_approved':False,'source_geometry_modified':False}
        rows.append(row);print(name,'source samples',int(valid.sum()),'neutral faces',row['triangles_requiring_neutral_display'],flush=True)
    proof={'case':'ZETA','source_volume_readback_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_reconstructed_RGB_volume_sha256':record['decoded_sha256'],
        'source_equivalent_RAS_affine':affine.tolist(),'sampling':'Trilinear source-reconstructed vector RGB, rounded to uint8; no coordinate clamping or extrapolation. Source interpolation and preparation retained.',
        'models':rows,'all_original_mesh_triangles_retained':sum(r['original_triangles'] for r in rows),'source_geometry_fitting_smoothing_decimation_or_repair_applied':False,
        'source_reconstructed_RGB_is_exact_raw_or_in_vivo_tissue_colour_approved':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (proof_dir/'ZETA-source-colour-sample-review.json').write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.source_root,a.proof_dir,a.output)
