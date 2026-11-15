#!/usr/bin/env python3
"""Audit every original renal CT plane and RTSTRUCT contour reference without fitting."""
from collections import defaultdict, Counter
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile


def partition_acquisitions(ct,normal):
    import numpy as np
    groups=defaultdict(list)
    for d in ct:groups[(str(d.AcquisitionNumber),str(d.AcquisitionTime))].append(d)
    acquisitions=[]
    for (number,time),images in sorted(groups.items()):
        images=sorted(images,key=lambda d:float(np.asarray(d.ImagePositionPatient,float)@normal))
        xyz=np.asarray([d.ImagePositionPatient for d in images],float);offsets=xyz@normal;delta=np.diff(offsets)
        if np.any(delta<=0):raise ValueError('Repeated plane within one declared acquisition')
        acquisitions.append({'source_acquisition_number':number,'source_acquisition_time':time,'images':len(images),
                             'observed_interplane_step_mm_min_max':[float(delta.min()),float(delta.max())] if len(delta) else None,
                             'uniform_interplane_step':bool(len(delta)>0 and np.allclose(delta,delta[0],atol=1e-6,rtol=0)),
                             'position_extent_lps_mm':[xyz[0].tolist(),xyz[-1].tolist()],
                             'phase_identity_verified':False})
    return acquisitions


def review(root, output):
    import numpy as np
    import pydicom
    selection=json.loads((root/'C3N-03018-selection.json').read_text());objects={}
    for role in ['original-ct','annotation']:
        receipt=json.loads((root/f'C3N-03018-{role}-archive-audit.json').read_text())
        with (root/f'C3N-03018-{role}.zip').open('rb') as source:
            digest=hashlib.sha256()
            for chunk in iter(lambda:source.read(1024*1024),b''):digest.update(chunk)
            if digest.hexdigest()!=receipt['archive_sha256']:raise ValueError('Audited source archive changed')
            source.seek(0)
            with zipfile.ZipFile(source) as archive:
                objects[role]=[pydicom.dcmread(io.BytesIO(archive.read(r['member'])),stop_before_pixels=True) for r in receipt['members']]
    ct=objects['original-ct'];rt=objects['annotation'][0];first=ct[0]
    orientation=np.asarray(first.ImageOrientationPatient,float);normal=np.cross(orientation[:3],orientation[3:]);spacing=np.asarray(first.PixelSpacing,float)
    if not np.allclose([np.linalg.norm(orientation[:3]),np.linalg.norm(orientation[3:]),np.dot(orientation[:3],orientation[3:])],[1,1,0],atol=1e-6,rtol=0):raise ValueError('Invalid source directions')
    if any(not np.array_equal(np.asarray(d.ImageOrientationPatient,float),orientation) or not np.array_equal(np.asarray(d.PixelSpacing,float),spacing) or (d.Rows,d.Columns)!=(first.Rows,first.Columns) for d in ct):raise ValueError('Source plane geometry varies')
    if any(str(d.SeriesInstanceUID)!=selection['original_ct_series']['SeriesInstanceUID'] or str(d.PatientID)!=selection['case_id'] for d in ct):raise ValueError('Original CT source identity differs')
    if len({str(d.SOPInstanceUID) for d in ct})!=len(ct):raise ValueError('Duplicate CT SOP')
    ct.sort(key=lambda d:float(np.asarray(d.ImagePositionPatient,float)@normal));positions=np.asarray([d.ImagePositionPatient for d in ct],float)
    distances=positions@normal;steps=np.diff(distances)
    acquisitions=partition_acquisitions(ct,normal)
    multiplicity=Counter(tuple(d.ImagePositionPatient) for d in ct)
    lookup={str(d.SOPInstanceUID):(i,d) for i,d in enumerate(ct)};records=[]
    frame_uids={str(d.FrameOfReferenceUID) for d in ct};roi_rows=[]
    for roi in rt.StructureSetROISequence:
        if str(roi.ReferencedFrameOfReferenceUID) not in frame_uids:raise ValueError('ROI frame differs from CT')
        roi_rows.append({'roi_number':int(roi.ROINumber),'source_name':str(roi.ROIName),'source_frame_of_reference_uid':str(roi.ReferencedFrameOfReferenceUID)})
    for roi in rt.ROIContourSequence:
        for index,contour in enumerate(roi.ContourSequence):
            if str(contour.ContourGeometricType)!='CLOSED_PLANAR':raise ValueError('Unsupported source contour type')
            refs=[str(r.ReferencedSOPInstanceUID) for r in contour.ContourImageSequence]
            if len(refs)!=1 or refs[0] not in lookup:raise ValueError('Contour does not reference one acquired CT plane')
            native_z,d=lookup[refs[0]];points=np.asarray(contour.ContourData,float).reshape(-1,3)
            if len(points)!=int(contour.NumberOfContourPoints) or not np.isfinite(points).all():raise ValueError('Contour point declaration differs')
            delta=points-np.asarray(d.ImagePositionPatient,float)
            plane_error=np.abs(delta@normal);column=delta@orientation[:3]/spacing[1];row=delta@orientation[3:]/spacing[0]
            records.append({'roi_number':int(roi.ReferencedROINumber),'contour_index':index,'points':len(points),
                            'referenced_ct_sop':refs[0],'source_ct_position_sorted_object_index':native_z,'source_acquisition_number':str(d.AcquisitionNumber),'source_acquisition_time':str(d.AcquisitionTime),'max_plane_error_mm':float(plane_error.max()),
                            'source_column_bounds': [float(column.min()),float(column.max())],'source_row_bounds':[float(row.min()),float(row.max())],
                            'all_points_in_acquired_plane_extent':bool(column.min()>=-.5 and column.max()<=d.Columns-.5 and row.min()>=-.5 and row.max()<=d.Rows-.5)})
    declared=sorted({float(d.SpacingBetweenSlices) for d in ct if hasattr(d,'SpacingBetweenSlices')})
    observations=[]
    for observation in rt.RTROIObservationsSequence:
        row={'roi_number':int(observation.ReferencedROINumber),'source_observation_label':str(observation.ROIObservationLabel)}
        for field in ['AnatomicRegionSequence','SegmentedPropertyCategoryCodeSequence','RTROIIdentificationCodeSequence']:
            row[field]=[{'code':str(r.CodeValue),'scheme':str(r.CodingSchemeDesignator),'meaning':str(r.CodeMeaning)} for r in getattr(observation,field,[])]
        observations.append(row)
    result={'case_id':selection['case_id'],'source_selection_sha256':hashlib.sha256((root/'C3N-03018-selection.json').read_bytes()).hexdigest(),
            'source_acquisitions':acquisitions,'ct_unique_positions':len(multiplicity),
            'position_multiplicity_counts':{str(n):sum(v==n for v in multiplicity.values()) for n in set(multiplicity.values())},
            'single_series_is_single_volume':False,'ct_images':len(ct),'source_rows_columns':[int(first.Rows),int(first.Columns)],'source_orientation_lps':orientation.tolist(),
            'source_pixel_spacing_mm':spacing.tolist(),'source_slice_thicknesses_mm':sorted({float(d.SliceThickness) for d in ct}),
            'declared_spacing_between_slices_mm':declared,'observed_interplane_step_mm_min_max':[float(steps.min()),float(steps.max())],
            'uniform_observed_interplane_step':bool(np.allclose(steps,steps[0],atol=1e-6,rtol=0)),
            'maximum_inplane_step_mm':float(np.linalg.norm(np.diff(positions,axis=0)-steps[:,None]*normal,axis=1).max()),
            'declared_spacing_matches_observed_positions':bool(all(np.allclose(steps,value,atol=1e-6,rtol=0) for value in declared)),
            'ct_position_extent_lps_mm':[positions[0].tolist(),positions[-1].tolist()],
            'source_frame_of_reference_uids':sorted(frame_uids),'source_rescale_types':sorted({str(getattr(d,'RescaleType','not_reported')) for d in ct}),
            'source_rescale_slopes':sorted({float(d.RescaleSlope) for d in ct}),'source_rescale_intercepts':sorted({float(d.RescaleIntercept) for d in ct}),
            'source_contrast_agents':sorted({str(getattr(d,'ContrastBolusAgent','not_reported')) for d in ct}),
            'source_rois':roi_rows,'source_roi_observations':observations,'contours':records,
            'all_contours_reference_acquired_ct_sops':True,'all_contour_points_in_acquired_extent':all(r['all_points_in_acquired_plane_extent'] for r in records),
            'max_contour_plane_error_mm':max(r['max_plane_error_mm'] for r in records),'source_geometry_fitted_or_corrected':False,
            'clinical_approval':False,'runtime_promoted':False,
            'limits':['Two acquisitions share one series and overlapping positions. They remain separate; no deduplication, phase assignment or interpolated unified volume is performed.',
                      'ROI labels and neoplasm codes are source annotations, not independent diagnosis or whole-kidney segmentation.',
                      'Original DICOM geometry and contour references do not approve contour interpolation, rasterization, anatomical boundaries or all reportable structures.',
                      'Post-contrast source description/agent does not establish renal enhancement-phase adequacy or an unenhanced comparison.']}
    output.write_text(json.dumps(result,indent=2)+'\n');print('Observed CT plane step',result['observed_interplane_step_mm_min_max'],'; contour max plane error',result['max_contour_plane_error_mm'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();review(a.source_root,a.output)
