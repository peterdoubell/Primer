#!/usr/bin/env python3
"""Measure declared colour-domain support only; bounds are not proof of photographic tissue validity."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from tools.anatomy_sources.review_openear_ZETA_geometry import ply

def support(vertices,affine,shape):
    affine=np.asarray(affine,float);shape=np.asarray(shape,int);vertices=np.asarray(vertices,float)
    if affine.shape!=(4,4) or shape.shape!=(3,) or (shape<2).any() or not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3,:3]))<1e-12:raise ValueError('Invalid original colour spatial grid')
    inverse=np.linalg.inv(affine);indices=vertices@inverse[:3,:3].T+inverse[:3,3]
    return np.isfinite(indices).all(1)&((indices>=0)&(indices<=shape-1)).all(1)

def review(root,proof_dir):
    volume_path=proof_dir/'ZETA-original-volume-readback.json';r=json.loads(volume_path.read_text());colour=next(v for v in r['volumes'] if 'Microslicing' in v['member']);A=np.array(colour['equivalent_RAS_affine']);shape=np.array(colour['source_sizes_fastest_first'][1:]);g=json.loads((proof_dir/'ZETA-original-geometry-header-review.json').read_text());rows=[]
    for model in g['meshes']:
        raw=(root/'ZETA-selected'/Path(model['member']).name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=model['original_member_sha256']:raise ValueError('Original mesh changed')
        vertices,faces,_=ply(raw);inside=support(vertices,A,shape)
        rows.append({'member':model['member'],'original_vertices':len(vertices),'vertices_inside_declared_colour_sample_centre_bounds':int(inside.sum()),
            'vertices_outside_declared_colour_bounds':int((~inside).sum()),'supported_vertex_fraction':float(inside.mean()),
            'vertex_fraction_is_not_surface_area_colour_coverage':True,'source_PLY_RAS_assumption_for_non_declared_meshes_requires_registration_review':not bool(model['source_comment_coordinate_declaration']),
            'bounds_alone_establish_valid_raw_photo_tissue_colour':False,'new_colour_values_applied':False})
    proof={'case':'ZETA','source_volume_readback_sha256':hashlib.sha256(volume_path.read_bytes()).hexdigest(),'source_colour_equivalent_RAS_affine':A.tolist(),'source_colour_spatial_shape_xyz':shape.tolist(),
        'valid_colour_support_uses_closed_original_sample_centre_bounds_no_clamping_or_extrapolation':True,'models':rows,
        'source_interpolation_and_padding_vs_actual_original_photo_coverage_independently_resolved':False,
        'source_registration_or_anatomical_colour_validity_approved':False,'clinical_approval':False,'runtime_promoted':False}
    (proof_dir/'ZETA-declared-colour-support-review.json').write_text(json.dumps(proof,indent=2)+'\n');print('Source bounds assessed for all13 meshes; no extrapolation, texture or anatomy approval')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();review(a.source_root,a.proof_dir)
