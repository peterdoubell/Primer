#!/usr/bin/env python3
"""Compare actual original vertices with independent source layers; do not fit source geometry."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
from tools.anatomy_sources.review_openear_ZETA_geometry import ply
from tools.anatomy_sources.decode_openear_ZETA_volumes import verified_memmap

def review(root,proof_dir):
    p=proof_dir/'ZETA-original-volume-readback.json';volumes=json.loads(p.read_text());seg=next(v for v in volumes['volumes'] if 'Segmentation.seg' in v['member']);bone=next(v for v in volumes['volumes'] if v['member']=='07_3D_Models/Bone.nrrd')
    labels=verified_memmap(root/'ZETA-volume-review/Segmentation.seg.nrrd.raw',seg)
    bone_mask=verified_memmap(root/'ZETA-volume-review/Bone.nrrd.raw',bone)
    models=json.loads((proof_dir/'ZETA-original-geometry-header-review.json').read_text())['meshes'];layers={l['source_name'].casefold():l for l in volumes['original_segmentation_layers']};rows=[]
    for model in models:
        name=Path(model['member']).stem.split('_',1)[-1];layer=layers[name.casefold()];raw=(root/'ZETA-selected'/Path(model['member']).name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=model['original_member_sha256']:raise ValueError('Original mesh changed')
        vertices,faces,_=ply(raw);reviews=[]
        for mask,volume,label in [(labels[:,:,:,layer['original_list_axis_index']],seg,'original_named_list_layer')]+([(bone_mask,bone,'original_standalone_Bone_volume')] if name=='Bone' else []):
            inverse=np.linalg.inv(np.array(volume['equivalent_RAS_affine']));samples=[];outside=0
            for start in range(0,len(vertices),100000):
                points=vertices[start:start+100000].astype(float);xyz=points@inverse[:3,:3].T+inverse[:3,3]
                inside=((xyz>=0)&(xyz<=np.array(mask.shape[::-1])-1)).all(1);outside+=int((~inside).sum())
                values=map_coordinates(mask,xyz[:,::-1].T,order=1,output=np.float64,prefilter=False,mode='constant',cval=np.nan);samples.append(values)
            values=np.concatenate(samples);valid=values[np.isfinite(values)];residual=np.abs(valid-.5)
            reviews.append({'source_mask':label,'every_original_vertex_sampled':len(vertices),'vertices_outside_declared_source_sample_domain':outside,
                'source_binary_field_range':[float(valid.min()),float(valid.max())],'source_binary_field_absolute_residual_50_95_100':np.quantile(residual,[.5,.95,1]).tolist(),
                'binary_field_residual_is_anatomical_distance_or_accuracy':False,'exact_binary_half_interface_equivalence_approved':False})
        row={'member':model['member'],'source_named_segmentation_layer':layer['source_name'],'source_original_list_index':layer['original_list_axis_index'],
             'comparison_coordinate_hypothesis':'Original PLY values interpreted in recorded source RAS frame; no fit or resampling',
             'source_PLY_RAS_declaration_present':bool(model['source_comment_coordinate_declaration']),'reviews':reviews,'full_native_tissue_identity_and_thickness_approved':False}
        rows.append(row);print(name,[(r['source_mask'],r['vertices_outside_declared_source_sample_domain'],r['source_binary_field_absolute_residual_50_95_100']) for r in reviews],flush=True)
    result={'case':'ZETA','source_volume_readback_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'models':rows,'new_geometry_transform_fitting_source_resampling_or_repair_applied':False,
            'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (proof_dir/'ZETA-original-mesh-layer-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();review(a.source_root,a.proof_dir)
