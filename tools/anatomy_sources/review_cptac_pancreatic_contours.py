#!/usr/bin/env python3
"""Review every original pancreatic contour and retain unannotated native planes."""
import argparse
import hashlib
import json
from pathlib import Path


def missing_indices(indices):
    if len(set(indices)) != len(indices):
        raise ValueError('Multiple polygons per plane require explicit combination review')
    ordered = sorted(indices)
    if not ordered:
        raise ValueError('No source contour planes')
    return sorted(set(range(ordered[0], ordered[-1] + 1)) - set(ordered))


def review(root, selection_path, geometry_path, output, derived):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from skimage.measure import find_contours
    from scipy import ndimage
    from tools.anatomy_sources.render_cptac_pancreatic_native_reference import verified_objects
    from tools.anatomy_sources.review_cptac_renal_contours import polygon_lines, boundary_distance_bound
    from tools.anatomy_sources.audit_massp_mesh_voxels import raster_section
    from tools.anatomy_sources.acquire_cptac_pancreatic_case import validate_selection
    selection = json.loads(selection_path.read_text()); validate_selection(selection)
    geometry = json.loads(geometry_path.read_text())
    if hashlib.sha256(selection_path.read_bytes()).hexdigest() != geometry['source_selection_sha256']:
        raise ValueError('Selection differs from original geometry audit')
    output.mkdir(parents=True, exist_ok=True); derived.mkdir(parents=True, exist_ok=True)
    records = []
    for pair in selection['source_pairs']:
        role = pair['role']; case = selection['case_id']
        record = next(r for r in geometry['records'] if r['source_role'] == role)
        ct = verified_objects(root, case, role+'-ct', record['ct_archive_sha256'])
        rt = verified_objects(root, case, role+'-annotation', record['annotation_archive_sha256'])[0]
        ct.sort(key=lambda d: float(d.ImagePositionPatient[2]))
        if len(ct) != record['ct_objects'] or any(str(d.SeriesInstanceUID) != record['original_ct_series_uid'] or
                list(map(float, d.ImageOrientationPatient)) != [1,0,0,0,1,0] or
                list(map(float, d.PixelSpacing)) != [.703125,.703125] or str(d.RescaleType) != 'HU' for d in ct):
            raise ValueError('Original source CT differs')
        positions = np.asarray([d.ImagePositionPatient for d in ct], float)
        affine = np.asarray(record['native_index_zyx_to_lps_mm'], float)
        if not np.array_equal(positions, affine[:3,3] + np.arange(len(ct))[:,None]*affine[:3,0]):
            raise ValueError('Native positions differ from audited grid')
        lookup = {str(d.SOPInstanceUID): (i,d) for i,d in enumerate(ct)}
        sources = []
        names = {int(r.ROINumber): str(r.ROIName) for r in rt.StructureSetROISequence}
        if len(names) != 1:
            raise ValueError('Multiple ROIs require separate interpretation')
        for roi in rt.ROIContourSequence:
            for index,c in enumerate(roi.ContourSequence):
                refs = [str(r.ReferencedSOPInstanceUID) for r in c.ContourImageSequence]
                if str(c.ContourGeometricType) != 'CLOSED_PLANAR' or len(refs) != 1 or refs[0] not in lookup:
                    raise ValueError('Unsupported or unrelated source contour')
                zi,d = lookup[refs[0]]; points = np.asarray(c.ContourData,float).reshape(-1,3)
                if len(points) != int(c.NumberOfContourPoints) or not np.all(points[:,2] == positions[zi,2]):
                    raise ValueError('Original contour point/plane declaration differs')
                xy = (points[:,:2]-positions[zi,:2])/.703125
                if np.any(xy < -.5) or np.any(xy > [d.Columns-.5,d.Rows-.5]):
                    raise ValueError('Source points outside native CT')
                sources.append({'index':index,'roi':int(roi.ReferencedROINumber),'zi':zi,'ct':d,'points':points,'xy':xy,'lines':polygon_lines(xy)})
        if len(sources) != len(record['contours']):
            raise ValueError('Contour count differs from audit')
        sources.sort(key=lambda s:s['zi'])
        absent = missing_indices([s['zi'] for s in sources])
        all_xy = np.concatenate([s['xy'] for s in sources]); lo = np.floor(all_xy.min(0)).astype(int)-5; hi = np.ceil(all_xy.max(0)).astype(int)+6
        if np.any(lo < 0) or hi[0] > ct[0].Columns or hi[1] > ct[0].Rows:
            raise ValueError('Review crop leaves acquired field')
        horizontal = np.arange(lo[0],hi[0]); vertical = np.arange(lo[1],hi[1]); rows=[]; stack=[]
        for s in sources:
            mask = raster_section(s['lines'],horizontal,vertical)
            paths = find_contours(mask.astype(float),.5)
            if not paths or any(not np.array_equal(p[0],p[-1]) for p in paths):
                raise ValueError('Derived raster boundary leaves crop')
            lines = np.concatenate([np.stack([(p[:,::-1]+lo)[:-1],(p[:,::-1]+lo)[1:]],axis=1) for p in paths])
            forward = boundary_distance_bound(s['lines']*.703125,lines*.703125)
            reverse = boundary_distance_bound(lines*.703125,s['lines']*.703125)
            xy=s['xy']; area=abs(float(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1)))/2)*.703125**2
            rows.append({'source_contour_index':s['index'],'source_roi_number':s['roi'],'native_plane_index':s['zi'],
                         'referenced_ct_sop':str(s['ct'].SOPInstanceUID),'source_z_lps_mm':float(s['ct'].ImagePositionPatient[2]),
                         'source_polygon_vertices':len(xy),'source_polygon_area_mm2':area,'raster_selected_pixels':int(mask.sum()),
                         'raster_area_mm2':float(mask.sum()*.703125**2),
                         'raster_foreground_components_4_connected':int(ndimage.label(mask,structure=ndimage.generate_binary_structure(2,1))[1]),
                         'raster_background_holes_8_connected':int(ndimage.label(~mask,structure=ndimage.generate_binary_structure(2,2))[1]-1),
                         'source_to_raster_boundary':forward,'raster_to_source_boundary':reverse})
            s['mask']=mask; stack.append(mask)
        figures=[]
        for start in range(0,len(sources),3):
            selected=sources[start:start+3]
            fig,axes=plt.subplots(len(selected),3,figsize=(14,4.5*len(selected)),squeeze=False,layout='constrained')
            for s,axs in zip(selected,axes):
                d=s['ct']; x=-float(d.ImagePositionPatient[0])-horizontal*.703125; y=-float(d.ImagePositionPatient[1])-vertical*.703125
                extent=[x[0]+.703125/2,x[-1]-.703125/2,y[-1]-.703125/2,y[0]+.703125/2]
                pixels=d.pixel_array[lo[1]:hi[1],lo[0]:hi[0]].astype(float)*float(d.RescaleSlope)+float(d.RescaleIntercept)
                for col,ax in enumerate(axs):
                    ax.imshow(pixels,cmap='gray',vmin=-160,vmax=240,interpolation='nearest',extent=extent,origin='upper',aspect='equal')
                    if col in (1,2):
                        pts=s['points']; ax.plot(-np.r_[pts[:,0],pts[0,0]],-np.r_[pts[:,1],pts[0,1]],color='#65b6dc',lw=.85)
                    if col==2:
                        ax.contour(x,y,s['mask'],levels=[.5],colors=['#ecb453'],linewidths=.8)
                    ax.set_title(f"Contour {s['index']} | native plane {s['zi']} | LPS Z {float(d.ImagePositionPatient[2]):g} mm\n"+['Unmarked CT','Original RTSTRUCT polygon','Original polygon + raster boundary'][col],fontsize=9)
                    ax.set_xlabel('RAS X mm (R → L)',fontsize=8); ax.set_ylabel('RAS Y mm (P → A)',fontsize=8)
            fig.suptitle(f"{case} | {role} | source ROI {next(iter(names.values()))}\nOriginal polygon blue / derived raster amber; source ROI identity/anatomical extent unapproved",fontsize=11)
            path=output/(role+f'-contour-page{start//3+1:02d}.png'); fig.savefig(path,dpi=110); plt.close(fig)
            figures.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'contour_indices':[s['index'] for s in selected]})
        gap_figures=[]
        for zi in absent:
            d=ct[zi]; fig,ax=plt.subplots(figsize=(6,6),layout='constrained')
            pixels=d.pixel_array[lo[1]:hi[1],lo[0]:hi[0]].astype(float)*float(d.RescaleSlope)+float(d.RescaleIntercept)
            x=-float(d.ImagePositionPatient[0])-horizontal*.703125; y=-float(d.ImagePositionPatient[1])-vertical*.703125
            ax.imshow(pixels,cmap='gray',vmin=-160,vmax=240,interpolation='nearest',origin='upper',extent=[x[0]+.703125/2,x[-1]-.703125/2,y[-1]-.703125/2,y[0]+.703125/2],aspect='equal')
            ax.set_title(f'{case} | {role} | native plane {zi}\nAcquired CT without a source contour; NOT a negative mask',fontsize=10)
            ax.set_xlabel('RAS X mm (R → L)'); ax.set_ylabel('RAS Y mm (P → A)')
            path=output/(role+f'-unannotated-plane{zi}.png'); fig.savefig(path,dpi=130); plt.close(fig)
            gap_figures.append({'native_plane_index':zi,'source_ct_sop':str(d.SOPInstanceUID),'source_z_lps_mm':float(d.ImagePositionPatient[2]),'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'label_state':'unannotated_not_negative'})
        path=derived/(case+'-'+role+'-selected-contour-planes.npz')
        np.savez_compressed(path,selected_centres_yx=np.stack(stack),native_plane_indices=np.array([s['zi'] for s in sources]),source_z_lps_mm=np.array([positions[s['zi'],2] for s in sources]),crop_start_xy=lo,crop_stop_exclusive_xy=hi)
        source_slab=sum(r['source_polygon_area_mm2'] for r in rows)*.625/1000
        raster_slab=sum(r['raster_area_mm2'] for r in rows)*.625/1000
        original_vol=float(next(iter(rt.StructureSetROISequence)).ROIVolume)
        records.append({'source_role':role,'ct_archive_sha256':record['ct_archive_sha256'],'annotation_archive_sha256':record['annotation_archive_sha256'],
                        'source_roi_name':next(iter(names.values())),'source_roi_volume_cm3':original_vol,'source_contours':rows,'figures':figures,
                        'unannotated_acquired_planes_inside_contour_span':gap_figures,'complete_source_contours_displayed':len(rows)==len(record['contours']),
                        'selected_plane_raster_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'selected_plane_array_shape':list(np.stack(stack).shape),
                        'array_is_contiguous_3d_mask':False,'source_crop_start_xy':lo.tolist(),'source_crop_stop_exclusive_xy':hi.tolist(),
                        'annotated_centres_only_equal_0625mm_slab_volume_cm3':{'original_polygons':source_slab,'pixel_centre_raster':raster_slab},
                        'slab_volume_is_validated_lesion_volume':False,'unannotated_planes_filled':False,
                        'positive_selected_pixels_on_first_and_last_contour_planes':[rows[0]['raster_selected_pixels'],rows[-1]['raster_selected_pixels']],
                        'roi_volume_semantics_or_end_surface_definition_reconciled':False})
        print(role,len(rows),'contours; unannotated planes',absent,'boundary bounds',max(r['source_to_raster_boundary']['conservative_whole_boundary_upper_bound_mm'] for r in rows),max(r['raster_to_source_boundary']['conservative_whole_boundary_upper_bound_mm'] for r in rows),'source/raster slab cm3',source_slab,raster_slab,'original cm3',original_vol,flush=True)
        del ct,stack,sources
    result={'case_id':selection['case_id'],'source_selection_sha256':hashlib.sha256(selection_path.read_bytes()).hexdigest(),
            'source_geometry_sha256':hashlib.sha256(geometry_path.read_bytes()).hexdigest(),'records':records,
            'raster_method':'Even/odd membership at native CT pixel centres; strict ray boundary ties. Selected planes stored with explicit native indices, not a contiguous volume.',
            'distance_method':'Bidirectional point-to-segment distances sampled at <=0.125 mm arclength, with conservative half-gap bound for unsampled boundary points.',
            'source_ct_or_contour_values_changed':False,'source_contour_planes_interpolated':False,'ends_closed':False,
            'cross_acquisition_registration_or_roi_merging':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Original continuous planar source polygons are authoritative; raster boundaries are measured derivatives, not segmentation truth.',
                      'Absent annotation on acquired CT is unknown, not a negative label; no cross-series contour supplies missing planes.',
                      'Positive endpoint contours do not establish end caps; centre-slab arithmetic is not a validated lesion volume.',
                      'ROI names/codes and a cohort do not establish source histology, whole pancreas or ducts/vessels/neural staging coverage.',
                      'Metadata-to-DICOM tracking identity and phase adequacy remain unresolved.']}
    (output/'contour-raster-review.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['source-root','selection','geometry','output','derived']:
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); review(a.source_root,a.selection,a.geometry,a.output,a.derived)
