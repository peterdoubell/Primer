#!/usr/bin/env python3
"""Preserve expert-source paired lumen masks and derive separate native-grid surfaces without fitting."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from tools.anatomy_sources.review_avt_r6_source import read_nrrd
from tools.anatomy_sources.review_aaa_kinematic_source import grid_transform,stl,geometry_controls

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'docs/graz-cta17-native-source-review'
HASHES={'figshare-metadata.json':'e7425f6e7a096e27b6add58414834eda5fa5a32746498829c86979abed113b31',
 'cta17s.nrrd':'c30bc554a36e1afb6259be4bf6bee2b84efe5856d5047474063428d8211c948d',
 'raw-cta17.nrrd':'1c075da3d83ef18f8539dfc8d7df0895800fb8281946c10593cefbdd94895791',
 'truelumen17.seg.nrrd':'818b5c7ecef9d612daa33b9ebbc7f67999edc5a6387ead7cf9b7037cd8ece5cf',
 'falselumen17.seg.nrrd':'6964df0bdb7104e13df587551e20b4f5d85275a583f141901594b139dc1fdcd4',
 'mesh17.stl':'b2aac9cea7f35142a742d4914fbc696cbe6addcd19c30fb73dee7ca9e8c31c9a',
 'PMC11156948.1.xml':'cab05197ce967317b3676a8ad24dc9979ddf481873ca15022b9714f05e2a40e0'}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def review(root):
    import numpy as np
    from scipy import ndimage
    from skimage.measure import marching_cubes
    for name,expected in HASHES.items():
        if sha((root/name).read_bytes())!=expected:raise ValueError('Reviewed original file differs: '+name)
    meta=json.loads((root/'figshare-metadata.json').read_text())
    if meta['license']['name']!='CC BY 4.0':raise ValueError('Original grant differs')
    xml=(root/'PMC11156948.1.xml').read_bytes();nlm=json.loads((root/'PMC11156948.1.json').read_text())
    if hashlib.md5(xml).hexdigest()!=nlm['xml_url'].split('md5=')[1]:raise ValueError('Publisher XML MD5 differs')
    document=ET.fromstring(xml);ct_header,ct=read_nrrd((root/'cta17s.nrrd').read_bytes());raw_header,raw_ct=read_nrrd((root/'raw-cta17.nrrd').read_bytes())
    if ct.shape!=raw_ct.shape or not np.array_equal(ct,raw_ct):raise ValueError('Raw/staged CT voxel correspondence differs')
    ct_basis,ct_origin=grid_transform(ct_header)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    for source,target in [('figshare-metadata.json','source-metadata.json'),('cta17-acquisition.json','original-range-acquisition.json')]:
        (OUTPUT/target).write_bytes((root/source).read_bytes())
    (OUTPUT/'original-mesh17.stl.gz').write_bytes(gzip.compress((root/'mesh17.stl').read_bytes(),mtime=0))
    records=[];masks=[]
    for kind,value,label,table_volume,table_mean,table_sd in [('true',1,'True Lumen',254.1,281,24),('false',2,'False Lumen',358.2,118,80)]:
        name=kind+'lumen17.seg.nrrd';raw=(root/name).read_bytes();header,mask=read_nrrd(raw);basis,origin=grid_transform(header)
        if (mask.shape!=ct.shape or header.get('Segment0_Name')!=label or header.get('Segment0_LabelValue')!=str(value)
                or np.max(np.abs(basis-ct_basis))>1e-12 or np.max(np.abs(origin-ct_origin))>1e-12):
            raise ValueError('Original lumen semantics or source grid differs')
        if set(np.unique(mask))!={0,value}:raise ValueError('Unexpected native mask labels')
        selected=mask==value;masks.append(selected);indices=np.argwhere(selected);lo=indices.min(0);hi=indices.max(0)
        # One original-background voxel around the label bbox preserves boundaries.
        # The ROI is clipped to the delivered grid; no invented padding is added.
        crop_lo=np.maximum(lo-1,0);crop_hi=np.minimum(hi+1,np.array(mask.shape)-1)
        roi=selected[crop_lo[0]:crop_hi[0]+1,crop_lo[1]:crop_hi[1]+1,crop_lo[2]:crop_hi[2]+1]
        components,n=ndimage.label(roi);sizes=np.bincount(components.ravel())[1:];del components,indices
        vertices,faces,normals,levels=marching_cubes(roi,level=.5,step_size=1,allow_degenerate=True)
        ijk=(vertices+crop_lo)[:,::-1].astype('float64');ras=(ijk@basis.T+origin)*[-1,-1,1]
        pbytes=ras.astype('<f8').tobytes();tbytes=faces.astype('<u4').tobytes()
        (OUTPUT/name).write_bytes(raw)
        (OUTPUT/(kind+'-positions.f64.gz')).write_bytes(gzip.compress(pbytes,mtime=0))
        (OUTPUT/(kind+'-triangles.u32.gz')).write_bytes(gzip.compress(tbytes,mtime=0))
        edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);_,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
        voxels=int(selected.sum());volume=float(voxels*abs(np.linalg.det(basis))/1000)
        sample_mean=float(ct[selected].mean());sample_sd=float(ct[selected].std())
        records.append({'lumen':kind,'source_name':label,'source_label_value':value,'source_mask_sha256':sha(raw),
            'source_voxel_sha256':sha(mask.tobytes()),'source_header':header,'voxel_count':voxels,
            'bbox_zyx':[lo.tolist(),hi.tolist()],'roi_crop_offset_zyx':crop_lo.tolist(),
            'six_connected_component_count':int(n),'component_voxel_counts':sizes.tolist(),
            'source_status_tag':header['Segment0_Tags'].split('|')[0],
            'grid_basis_difference_max_native_units':float(np.abs(basis-ct_basis).max()),
            'grid_origin_difference_max_native_units':float(np.abs(origin-ct_origin).max()),
            'voxel_volume_from_native_matrix':float(abs(np.linalg.det(basis))),
            'voxel_volume_if_source_mm_units_ml':volume,'source_table_volume_ml':table_volume,
            'voxel_volume_minus_source_table_ml':volume-table_volume,
            'mean_stored_ct_value_within_label':sample_mean,'population_sd_stored_ct_value_within_label':sample_sd,
            'source_table_mean_hu':table_mean,'source_table_sd_hu':table_sd,
            'table_statistics_are_independent_dicom_calibration':False,
            'positions':len(ras),'triangles':len(faces),'positions_sha256':sha(pbytes),'triangles_sha256':sha(tbytes),
            'bounds_ras_native_units':[ras.min(0).tolist(),ras.max(0).tolist()],
            'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),
            'source_labels_changed':False,'interpolation_is_binary_0_5_isosurface':True,
            'original_voxel_anisotropy_preserved':True,'background_padding_added':False,
            'source_smoothing_decimation_fitting_or_component_removal_applied':False,
            'geometry_is_original_delivered_mesh':False,'clinical_approval':False,'runtime_promoted':False})
    overlap=int(np.count_nonzero(masks[0]&masks[1]))
    # Retain original source table cells without silently correcting printed values.
    tables=[[[ ' '.join(c.itertext()) for c in row.findall('*')] for row in table.findall('.//tr')]
            for table in document.findall('.//table')]
    original=stl((root/'mesh17.stl').read_bytes());control=geometry_controls(original)
    summary={'source_record_url':'https://figshare.com/articles/dataset/22269091','source_doi':'10.6084/m9.figshare.22269091',
        'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC11156948/','source_article_doi':'10.1038/s41597-024-03284-2',
        'source_metadata_sha256':HASHES['figshare-metadata.json'],'source_article_xml_sha256':HASHES['PMC11156948.1.xml'],
        'publisher_article_xml_md5_verified':True,'dataset_license':'CC BY 4.0','dataset_license_url':meta['license']['url'],
        'attribution':'; '.join(a['full_name'] for a in meta['authors'])+'. Aortic Dissection Dataset and Segmentations. DOI 10.6084/m9.figshare.22269091. CC BY 4.0. No endorsement implied.',
        'source_case':'cta17','source_table_segmentation_method':'Interpolating','source_table_annotator_tier':'cardiac_surgery_resident',
        'source_publication_final_expert_checks':['Christian Mayer','Johannes Schmid','Heinrich Mächler'],
        'source_reported_contrast_phase':'arterial','source_reported_ecg_gated':False,
        'raw_ct_sha256':HASHES['raw-cta17.nrrd'],'staged_ct_sha256':HASHES['cta17s.nrrd'],
        'raw_staged_ct_all_voxels_equal':True,'ct_voxel_count':int(ct.size),'original_ct_voxel_sha256':sha(ct.tobytes()),
        'ct_header':ct_header,'raw_ct_header':raw_header,'original_ct_value_range':[int(ct.min()),int(ct.max())],
        'original_mask_overlap_voxels':overlap,'records':records,'source_tables':tables,
        'original_delivered_mesh_sha256':HASHES['mesh17.stl'],'original_delivered_mesh_controls':control,
        'original_mesh_patient_frame_or_unit_transform_verified':False,'original_mesh_fitted_or_rescaled':False,
        'upstream_public_mesh_code_commit':'7700c2a15c707ff292e7275d14558914c24817be',
        'upstream_code_applies_to_cta17_verified':False,
        'source_voxels_masks_or_original_mesh_changed':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False,
        'limits':['Source masks were checked by clinical experts, but clearly thrombosed sections were excluded and some uncertain dark regions were included as presumed late-filling lumen.',
            'The source did not locate entry/re-entry tears and excludes type A, poorly distinguishable or markedly thrombosed examples; it cannot represent every AAS phenotype.',
            'One expert annotation is not a separate wall, flap, thrombus, every branch, perfusion or complication map.',
            'True/false masks have completed/inprogress workflow tags; publication expert review and application metadata are separate evidence.',
            'Source-table volume and intensity controls differ slightly from delivered voxel statistics; no masks or CT values are changed to force agreement.',
            'Delivered mesh17 is preserved, but its unitless coordinate frame is not assigned to the patient by guess or fitting. Public conversion code only explicitly loops over cases 25–40.',
            'Native-grid derivatives preserve anisotropy and separate source label values without merging channels or adding a wall model.',
            'Arterial phase is publication-reported, not recovered from DICOM; original DICOM calibration and exact entry/tear/complete anatomy remain unverified.']}
    (OUTPUT/'paired-lumen-source-review.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Preserved raw/staged CT correspondence and separate native lumen annotations; derived two unfitted source-mask surfaces.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    review(p.parse_args().source_root)
