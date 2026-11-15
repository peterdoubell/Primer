#!/usr/bin/env python3
"""Preserve acquired endpoint context and explicit contour-volume conventions without closing anatomy."""
import argparse
import hashlib
import json
from pathlib import Path


def volume_candidates(z_mm,areas_mm2,raster_areas_mm2,recorded_cm3):
    import numpy as np
    z=np.asarray(z_mm,float);area=np.asarray(areas_mm2,float);raster=np.asarray(raster_areas_mm2,float)
    if z.ndim!=1 or len(z)<2 or area.shape!=z.shape or raster.shape!=z.shape or not np.isfinite(np.r_[z,area,raster]).all():raise ValueError('Invalid volume inputs')
    steps=np.diff(z)
    if np.any(steps<=0) or not np.allclose(steps,steps[0],atol=1e-6,rtol=0):raise ValueError('Nonuniform or repeated source planes require separate convention')
    if np.any(area<0) or np.any(raster<0) or recorded_cm3<=0:raise ValueError('Invalid source area/volume')
    linear=float(np.sum((area[:-1]+area[1:])/2*steps));slabs=float(area.sum()*steps[0]);voxels=float(raster.sum()*steps[0])
    rows=[]
    for name,mm3,assumption in [
        ('linear_area_between_observed_planes',linear,'Linearly interpolate planar area only between first/last observed centres; no outside end cap.'),
        ('constant_area_centred_slabs',slabs,'Each source polygon area occupies one observed plane-spacing slab, extending half a step beyond both endpoint centres.'),
        ('native_pixel_centres_centred_slabs',voxels,'Each selected native pixel centre occupies its full in-plane pixel area and one observed spacing slab; no source-author equivalence claimed.')]:
        rows.append({'convention':name,'volume_mm3':mm3,'volume_cm3':mm3/1000,'assumption':assumption,
                     'difference_from_recorded_cm3':mm3/1000-recorded_cm3,'relative_difference_percent':100*(mm3/1000-recorded_cm3)/recorded_cm3,
                     'is_original_author_volume_method':False,'is_clinical_volume_validation':False})
    return rows


def review(root,output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from tools.anatomy_sources.review_cptac_renal_contours import verified_objects
    contour_path=Path('docs/cptac-renal-source-review/C3N-03018-contour-review/contour-raster-review.json');contours=json.loads(contour_path.read_text())
    selection=json.loads((root/'C3N-03018-selection.json').read_text());ct=verified_objects(root,'original-ct');rt=verified_objects(root,'annotation')[0]
    roi=rt.StructureSetROISequence[0];recorded=float(roi.ROIVolume);csv_value=float(selection['annotation_row']['ROIVolume'])
    if recorded!=csv_value:raise ValueError('Original DICOM and CSV volume values differ')
    values=contours['source_contours'];z=np.array([r['source_ct_plane_z_lps_mm'] for r in values]);areas=[r['source_polygon_area_mm2'] for r in values]
    candidates=volume_candidates(z,areas,[r['raster_area_mm2'] for r in values],recorded)
    acquisition=[d for d in ct if str(d.AcquisitionNumber)=='1'];acquisition.sort(key=lambda d:float(d.ImagePositionPatient[2]));lookup={str(d.SOPInstanceUID):i for i,d in enumerate(acquisition)}
    original={str(c.ContourImageSequence[0].ReferencedSOPInstanceUID):np.asarray(c.ContourData,float).reshape(-1,3) for r in rt.ROIContourSequence for c in r.ContourSequence}
    lo=np.asarray(contours['source_crop_start_xy']);hi=np.asarray(contours['source_crop_stop_exclusive_xy']);figures=[];ends=[]
    output.mkdir(parents=True,exist_ok=True)
    for name,source in [('inferior',values[0]),('superior',values[-1])]:
        centre=lookup[source['referenced_ct_sop']]
        if centre<2 or centre+2>=len(acquisition):raise ValueError('Original acquisition lacks endpoint neighbours')
        images=acquisition[centre-2:centre+3];fig,axes=plt.subplots(1,5,figsize=(20,5.6),layout='constrained');planes=[]
        for offset,(ax,d) in zip(range(-2,3),zip(axes,images)):
            if list(map(float,d.ImageOrientationPatient))!=[1,0,0,0,1,0]:raise ValueError('Unreviewed native orientation')
            sy,sx=map(float,d.PixelSpacing);origin=np.asarray(d.ImagePositionPatient,float);xs=-origin[0]-np.arange(lo[0],hi[0])*sx;ys=-origin[1]-np.arange(lo[1],hi[1])*sy
            extent=[float(xs[0]+sx/2),float(xs[-1]-sx/2),float(ys[-1]-sy/2),float(ys[0]+sy/2)]
            pixels=d.pixel_array[lo[1]:hi[1],lo[0]:hi[0]].astype(float)*float(d.RescaleSlope)+float(d.RescaleIntercept)
            ax.imshow(pixels,cmap='gray',vmin=-160,vmax=240,origin='upper',extent=extent,interpolation='nearest',aspect='equal')
            sop=str(d.SOPInstanceUID);points=original.get(sop)
            if points is not None:ax.plot(-np.r_[points[:,0],points[0,0]],-np.r_[points[:,1],points[0,1]],color='#65b6dc',lw=.9)
            status='Own original contour shown' if points is not None else 'No source contour; anatomy unassessed'
            ax.set_title(f'Offset {offset:+d} source planes | LPS Z {float(d.ImagePositionPatient[2]):g} mm\n'+status,fontsize=8)
            ax.set_xlabel('RAS X mm (R → L)',fontsize=8);ax.set_ylabel('RAS Y mm (P → A)',fontsize=8)
            planes.append({'offset_from_endpoint':offset,'ct_sop_instance_uid':sop,'acquisition_number':str(d.AcquisitionNumber),
                           'source_plane_z_lps_mm':float(d.ImagePositionPatient[2]),'source_contour_present':points is not None,
                           'unannotated_plane_is_clinically_negative':False})
        fig.suptitle(f'C3N-03018 | {name} annotation end and acquired neighbouring CT\nOriginal acquisition 1; no contour transfer, zero-mask assumption or invented end surface',fontsize=11)
        path=output/(name+'-endpoint-context.png');fig.savefig(path,dpi=130);plt.close(fig)
        figures.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_pixels_resampled':False})
        ends.append({'end':name,'endpoint_source_polygon_area_mm2':source['source_polygon_area_mm2'],'acquired_planes':planes,'end_cap_defined_in_source':False})
    result={'case_id':selection['case_id'],'source_selection_sha256':hashlib.sha256((root/'C3N-03018-selection.json').read_bytes()).hexdigest(),
            'source_contour_review_sha256':hashlib.sha256(contour_path.read_bytes()).hexdigest(),'original_rtstruct_roi_volume_value':str(roi.ROIVolume),
            'csv_volume_value':selection['annotation_row']['ROIVolume'],'csv_and_dicom_values_match_exactly':True,
            'dicom_roi_volume_unit':'cm3','unit_basis':'DICOM PS3.3 Structure Set Module, ROI Volume (3006,002C)',
            'unit_definition_url':'https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_c.8.8.5.html',
            'original_generation_algorithm':str(roi.ROIGenerationAlgorithm),'source_volume_calculation_algorithm_verified':False,
            'volume_candidates':candidates,'source_geometry_scaled_to_match_recorded_volume':False,'source_values_changed':False,
            'annotation_end_context':ends,'figures':figures,'clinical_approval':False,'runtime_promoted':False,
            'status':'held_unreconciled_source_volume_convention_and_end_extent',
            'limits':['DICOM resolves the stored volume unit and matches the CSV; it does not explain the authors numerical volume method.',
                      'Area/slab conventions are explicit diagnostic comparisons, not competing approved anatomical models.',
                      'Nonzero endpoint contours and acquired neighbours do not establish the actual superior/inferior tumour boundary.',
                      'No absent annotation is made clinically negative; no source surface is scaled, closed or repaired to force agreement.']}
    (output/'endpoint-and-volume-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recorded original volume cm3',recorded,'; comparison conventions',[(r['convention'],r['volume_cm3']) for r in candidates],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();review(a.source_root,a.output)
