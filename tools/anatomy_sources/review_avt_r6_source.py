#!/usr/bin/env python3
"""Inspect original AVT R6 CT/mask and retain a source-mask surface as an unapproved derivative."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.review_aaa_kinematic_source import grid_transform

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'docs/avt-r6-native-source-review'
CT_SHA='2931246e0eab752244389d502dd798dd3414a25b54eb1b2f625f43d3f28f5ccd'
MASK_SHA='2d5609646c808646dab10343ae56046c9613e35b5c98b2917ec88682415f335f'
META_SHA='04f2388838d5e91ad3e218c23baddc657ca2998c4f8af5571f12326ab381936d'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def read_nrrd(raw):
    import numpy as np
    header,packed=raw.split(b'\n\n',1);fields={}
    for line in header.decode().splitlines():
        if line.startswith('#') or ':' not in line:continue
        key,_,value=line.partition(':');fields[key]=value.lstrip('= ')
    if fields.get('dimension')!='3' or fields.get('encoding')!='gzip' or fields.get('space')!='left-posterior-superior':raise ValueError('Unreviewed native grid')
    if fields['type']=='short' and fields.get('endian')=='little':dtype='<i2'
    elif fields['type']=='unsigned char':dtype='u1'
    else:raise ValueError('Unreviewed native sample type')
    dimensions=list(map(int,fields['sizes'].split()));values=np.frombuffer(gzip.decompress(packed),dtype)
    if len(dimensions)!=3 or any(d<1 for d in dimensions) or values.size!=dimensions[0]*dimensions[1]*dimensions[2]:raise ValueError('Native sample count differs')
    return fields,values.reshape(dimensions[::-1])


def review(root):
    import numpy as np
    from scipy import ndimage
    from skimage.measure import marching_cubes
    metadata=(root/'figshare-metadata.json').read_bytes()
    if sha(metadata)!=META_SHA:raise ValueError('Reviewed metadata snapshot differs')
    raw_mask=(root/'R6.seg.nrrd').read_bytes();raw_ct=(root/'R6.nrrd').read_bytes()
    if sha(raw_mask)!=MASK_SHA or sha(raw_ct)!=CT_SHA:raise ValueError('Original case bytes differ')
    mf,mask=read_nrrd(raw_mask);cf,ct=read_nrrd(raw_ct);mb,mo=grid_transform(mf);cb,co=grid_transform(cf)
    if mask.shape!=ct.shape or np.max(np.abs(mb-cb))>1e-12 or np.max(np.abs(mo-co))>1e-12:raise ValueError('Original grids do not correspond')
    counts=np.zeros(256,dtype='int64')
    for slab in mask:counts+=np.bincount(slab.ravel(),minlength=256)
    if set(np.flatnonzero(counts))!={0,1} or mf.get('Segment0_LabelValue')!='1' or mf.get('Segment0_Name')!='aorta':raise ValueError('Unreviewed original semantic label')
    xyz=np.argwhere(mask==1);lo=xyz.min(0);hi=xyz.max(0);roi=mask[lo[0]:hi[0]+1,lo[1]:hi[1]+1,lo[2]:hi[2]+1]
    components,n=ndimage.label(roi);component_sizes=np.bincount(components.ravel())[1:];del components,xyz
    # No boundary padding, smoothing, decimation or branch splitting is applied.
    vertices_zyx,faces,normals,values=marching_cubes(roi,level=.5,step_size=1,allow_degenerate=True)
    ijk=(vertices_zyx+lo)[:,::-1].astype('float64');lps=ijk@mb.T+mo;ras=lps*[-1,-1,1]
    edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);_,edge_counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
    pos=ras.astype('<f8').tobytes();tri=faces.astype('<u4').tobytes()
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/'original-R6.seg.nrrd').write_bytes(raw_mask)
    (OUTPUT/'source-metadata.json').write_bytes(metadata)
    for source,target in [('r6-acquisition.json','original-range-acquisition.json'),('rider-license-rows.json','tcia-license-row-review.json')]:
        (OUTPUT/target).write_bytes((root/source).read_bytes())
    (OUTPUT/'mask-isosurface-positions.f64.gz').write_bytes(gzip.compress(pos,mtime=0))
    (OUTPUT/'mask-isosurface-triangles.u32.gz').write_bytes(gzip.compress(tri,mtime=0))
    summary={'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC8760499/','source_record_url':'https://figshare.com/articles/dataset/14806362',
        'source_metadata_sha256':sha(metadata),'source_case_path':'Rider/R6 (AAA)/','case_diagnosis_is_source_directory_label':True,
        'original_ct_sha256':CT_SHA,'original_ct_bytes':len(raw_ct),'original_mask_sha256':MASK_SHA,'original_mask_bytes':len(raw_mask),
        'ct_header':cf,'mask_header':mf,'ct_grid_shape_zyx':list(ct.shape),'mask_grid_shape_zyx':list(mask.shape),
        'delivered_ct_voxel_count':int(ct.size),'original_ct_voxel_int16_sha256':sha(ct.tobytes()),
        'original_mask_voxel_uint8_sha256':sha(mask.tobytes()),'stored_ct_value_range':[int(ct.min()),int(ct.max())],
        'mask_voxel_counts':{str(i):int(counts[i]) for i in np.flatnonzero(counts)},
        'mask_bbox_zyx':[lo.tolist(),hi.tolist()],'mask_6_connected_components':int(n),'mask_component_voxel_counts':component_sizes.tolist(),
        'maximum_source_basis_difference_native_units':float(np.abs(mb-cb).max()),'maximum_source_origin_difference_native_units':float(np.abs(mo-co).max()),
        'grid_correspondence_is_independent_anatomical_validation':False,'source_segment_status_tag':mf['Segment0_Tags'].split('|')[0],
        'source_segment_status_is_independent_finished_review':False,'case_specific_annotator_or_independent_reader_verified':False,
        'dataset_metadata_license':'CC BY 4.0','dataset_description_inherits_upstream_collection_terms':True,
        'tcia_current_and_historical_image_rows_allow_cc_by_4_and_3':True,'exact_underlying_tcia_case_version_linkage_verified':False,
        'commercial_runtime_rights_clearance_status':'pending_exact_source_case_and_version_attribution_linkage',
        'original_voxels_changed':False,'highest_resolution_acquired_master_verified':False,'ct_hu_or_bolus_timing_verified':False,
        'physical_space_units_independently_verified':False,'source_labels_separate_every_reportable_structure':False,
        'derived_surface':{'method':'skimage_marching_cubes_binary_level_0_5_full_resolution_no_padding','positions':len(ras),'triangles':len(faces),
            'positions_dtype':'little_endian_float64','triangles_dtype':'little_endian_uint32','positions_sha256':sha(pos),'triangles_sha256':sha(tri),
            'source_mask_bbox_offset_zyx':lo.tolist(),'source_lps_to_ras_signs':[-1,-1,1],'boundary_edges':int((edge_counts==1).sum()),
            'nonmanifold_edges':int((edge_counts>2).sum()),'normals_are_derived_not_original_source_samples':True,
            'mask_conversion_is_original_delivered_geometry':False,'source_padding_or_caps_added':False,'smoothing_or_decimation_applied':False,
            'branch_or_wall_anatomical_identity_independently_reviewed':False,'clinical_approval':False,'runtime_promoted':False},
        'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False,
        'limits':['One binary aorta label does not separately delineate lumen, thrombus, wall, calcium, every vessel branch, rupture compartment, fistula or repair anatomy.',
            'Publication describes thresholding, noise filtering, manual correction and morphological closing; it explicitly warns that low-resolution cases omit branches.',
            'The original segment tag says inprogress; published benchmark ground-truth naming is not independent completed clinical anatomical review.',
            'Cardiac/contrast phase, CT HU calibration and acquired-master geometry are not independently recovered from these derivative NRRD headers.',
            'Only selected ZIP members were retrieved; member CRC and consistent ETag are verified, but the entire archive publisher MD5 is not.',
            'Upstream version-specific rights/attribution and exact original case linkage remain unresolved; no blanket commercial clearance from the Figshare badge.']}
    linkage=ROOT/'docs/avt-r6-dicom-linkage-review/complete-dicom-linkage-review.json'
    if linkage.exists():
        evidence=json.loads(linkage.read_text())
        if (evidence['original_ct_sha256']!=CT_SHA or evidence['original_mask_sha256']!=MASK_SHA
                or not evidence['all_source_slices_and_pixels_match'] or evidence['verified_original_pixel_count']!=ct.size
                or {r['voxel_k'] for r in evidence['records']}!=set(range(ct.shape[0]))
                or len(evidence['records'])!=ct.shape[0]):raise ValueError('DICOM linkage evidence does not cover this complete source')
        summary['verified_original_dicom_linkage']={'evidence_path':str(linkage.relative_to(ROOT)),
            'evidence_sha256':sha(linkage.read_bytes()),'source_doi':evidence['source_doi'],
            'SeriesInstanceUID':evidence['source_series']['SeriesInstanceUID'],'verified_pixel_count':evidence['verified_original_pixel_count']}
        summary['physical_space_units_independently_verified']=True
        summary['ct_hu_calibration_verified']=True
        summary['ct_bolus_timing_verified']=False
        summary['exact_underlying_series_linkage_verified']=True
        summary['original_avt_export_tcia_release_version_verified']=False
        summary['commercial_runtime_rights_clearance_status']='verified_current_source_ct_cc_by_3_0_and_mask_cc_by_4_0_with_attribution'
        summary['upstream_source_collection']='RIDER Lung PET-CT'
        summary['upstream_source_doi']=evidence['source_doi']
        summary['upstream_source_license']='CC BY 3.0'
        summary['previously_considered_rider_lung_ct_license_rows_allow_cc_by_4_and_3']=summary.pop('tcia_current_and_historical_image_rows_allow_cc_by_4_and_3')
        summary['matched_upstream_collection_image_row_license']='CC BY 3.0'
        summary['limits']=[s for s in summary['limits'] if not s.startswith('Cardiac/contrast phase, CT HU') and not s.startswith('Upstream version-specific rights/')]
        summary['limits']+=['Current original DICOM series, mm/HU calibration and reuse grants are fully matched; historical AVT export release, bolus timing and acquired-master status remain unverified.',
            'The AVT publication cites RIDER Lung CT; the exact R6 pixels match RIDER Lung PET-CT. Original citation is retained with explicit case-specific correction.']
    (OUTPUT/'native-source-review.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Verified R6 CT/mask;',int(counts[1]),'label voxels;',len(ras),'source-mask isosurface positions;',len(faces),'triangles; clinical approval pending.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    review(p.parse_args().source_root)
