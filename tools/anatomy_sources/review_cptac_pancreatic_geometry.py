#!/usr/bin/env python3
"""Audit both original pancreatic CT grids and every source contour without fitting or phase inference."""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import zipfile


def verified_headers(root,case,role):
    import pydicom
    receipt_path=root/(case+'-'+role+'-archive-audit.json');receipt=json.loads(receipt_path.read_text())
    with (root/(case+'-'+role+'.zip')).open('rb') as source:
        digest=hashlib.sha256()
        for chunk in iter(lambda:source.read(1024*1024),b''):digest.update(chunk)
        if digest.hexdigest()!=receipt['archive_sha256']:raise ValueError('Original audited archive changed')
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            return [pydicom.dcmread(io.BytesIO(archive.read(row['member'])),stop_before_pixels=True) for row in receipt['members']],receipt


def time_seconds(value):
    text=str(value)
    if len(text)<6:raise ValueError('Need complete original DICOM time')
    hour=int(text[:2]);minute=int(text[2:4]);second=float(text[4:])
    if not 0<=hour<24 or not 0<=minute<60 or not 0<=second<60:raise ValueError('Invalid DICOM time')
    return hour*3600+minute*60+second


def review(root,selection_path,output):
    import numpy as np
    from tools.anatomy_sources.acquire_cptac_pancreatic_case import validate_selection
    from tools.anatomy_sources.review_cptac_renal_geometry import partition_acquisitions
    selection=json.loads(selection_path.read_text());validate_selection(selection);case=selection['case_id'];records=[]
    for pair in selection['source_pairs']:
        role=pair['role'];images,ct_receipt=verified_headers(root,case,role+'-ct');annotations,rt_receipt=verified_headers(root,case,role+'-annotation')
        if len(annotations)!=1:raise ValueError('Expected one original RTSTRUCT')
        rt=annotations[0];first=images[0];orientation=np.asarray(first.ImageOrientationPatient,float);normal=np.cross(orientation[:3],orientation[3:]);spacing=np.asarray(first.PixelSpacing,float)
        if not np.allclose([np.linalg.norm(orientation[:3]),np.linalg.norm(orientation[3:]),np.dot(orientation[:3],orientation[3:])],[1,1,0],atol=1e-6,rtol=0):raise ValueError('Invalid original CT directions')
        for d in images:
            if (str(d.PatientID)!=case or str(d.SeriesInstanceUID)!=pair['original_ct_series']['SeriesInstanceUID'] or str(d.StudyInstanceUID)!=pair['original_ct_series']['StudyInstanceUID'] or
                not np.array_equal(np.asarray(d.ImageOrientationPatient,float),orientation) or not np.array_equal(np.asarray(d.PixelSpacing,float),spacing) or (d.Rows,d.Columns)!=(first.Rows,first.Columns)):raise ValueError('Source CT identity or geometry differs within selected series')
        if str(rt.PatientID)!=case or str(rt.SeriesInstanceUID)!=pair['annotation_series']['SeriesInstanceUID'] or str(rt.StudyInstanceUID)!=pair['annotation_series']['StudyInstanceUID']:raise ValueError('Original RTSTRUCT identity differs')
        if len({str(d.SOPInstanceUID) for d in images})!=len(images):raise ValueError('Duplicate source SOP')
        instance_order=sorted(images,key=lambda d:int(d.InstanceNumber));original_steps=np.diff(np.asarray([d.ImagePositionPatient for d in instance_order],float)@normal)
        images.sort(key=lambda d:float(np.asarray(d.ImagePositionPatient,float)@normal));positions=np.asarray([d.ImagePositionPatient for d in images],float);offsets=positions@normal;steps=np.diff(offsets)
        if np.any(steps<=0):raise ValueError('Repeated source positions; preserve actual acquisitions before volume creation')
        partitions=partition_acquisitions(images,normal)
        if len(partitions)!=1 or not partitions[0]['uniform_interplane_step']:raise ValueError('Selected series is not one regular original acquisition')
        lookup={str(d.SOPInstanceUID):(i,d) for i,d in enumerate(images)};frames={str(d.FrameOfReferenceUID) for d in images};contours=[];rois=[]
        for r in rt.StructureSetROISequence:
            if str(r.ReferencedFrameOfReferenceUID) not in frames:raise ValueError('ROI coordinate frame differs')
            rois.append({'roi_number':int(r.ROINumber),'source_name':str(r.ROIName),'source_tracking_id':str(getattr(r,'TrackingID','not_reported')),
                         'source_tracking_uid':str(getattr(r,'TrackingUID','not_reported')),'original_roi_volume_cm3':str(getattr(r,'ROIVolume','not_reported')),
                         'generation_algorithm':str(getattr(r,'ROIGenerationAlgorithm','not_reported'))})
        for roi in rt.ROIContourSequence:
            for index,c in enumerate(roi.ContourSequence):
                if str(c.ContourGeometricType)!='CLOSED_PLANAR':raise ValueError('Unreviewed source contour type')
                refs=[str(r.ReferencedSOPInstanceUID) for r in c.ContourImageSequence]
                if len(refs)!=1 or refs[0] not in lookup:raise ValueError('Contour references an unacquired or different CT object')
                z,d=lookup[refs[0]];points=np.asarray(c.ContourData,float).reshape(-1,3)
                if len(points)!=int(c.NumberOfContourPoints) or not np.isfinite(points).all():raise ValueError('Source contour points differ from declaration')
                delta=points-np.asarray(d.ImagePositionPatient,float);column=delta@orientation[:3]/spacing[1];row=delta@orientation[3:]/spacing[0];error=np.abs(delta@normal)
                contours.append({'source_roi_number':int(roi.ReferencedROINumber),'source_contour_index':index,'referenced_ct_sop':refs[0],
                                 'native_sorted_plane_index':z,'source_plane_position_lps':list(map(float,d.ImagePositionPatient)),
                                 'source_contour_points':len(points),'maximum_referenced_plane_error_mm':float(error.max()),
                                 'source_column_bounds':[float(column.min()),float(column.max())],'source_row_bounds':[float(row.min()),float(row.max())],
                                 'points_in_source_extent':bool(column.min()>=-.5 and column.max()<=d.Columns-.5 and row.min()>=-.5 and row.max()<=d.Rows-.5)})
        affine=np.eye(4);affine[:3,0]=positions[1]-positions[0];affine[:3,1]=orientation[3:]*spacing[0];affine[:3,2]=orientation[:3]*spacing[1];affine[:3,3]=positions[0]
        observations=[]
        for obs in rt.RTROIObservationsSequence:
            fields={}
            for name in ['AnatomicRegionSequence','SegmentedPropertyCategoryCodeSequence','RTROIIdentificationCodeSequence']:
                fields[name]=[{'scheme':str(r.CodingSchemeDesignator),'code':str(r.CodeValue),'meaning':str(r.CodeMeaning)} for r in getattr(obs,name,[])]
            observations.append({'roi_number':int(obs.ReferencedROINumber),'source_observation_label':str(obs.ROIObservationLabel),'source_codes':fields})
        records.append({'source_role':role,'original_ct_series_uid':str(first.SeriesInstanceUID),'ct_archive_sha256':ct_receipt['archive_sha256'],'annotation_archive_sha256':rt_receipt['archive_sha256'],
                        'ct_objects':len(images),'source_shape_zyx':[len(images),int(first.Rows),int(first.Columns)],'source_orientation_lps':orientation.tolist(),'source_pixel_spacing_mm':spacing.tolist(),
                        'source_slice_thicknesses_mm':sorted({float(d.SliceThickness) for d in images}),'original_spacing_between_slices_values_mm':sorted({float(d.SpacingBetweenSlices) for d in images if hasattr(d,'SpacingBetweenSlices')}),
                        'observed_increasing_position_steps_mm':[float(steps.min()),float(steps.max())],'original_instance_order_signed_steps_mm':[float(original_steps.min()),float(original_steps.max())],
                        'native_index_zyx_to_lps_mm':affine.tolist(),'acquisitions':partitions,'frame_of_reference_uids':sorted(frames),
                        'source_contrast_agents':sorted({str(getattr(d,'ContrastBolusAgent','not_reported')) for d in images}),
                        'source_contrast_start_times':sorted({str(getattr(d,'ContrastBolusStartTime','not_reported')) for d in images}),
                        'source_contrast_stop_times':sorted({str(getattr(d,'ContrastBolusStopTime','not_reported')) for d in images}),
                        'source_rescale_types':sorted({str(getattr(d,'RescaleType','not_reported')) for d in images}),
                        'metadata_tracking_uid':pair['annotation_row']['Tracking UID'],
                        'dicom_tracking_uids_match_metadata':all(r['source_tracking_uid']==pair['annotation_row']['Tracking UID'] for r in rois),
                        'rois':rois,'source_roi_observations':observations,'contours':contours,'all_contours_in_source_extent':all(c['points_in_source_extent'] for c in contours),
                        'maximum_contour_plane_error_mm':max(c['maximum_referenced_plane_error_mm'] for c in contours),'clinical_approval':False})
    common=set(records[0]['frame_of_reference_uids']) & set(records[1]['frame_of_reference_uids'])
    delta=time_seconds(records[1]['acquisitions'][0]['source_acquisition_time'])-time_seconds(records[0]['acquisitions'][0]['source_acquisition_time'])
    result={'case_id':case,'original_image_doi':selection['original_image_doi'],'annotation_doi':selection['annotation_doi'],'annotation_version':selection['annotation_version'],
            'source_selection_sha256':hashlib.sha256(selection_path.read_bytes()).hexdigest(),'records':records,'shared_declared_frame_of_reference_uids':sorted(common),
            'difference_between_acquisition_time_fields_seconds':delta,
            'source_dicom_tracking_uid_sets_match_each_other':{r['source_tracking_uid'] for r in records[0]['rois']}=={r['source_tracking_uid'] for r in records[1]['rois']},
            'cross_metadata_dicom_tracking_identity_reconciled':all(r['dicom_tracking_uids_match_metadata'] for r in records),'same_declared_frame_is_anatomical_registration':False,
            'named_pancreatic_or_portal_phase_adequacy_verified':False,'contrast_timing_relative_to_injection_verified':False,'source_rois_merged_or_averaged':False,
            'source_values_or_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Source-labelled series and recorded acquisition times remain source facts; absent injection timing/agent information cannot be supplied by labels alone.',
                      'The original negative spacing tag and descending instance-order geometry are preserved separately from increasing-position analysis indices.',
                      'CSV and DICOM tracking UIDs differ, while each representation agrees internally across the two source roles; both identities remain unchanged and unresolved. Tracking/frame correspondence does not prove motion-free anatomy, phase adequacy, tumour extent or source histological identity.',
                      'Lesion selection/RTSTRUCT codes do not supply whole pancreas, ducts, vessels, neural tissue or all source reporting structures.']}
    output.write_text(json.dumps(result,indent=2)+'\n');print('Source CT grids',[r['source_shape_zyx'] for r in records],'; contours',[len(r['contours']) for r in records],'; maximum plane errors',[r['maximum_contour_plane_error_mm'] for r in records],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--selection',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.source_root,a.selection,a.output)
