#!/usr/bin/env python3
"""Render unmarked acquired renal CT sections while preserving acquisition separation."""
import argparse
import hashlib
import json
from pathlib import Path


def render(root,output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from tools.anatomy_sources.review_cptac_renal_contours import verified_objects
    from tools.anatomy_sources.acquire_cptac_renal_case import validate_selection
    selection_path=root/'C3N-03018-selection.json';selection=json.loads(selection_path.read_text());validate_selection(selection)
    geometry_path=Path('docs/cptac-renal-source-review/C3N-03018-original-geometry-review.json');geometry=json.loads(geometry_path.read_text())
    receipt=json.loads((root/'C3N-03018-original-ct-archive-audit.json').read_text());ct=verified_objects(root,'original-ct')
    images=[d for d in ct if str(d.AcquisitionNumber)=='1'];images.sort(key=lambda d:float(d.ImagePositionPatient[2]));del ct
    if len(images)!=417 or any(list(map(float,d.ImageOrientationPatient))!=[1,0,0,0,1,0] or str(d.AcquisitionTime)!='104940.737882' for d in images):raise ValueError('Selected original acquisition geometry differs')
    positions=np.asarray([d.ImagePositionPatient for d in images],float)
    if not np.array_equal(np.diff(positions,axis=0),np.tile([0,0,.625],(416,1))):raise ValueError('Source acquisition position steps differ')
    if any(str(d.RescaleType)!='HU' or float(d.RescaleSlope)!=1 or float(d.RescaleIntercept)!=-1024 or list(map(float,d.PixelSpacing))!=[.976562,.976562] for d in images):raise ValueError('Native CT scale/sampling differs')
    volume=np.stack([d.pixel_array.astype(np.float32)-1024 for d in images]);rt=verified_objects(root,'annotation')[0]
    points=np.concatenate([np.asarray(c.ContourData,float).reshape(-1,3) for r in rt.ROIContourSequence for c in r.ContourSequence])
    midpoint=(points.min(0)+points.max(0))/2
    origin=positions[0];sx=sy=.976562;sz=.625
    centre=np.rint((midpoint-origin)/[sx,sy,sz]).astype(int);x_index,y_index,z_index=map(int,centre)
    # Crop is only a selected physical review region; no claimed whole-observation/organ coverage.
    start=np.maximum(np.floor((points.min(0)-origin)/[sx,sy,sz]).astype(int)-[30,30,30],0)
    stop=np.minimum(np.ceil((points.max(0)-origin)/[sx,sy,sz]).astype(int)+[31,31,31],[512,512,417])
    x0,y0,z0=map(int,start);x1,y1,z1=map(int,stop)
    x=-origin[0]-np.arange(x0,x1)*sx;y=-origin[1]-np.arange(y0,y1)*sy;z=origin[2]+np.arange(z0,z1)*sz
    views=[(volume[z_index,y0:y1,x0:x1],[x[0]+sx/2,x[-1]-sx/2,y[-1]-sy/2,y[0]+sy/2],'upper','Axial',0,z_index,'RAS X mm (R → L)','RAS Y mm (P → A)'),
           (volume[z0:z1,y_index,x0:x1],[x[0]+sx/2,x[-1]-sx/2,z[0]-sz/2,z[-1]+sz/2],'lower','Coronal',1,y_index,'RAS X mm (R → L)','RAS Z mm (I → S)'),
           (volume[z0:z1,y0:y1,x_index],[y[0]+sy/2,y[-1]-sy/2,z[0]-sz/2,z[-1]+sz/2],'lower','Sagittal',2,x_index,'RAS Y mm (A → P)','RAS Z mm (I → S)')]
    fig,axes=plt.subplots(2,3,figsize=(12,8),layout='constrained')
    for row,(low,high,label) in enumerate([(-160,240,'Soft-tissue display'),(-600,1000,'Wide display')]):
        for ax,(pixels,extent,mode,name,axis,index,xlabel,ylabel) in zip(axes[row],views):
            ax.imshow(pixels,cmap='gray',vmin=low,vmax=high,extent=extent,origin=mode,interpolation='nearest',aspect='equal')
            ax.set_title(f'{name} | native index {index}\n{label}: {low} to {high} stored HU',fontsize=9)
            ax.set_xlabel(xlabel,fontsize=8);ax.set_ylabel(ylabel,fontsize=8);ax.tick_params(labelsize=7)
    fig.suptitle('CPTAC C3N-03018 | original CT acquisition 1 | selected unmarked source sections\n'
                 'Native 0.976562 × 0.976562 × 0.625 mm; phase/diagnosis/boundaries unapproved; no annotation or model overlay',fontsize=10)
    output.mkdir(parents=True,exist_ok=True);path=output/'cptac-c3n03018-acq1-native-ct.png';fig.savefig(path,dpi=150);plt.close(fig)
    result={'source':{'dataset_doi':selection['original_image_doi'],'data_license':'CC BY 4.0','case_id':selection['case_id'],
                     'ct_dicom_files':850,'selected_acquisition_number':1,'selected_acquisition_dicom_files':417,
                     'other_acquisition_dicom_files':433,'publisher_per_file_md5_verified':True,'ct_archive_sha256':receipt['archive_sha256'],
                     'original_geometry_review_sha256':hashlib.sha256(geometry_path.read_bytes()).hexdigest(),
                     'source_selection_sha256':hashlib.sha256(selection_path.read_bytes()).hexdigest()},
            'figure_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_shape':[417,512,512],
            'source_index_order':'Original acquisition 1 Z,Y,X; sorted by actual ImagePositionPatient',
            'source_sampling_zyx_mm':[sz,sy,sx],'source_slice_thickness_mm':.625,'declared_spacing_between_slices_mm':2.5,
            'observed_interplane_step_mm':.625,'source_acquisitions_interleaved_or_deduplicated':False,
            'planes':[{'axis':axis,'index':index,'source_resampling':False} for _,_,_,_,axis,index,_,_ in views],
            'axial_source_sop_instance_uid':str(images[z_index].SOPInstanceUID),
            'crop_start_zyx':[z0,y0,x0],'crop_stop_exclusive_zyx':[z1,y1,x1],
            'section_selection_basis':'Nearest native voxel indices to the original annotation bounding-box midpoint; location aid, not a measured anatomical centre.',
            'source_voxels_changed':False,'clinical_approval':False,'model_geometry_overlaid':False,'annotation_geometry_overlaid':False,
            'named_phase_verified':False,'histological_diagnosis_verified':False,'complete_renal_anatomy_verified':False,
            'source_annotation_is_whole_kidney':False,'source_volume_and_end_extent_reconciled':False}
    (output/'cptac-c3n03018-acq1-sections.provenance.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Native source section centre ZYX',[z_index,y_index,x_index],'; PNG',path,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();render(a.source_root,a.output)
