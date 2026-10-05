#!/usr/bin/env python3
"""Preserve exact renal source RTSTRUCT outlines without surface creation or whole-organ relabelling."""
import argparse,hashlib,json
from pathlib import Path


def decimal_text(value):
    return getattr(value,'original_string',str(value))


def export(root,volume_provenance,output):
    import numpy as np
    from tools.anatomy_sources.review_cptac_renal_contours import verified_objects
    from tools.anatomy_sources.acquire_cptac_renal_case import validate_selection
    selection_path=root/'C3N-03018-selection.json';selection=json.loads(selection_path.read_text());validate_selection(selection)
    volume=json.loads(volume_provenance.read_text());geometry_path=Path('docs/cptac-renal-source-review/C3N-03018-original-geometry-review.json');geometry=json.loads(geometry_path.read_text())
    if (volume['source_selection_sha256']!=hashlib.sha256(selection_path.read_bytes()).hexdigest()
        or volume['source_geometry_review_sha256']!=hashlib.sha256(geometry_path.read_bytes()).hexdigest()
        or volume['selected_acquisition_number']!=1 or not geometry['all_contour_points_in_acquired_extent']
        or geometry['max_contour_plane_error_mm']!=0):raise ValueError('Audited source geometry/volume differs')
    annotation=verified_objects(root,'annotation')
    if len(annotation)!=1:raise ValueError('Original annotation count differs')
    rt=annotation[0];receipt=json.loads((root/'C3N-03018-annotation-archive-audit.json').read_text())
    if str(rt.SeriesInstanceUID)!=selection['annotation_row']['SeriesInstanceUID'] or str(rt.FrameOfReferenceUID) not in geometry['source_frame_of_reference_uids']:
        raise ValueError('Original source annotation frame/identity differs')
    frames={r['source_sop_instance_uid']:r for r in volume['frames']};rows=[];roi_meta=[]
    for roi in rt.StructureSetROISequence:
        roi_meta.append({'roi_number':int(roi.ROINumber),'source_name':str(roi.ROIName),'generation_algorithm':str(roi.ROIGenerationAlgorithm),
                         'declared_roi_volume_decimal_cm3':decimal_text(roi.ROIVolume),'independent_whole_organ_or_histology_verified':False})
    for roi in rt.ROIContourSequence:
        for index,contour in enumerate(roi.ContourSequence):
            refs=[str(r.ReferencedSOPInstanceUID) for r in contour.ContourImageSequence]
            if len(refs)!=1 or refs[0] not in frames or str(contour.ContourGeometricType)!='CLOSED_PLANAR':raise ValueError('Source contour type/reference differs')
            strings=[decimal_text(v) for v in contour.ContourData];points=np.asarray(strings,dtype=float).reshape(-1,3);frame=frames[refs[0]]
            if (len(points)!=int(contour.NumberOfContourPoints) or not np.isfinite(points).all()
                or not np.all(points[:,2]==frame['source_position_lps_mm'][2])):raise ValueError('Original contour coordinate/plane differs')
            row=next(r for r in geometry['contours'] if r['roi_number']==int(roi.ReferencedROINumber) and r['contour_index']==index)
            if refs[0]!=row['referenced_ct_sop'] or len(points)!=row['points'] or row['source_acquisition_number']!='1':raise ValueError('Original contour differs from prior source audit')
            rows.append({'source_roi_number':int(roi.ReferencedROINumber),'source_contour_index':index,
                         'original_contour_number':int(contour.ContourNumber) if 'ContourNumber' in contour else None,
                         'source_ct_sop':refs[0],'native_acquisition1_plane_index':frame['index'],'geometric_type':'CLOSED_PLANAR',
                         'source_decimal_lps_xyz_mm':strings,'points':len(points),'original_plane_lps_z_mm':frame['source_position_lps_mm'][2],
                         'source_slab_thickness_present':(0x3006,0x0044) in contour,'source_offset_vector_present':(0x3006,0x0045) in contour})
    if len(rows)!=75 or len(rows)!=len(geometry['contours']):raise ValueError('Original contour omission')
    result={'schema_version':1,'case_id':selection['case_id'],'source_annotation_doi':selection['annotation_doi'],
      'source_annotation_archive_sha256':receipt['archive_sha256'],'source_rt_sop':str(rt.SOPInstanceUID),'source_frame_of_reference_uid':str(rt.FrameOfReferenceUID),
      'source_volume_provenance_sha256':hashlib.sha256(volume_provenance.read_bytes()).hexdigest(),'source_volume_uncompressed_sha256':volume['uncompressed_sha256'],
      'source_selection_sha256':volume['source_selection_sha256'],'source_geometry_review_sha256':volume['source_geometry_review_sha256'],
      'source_rois':roi_meta,'source_roi_observations':geometry['source_roi_observations'],'contours':rows,'source_contours':len(rows),'source_points':sum(r['points'] for r in rows),
      'coordinate_encoding':'Original DICOM decimal strings in consecutive LPS XYZ millimetre triplets; original order retained.',
      'line_semantics':'Per-contour CLOSED_PLANAR last-to-first edge only; no between-plane edges, surface triangulation, interpolation or endpoint cap.',
      'source_points_transformed_repaired_or_rounded':False,'surface_or_voxel_mask_created':False,'whole_kidney_segmentation':False,
      'different_acquisitions_registered_or_joined':False,'clinical_approval':False,'model_coverage_granted':False,
      'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
      'attribution':'CPTAC-CCRCC Tumor Annotations, The Cancer Imaging Archive. DOI '+selection['annotation_doi']+'. CC BY 4.0. Derivative: separate original-coordinate polyline display, without altered source points or surface creation.',
      'limitations':['Source neoplasm/right-kidney labels do not independently verify histology or a complete organ segmentation.',
                     'Sparse planar outlines and their endpoints do not establish a continuous closed surface or calibrated lesion volume; prior volume/end-extent discrepancies remain unresolved.',
                     'Viewer coordinate normalization is a reversible display mapping in the same source frame, not patient fitting or cross-acquisition registration.']}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n');print('Retained',result['source_contours'],'contours and',result['source_points'],'original decimal coordinate points')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--volume-provenance',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();export(a.source_root,a.volume_provenance,a.output)
