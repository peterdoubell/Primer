#!/usr/bin/env python3
"""Audit the author-published paired CT/CTV example; risk regions are not individual lymph nodes."""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy import ndimage
from skimage.measure import marching_cubes
from tools.anatomy_sources.review_hvsmr2_pat7_source import read_nifti
LABELS={1:'Right II+III+Va target region',2:'Left II+III+Va target region',3:'Right IV+Vb target region',4:'Left IV+Vb target region',5:'Right Ib target region',6:'Left Ib target region'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def review(root,proof_dir):
    proof_dir.mkdir(parents=True,exist_ok=True)
    surface_dir=root/'public-example-derived-review';surface_dir.mkdir(parents=True,exist_ok=True)
    acquisition=json.loads((proof_dir/'LNCTVSeg-original-example-acquisition.json').read_text());files={r['file']:r for r in acquisition['public_example_original_blobs']};source=root/'LNCTVSeg-original-example';rows=[];arrays={}
    for name in ['lnctvseg0001_0000.nii.gz','lnctvseg0001_0001.nii.gz','lnctvseg0001.nii.gz']:
        raw=(source/name).read_bytes()
        if sha(raw)!=files[name]['sha256']:raise ValueError('Original public example bytes changed')
        data,A,h=read_nifti(source/name);independent=nib.load(source/name)
        if not np.array_equal(data,independent.dataobj.get_unscaled()) or not np.allclose(A,independent.affine,rtol=0,atol=1e-7):raise ValueError('Independent source sample/affine readback differs')
        q=independent.get_qform()
        if h['qform_code']>0 and not np.allclose(A,q,rtol=0,atol=1e-5):raise ValueError('Original qform and sform disagree')
        if h['slope'] not in (0,1) or h['intercept']!=0:raise ValueError('Review requires unscaled source CT and labels')
        rows.append({'file':name,'source_file_sha256':sha(raw),'all_original_samples_match_independent_nibabel':True,'source_qform_sform_correspondence_checked':True,**h});arrays[name]=(data,A)
    noncontrast,A=arrays['lnctvseg0001_0000.nii.gz'];contrast,B=arrays['lnctvseg0001_0001.nii.gz'];mask,C=arrays['lnctvseg0001.nii.gz']
    if noncontrast.shape!=contrast.shape or mask.shape!=contrast.shape or not np.array_equal(A,B) or not np.array_equal(A,C):raise ValueError('Original public example arrays do not share declared grid')
    if set(np.unique(mask).tolist())!=set(range(7)):raise ValueError('Original target label set differs')
    targets=[]
    for value,name in LABELS.items():
        region=mask==value;components,n=ndimage.label(region,ndimage.generate_binary_structure(3,1));sizes=np.bincount(components.ravel())[1:];locations=np.where(region)
        vertices,faces,_,_=marching_cubes(region.astype(np.uint8),level=.5,allow_degenerate=True)
        positions=vertices.astype(np.float64)@A[:3,:3].T+A[:3,3]
        edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
        _,counts=np.unique(edges,axis=0,return_counts=True)
        pos=positions.astype('<f8').tobytes();tri=faces.astype('<u4').tobytes()
        for suffix,raw in [('positions.f64.gz',pos),('triangles.u32.gz',tri)]:
            target=surface_dir/f'target{value}-{suffix}';target.write_bytes(gzip.compress(raw,mtime=0))
            if gzip.decompress(target.read_bytes())!=raw:raise ValueError('Derived array write/readback differs')
        targets.append({'source_value':value,'source_target_name':name,'voxels':int(region.sum()),'six_neighbour_components':int(n),'component_sizes_descending':sorted(sizes.tolist(),reverse=True),'source_bounds_xyz_inclusive':[[int(v.min()),int(v.max())] for v in locations],'source_components_filtered_or_repaired':False,
            'vertices':len(vertices),'triangles':len(faces),'positions_sha256':sha(pos),'triangles_sha256':sha(tri),'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),'source_sform_bounds':np.stack([positions.min(0),positions.max(0)]).tolist()})
    proof={'case':'lnctvseg0001','source_acquisition_sha256':sha((proof_dir/'LNCTVSeg-original-example-acquisition.json').read_bytes()),'original_files':rows,'source_role_statements':{'lnctvseg0001_0000.nii.gz':'Author readme: non-contrast CT','lnctvseg0001_0001.nii.gz':'Author readme: contrast-enhanced CT; actual phase/timing not supplied'},
        'same_original_declared_grid_verified':True,'source_CT_arrays_are_byte_identical_samples':bool(np.array_equal(noncontrast,contrast)),'source_CT_arrays_are_independently_raw_DICOM_registered_or_HU_calibrated':False,
        'source_targets':targets,'original_target_regions_are_individual_node_cortex_hilum_capsule_or_ENE_geometry':False,'source_samples_registered_resampled_relabelled_or_repaired':False,
        'source_frame':list(nib.aff2axcodes(A)),'derivation':'All original per-class binary masks; level 0.5 Lewiner isosurfaces transformed only by original sform. No padding, fitting, smoothing, decimation, class merge or component deletion. Surface interfaces and caps are target-region annotation boundaries, not node walls.',
        'public_repository_example_data_license_independently_cleared':False,
        'source_semantics':{'primary_article':'https://pmc.ncbi.nlm.nih.gov/articles/PMC11452638/','article_license':'CC BY-NC-ND 4.0','dataset_license':'CC BY 4.0','repository_software_license':'GPL-3.0',
            'lower_neck_label_discrepancy':{'repository_labels_3_4':'IV+Vb','article_table_2_labels_3_4':'IV+Vb+Vc','resolved':False},
            'CTV_map_is_unmodified_universal_surgical_or_2013_consensus_map':False,'CTV_independent_sublevels_recovered_from_combined_masks':False,
            'source_anonymization':'Paper reports blurred facial regions and removal of personal metadata; no claim of untouched whole-head geometry.'},
        'source_declared_sampling_is_adequate_for_all_tiny_nodal_wall_or_neural_structures':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (proof_dir/'LNCTVSeg-original-example-volume-review.json').write_text(json.dumps(proof,indent=2)+'\n');print('Original scalar samples checked',sum(np.prod(r['dimensions']) for r in rows));print([(r['source_value'],r['voxels'],r['six_neighbour_components']) for r in targets])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();review(a.source_root,a.proof_dir)
