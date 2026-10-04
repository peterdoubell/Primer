#!/usr/bin/env python3
"""Preserve original decimal contour coordinates as separate 3D polylines, never a fitted surface."""
import argparse
import hashlib
import json
from pathlib import Path


def decimal_text(value):
    return getattr(value, 'original_string', str(value))


def export(root, selection_path, geometry_path, output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from tools.anatomy_sources.review_cptac_pancreatic_geometry import verified_headers
    from tools.anatomy_sources.acquire_cptac_pancreatic_case import validate_selection
    selection=json.loads(selection_path.read_text()); validate_selection(selection)
    geometry=json.loads(geometry_path.read_text())
    if geometry['source_selection_sha256'] != hashlib.sha256(selection_path.read_bytes()).hexdigest():
        raise ValueError('Selection differs from audited source')
    output.mkdir(parents=True,exist_ok=True); records=[]
    fig=plt.figure(figsize=(14,7),layout='constrained')
    for slot,pair in enumerate(selection['source_pairs']):
        role=pair['role']; original=next(r for r in geometry['records'] if r['source_role']==role)
        annotations,receipt=verified_headers(root,selection['case_id'],role+'-annotation')
        if receipt['archive_sha256']!=original['annotation_archive_sha256'] or len(annotations)!=1:
            raise ValueError('Original annotation differs from geometry audit')
        rt=annotations[0]
        if str(rt.SeriesInstanceUID)!=pair['annotation_series']['SeriesInstanceUID']:
            raise ValueError('Original annotation series differs')
        contours=[]; roi_fields=[]; polygon_fields=[]
        for roi in rt.StructureSetROISequence:
            roi_fields.append({'roi_number':int(roi.ROINumber),'source_name':str(roi.ROIName),
                               'dicom_roi_volume_decimal_cm3':decimal_text(roi.ROIVolume),'csv_roi_volume_decimal':pair['annotation_row']['ROIVolume'],
                               'csv_and_dicom_roi_volume_equal':decimal_text(roi.ROIVolume)==pair['annotation_row']['ROIVolume'],
                               'roi_generation_algorithm':str(roi.ROIGenerationAlgorithm),
                               'roi_generation_description_present': 'ROIGenerationDescription' in roi,
                               'roi_derivation_algorithm_identification_present': 'ROIDerivationAlgorithmIdentificationSequence' in roi})
        for roi in rt.ROIContourSequence:
            polygon_fields.append({'referenced_roi_number':int(roi.ReferencedROINumber),
                                   'source_pixel_planes_characteristics_sequence_present':(0x3006,0x004A) in roi,
                                   'source_series_sequence_present':(0x3006,0x004B) in roi})
            for index,c in enumerate(roi.ContourSequence):
                audited=next(r for r in original['contours'] if r['source_contour_index']==index and r['source_roi_number']==int(roi.ReferencedROINumber))
                refs=[str(r.ReferencedSOPInstanceUID) for r in c.ContourImageSequence]
                if refs != [audited['referenced_ct_sop']] or str(c.ContourGeometricType)!='CLOSED_PLANAR':
                    raise ValueError('Source contour reference/type differs')
                raw=[decimal_text(v) for v in c.ContourData]
                points=np.asarray(raw,float).reshape(-1,3)
                if len(points)!=audited['source_contour_points'] or not np.all(points[:,2]==audited['source_plane_position_lps'][2]):
                    raise ValueError('Original point count/plane differs')
                contours.append({'source_roi_number':int(roi.ReferencedROINumber),'source_contour_index':index,
                                 'original_contour_number':int(c.ContourNumber),'source_ct_sop':refs[0],
                                 'native_plane_index':audited['native_sorted_plane_index'],'geometric_type':str(c.ContourGeometricType),
                                 'source_decimal_lps_xyz_mm':raw,'points':len(points),
                                 'contour_slab_thickness_present':(0x3006,0x0044) in c,
                                 'contour_offset_vector_present':(0x3006,0x0045) in c})
        if len(contours)!=len(original['contours']): raise ValueError('Source contour omission')
        grid_present=any(r['source_pixel_planes_characteristics_sequence_present'] for r in polygon_fields)
        ax=fig.add_subplot(1,2,slot+1,projection='3d'); all_points=[]
        for c in contours:
            points=np.asarray(c['source_decimal_lps_xyz_mm'],float).reshape(-1,3); all_points.append(points)
            # The last-to-first edge is source CLOSED_PLANAR semantics, not an end cap or between-plane bridge.
            closed=np.vstack([points,points[0]])
            ax.plot(closed[:,0],closed[:,1],closed[:,2],color='#337fac',lw=.55)
        points=np.concatenate(all_points); lo=points.min(0); hi=points.max(0)
        ax.set_box_aspect(hi-lo); ax.set_xlim(lo[0],hi[0]); ax.set_ylim(lo[1],hi[1]); ax.set_zlim(lo[2],hi[2])
        ax.set_xlabel('LPS X mm (R → L)'); ax.set_ylabel('LPS Y mm (A → P)'); ax.set_zlabel('LPS Z mm (I → S)')
        ax.view_init(elev=23,azim=-65)
        ax.set_title(f'{role} | {len(contours)} source planar outlines\nNo between-plane faces, interpolation or end caps',fontsize=10)
        records.append({'source_role':role,'annotation_archive_sha256':receipt['archive_sha256'],'source_rt_sop':str(rt.SOPInstanceUID),
                        'source_manufacturer_model':str(rt.ManufacturerModelName),'source_rois':roi_fields,'roi_contour_metadata':polygon_fields,
                        'source_contours':contours,'source_pixel_plane_grid_declared':grid_present,
                        'dicom_grid_specific_absent_roi_rule_applicable':grid_present,
                        'source_explicit_volume_algorithm_available':False,
                        'whole_pancreas_or_source_histology_independently_verified':False})
        print(role,'vertices',sum(c['points'] for c in contours),'source pixel plane grid present',grid_present,flush=True)
    fig.suptitle('C3L-02112 | original RTSTRUCT coordinates in separate native LPS frames\nExact source outlines only; source ROI extent unapproved; no inter-series registration or lesion surface',fontsize=11)
    path=output/'original-contour-polylines-3d.png'; fig.savefig(path,dpi=130); plt.close(fig)
    result={'case_id':selection['case_id'],'source_selection_sha256':hashlib.sha256(selection_path.read_bytes()).hexdigest(),
            'source_geometry_sha256':hashlib.sha256(geometry_path.read_bytes()).hexdigest(),'records':records,
            'coordinate_encoding':'Original DICOM DS strings, flat consecutive LPS XYZ triplets in millimetres; no rounding or quantization.',
            'line_representation':'Original CLOSED_PLANAR per-contour closing edge only. No points added to exported source arrays, no between-plane links or triangulation.',
            'source_points_transformed_or_repaired':False,'solid_surface_created':False,'cross_acquisition_registration':False,
            'clinical_approval':False,'runtime_promoted':False,'figure':{'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},
            'standards_review':{'edition':'DICOM PS3.3 2026d','roi_volume_units':'cm3',
                                'volume_attribute_reference':'https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.8.5.html',
                                'source_grid_absent_roi_rule_reference':'https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.8.6.4.html'},
            'limits':['A declared source pixel-plane grid triggers DICOM grid-specific absence semantics; these source files must be assessed for that actual declaration, not assumed to contain it.',
                      'Publisher protocol establishes lesion-target annotation and volume reporting, not an explicit integration or end-cap formula for this ROI.',
                      'Source ROI malignant-neoplasm codes are annotation assertions, not independent case-level pathology verification.',
                      'Original decimal vertices are preserved for future independent boundary review; a planar-line 3D plot is not a validated lesion surface.']}
    (output/'original-contour-geometry.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['source-root','selection','geometry','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); export(a.source_root,a.selection,a.geometry,a.output)
