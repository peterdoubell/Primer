#!/usr/bin/env python3
"""Preserve referenced native CT contours and quantify an explicit pixel-centre raster derivative."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile


def polygon_lines(points):
    import numpy as np
    points=np.asarray(points,float)
    if points.ndim!=2 or points.shape[1]!=2 or len(points)<3 or not np.isfinite(points).all():raise ValueError('Invalid source polygon')
    if len(np.unique(points,axis=0))!=len(points):raise ValueError('Repeated/keyhole vertices require separate source review')
    lines=np.stack([points,np.roll(points,-1,axis=0)],axis=1)
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    for i,(a,b) in enumerate(lines):
        for j in range(i+1,len(lines)):
            if j==i+1 or i==0 and j==len(lines)-1:continue
            c,d=lines[j]
            if np.any(np.maximum(np.minimum(a,b),np.minimum(c,d))>np.minimum(np.maximum(a,b),np.maximum(c,d))):continue
            ab_c=cross(b-a,c-a);ab_d=cross(b-a,d-a);cd_a=cross(d-c,a-c);cd_b=cross(d-c,b-c)
            if ab_c*ab_d<=0 and cd_a*cd_b<=0:raise ValueError('Self-contacting source polygon requires separate review')
    return lines


def boundary_distance_bound(first,second,step_mm=.125):
    """Exact sampled point-to-segment distances with a conservative arclength gap bound."""
    import numpy as np
    if step_mm<=0:raise ValueError('Need positive boundary sampling interval')
    points=[];maximum_gap=0
    for a,b in first:
        length=float(np.linalg.norm(b-a));n=max(1,int(np.ceil(length/step_mm)))
        points.append(a+np.arange(n+1)[:,None]/n*(b-a));maximum_gap=max(maximum_gap,length/n)
    points=np.concatenate(points);a=second[:,0];edge=second[:,1]-a;squared=np.einsum('ij,ij->i',edge,edge)
    if np.any(squared<=0):raise ValueError('Zero-length boundary segment')
    distances=[]
    for start in range(0,len(points),256):
        delta=points[start:start+256,None,:]-a
        fraction=np.clip(np.einsum('ijk,jk->ij',delta,edge)/squared,0,1)
        distances.extend(np.sqrt(np.min(np.sum((delta-fraction[:,:,None]*edge)**2,axis=2),axis=1)).tolist())
    maximum=max(distances)
    return {'sampled_points':len(points),'maximum_sample_to_segment_distance_mm':maximum,
            'maximum_arclength_sample_gap_mm':maximum_gap,'conservative_whole_boundary_upper_bound_mm':maximum+maximum_gap/2,
            'method':'Exact distance from sampled points to every opposite boundary segment; distance is 1-Lipschitz in arclength, so nearest-sample gap/2 bounds unsampled points.'}


def verified_objects(root,role):
    import pydicom
    receipt=json.loads((root/f'C3N-03018-{role}-archive-audit.json').read_text())
    with (root/f'C3N-03018-{role}.zip').open('rb') as source:
        sha=hashlib.sha256()
        for chunk in iter(lambda:source.read(1024*1024),b''):sha.update(chunk)
        if sha.hexdigest()!=receipt['archive_sha256']:raise ValueError('Audited source archive changed')
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            return [pydicom.dcmread(io.BytesIO(archive.read(row['member']))) for row in receipt['members']]


def review(root,output,derived):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from skimage.measure import find_contours
    from tools.anatomy_sources.audit_massp_mesh_voxels import raster_section
    geometry_path=Path('docs/cptac-renal-source-review/C3N-03018-original-geometry-review.json');geometry=json.loads(geometry_path.read_text())
    if geometry['max_contour_plane_error_mm']!=0 or not geometry['all_contour_points_in_acquired_extent']:raise ValueError('Source contour geometry is held')
    ct=verified_objects(root,'original-ct');rt=verified_objects(root,'annotation')[0];lookup={str(d.SOPInstanceUID):d for d in ct}
    rows=[];source_contours=[]
    for roi in rt.ROIContourSequence:
        for index,c in enumerate(roi.ContourSequence):
            if str(c.ContourGeometricType)!='CLOSED_PLANAR':raise ValueError('Unsupported source polygon type')
            refs=[str(r.ReferencedSOPInstanceUID) for r in c.ContourImageSequence]
            if len(refs)!=1 or refs[0] not in lookup:raise ValueError('Contour reference differs')
            d=lookup[refs[0]]
            if str(d.AcquisitionNumber)!='1':raise ValueError('Source contour acquisition differs')
            if list(map(float,d.ImageOrientationPatient))!=[1,0,0,0,1,0]:raise ValueError('Unreviewed source display direction')
            points=np.asarray(c.ContourData,float).reshape(-1,3);origin=np.asarray(d.ImagePositionPatient,float);spacing=np.asarray(d.PixelSpacing,float)
            xy=(points[:,:2]-origin[:2])/spacing[::-1]
            source_contours.append({'index':index,'roi':int(roi.ReferencedROINumber),'ct':d,'points_lps':points,'xy':xy,'lines':polygon_lines(xy)})
    if len({str(r['ct'].SOPInstanceUID) for r in source_contours})!=len(source_contours):raise ValueError('Multiple polygons per plane require explicit hole/combination review')
    source_contours.sort(key=lambda r:float(r['ct'].ImagePositionPatient[2]));z=np.array([float(r['ct'].ImagePositionPatient[2]) for r in source_contours])
    if not np.array_equal(np.diff(z),np.full(len(z)-1,.625)):raise ValueError('Unannotated gaps between source contour planes; no interpolation allowed')
    all_xy=np.concatenate([r['xy'] for r in source_contours]);lo=np.floor(all_xy.min(0)).astype(int)-5;hi=np.ceil(all_xy.max(0)).astype(int)+6
    if np.any(lo<0) or hi[0]>512 or hi[1]>512:raise ValueError('Review crop leaves acquired field')
    horizontal=np.arange(lo[0],hi[0]);vertical=np.arange(lo[1],hi[1]);stack=[]
    output.mkdir(parents=True,exist_ok=True);derived.mkdir(parents=True,exist_ok=True);figures=[]
    for source in source_contours:
        d=source['ct'];spacing=np.asarray(d.PixelSpacing,float);mask=raster_section(source['lines'],horizontal,vertical)
        paths=find_contours(mask.astype(float),.5)
        if not paths or any(not np.array_equal(path[0],path[-1]) for path in paths):raise ValueError('Raster boundary leaves review crop')
        segments=[]
        for path in paths:
            xy=path[:,::-1]+lo;segments.append(np.stack([xy[:-1],xy[1:]],axis=1))
        raster_lines=np.concatenate(segments);physical_scale=spacing[::-1]
        forward=boundary_distance_bound(source['lines']*physical_scale,raster_lines*physical_scale)
        reverse=boundary_distance_bound(raster_lines*physical_scale,source['lines']*physical_scale)
        xy=source['xy'];area=abs(float(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1)))/2)*float(np.prod(spacing))
        row={'source_contour_index':source['index'],'referenced_ct_sop':str(d.SOPInstanceUID),'source_acquisition_number':str(d.AcquisitionNumber),
             'source_ct_plane_z_lps_mm':float(d.ImagePositionPatient[2]),'source_polygon_vertices':len(xy),'source_polygon_area_mm2':area,
             'native_centre_selected_pixels':int(mask.sum()),'raster_area_mm2':float(mask.sum()*np.prod(spacing)),
             'source_to_raster_boundary':forward,'raster_to_source_boundary':reverse,'clinical_approval':False}
        rows.append(row);stack.append(mask);source['mask']=mask
    for start in range(0,len(source_contours),3):
        selected=source_contours[start:start+3];fig,axes=plt.subplots(len(selected),3,figsize=(14,4.5*len(selected)),squeeze=False,layout='constrained')
        for row,(source,axs) in enumerate(zip(selected,axes)):
            d=source['ct'];sy,sx=map(float,d.PixelSpacing);origin=np.asarray(d.ImagePositionPatient,float)
            x=-origin[0]-horizontal*sx;y=-origin[1]-vertical*sy
            extent=[float(x[0]+sx/2),float(x[-1]-sx/2),float(y[-1]-sy/2),float(y[0]+sy/2)]
            pixels=d.pixel_array[lo[1]:hi[1],lo[0]:hi[0]].astype(float)*float(d.RescaleSlope)+float(d.RescaleIntercept)
            for col,ax in enumerate(axs):
                ax.imshow(pixels,cmap='gray',vmin=-160,vmax=240,interpolation='nearest',extent=extent,origin='upper',aspect='equal')
                if col in (1,2):
                    points=source['points_lps'];ax.plot(-np.r_[points[:,0],points[0,0]],-np.r_[points[:,1],points[0,1]],color='#65b6dc',lw=.85)
                if col==2:ax.contour(x,y,source['mask'],levels=[.5],colors=['#ecb453'],linewidths=.8)
                ax.set_title(f"Source contour {source['index']} | LPS Z {float(d.ImagePositionPatient[2]):g} mm\n"+['Unmarked acquired CT','Original RTSTRUCT polygon','Original polygon + raster boundary'][col],fontsize=9)
                ax.set_xlabel('RAS X mm (R → L)',fontsize=8);ax.set_ylabel('RAS Y mm (P → A)',fontsize=8)
        fig.suptitle('C3N-03018 | original acquisition 1 | source ROI RT KIDNEY - 1\n'
                     'Native 0.976562 × 0.976562 × 0.625 mm; source polygon blue / derived raster amber; no diagnosis or whole-kidney claim',fontsize=11)
        path=output/f'contour-review-page{start//3+1:02d}.png';fig.savefig(path,dpi=130);plt.close(fig)
        figures.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_contour_indices':[s['index'] for s in selected],
                        'referenced_ct_sops':[str(s['ct'].SOPInstanceUID) for s in selected],'ct_display_window_hu':[-160,240],'source_ct_resampled':False})
    path=derived/'native-contour-plane-raster.npz';np.savez_compressed(path,selected_centres_zyx=np.stack(stack),source_z_lps_mm=z,crop_start_xy=lo,crop_stop_exclusive_xy=hi)
    result={'case_id':'C3N-03018','source_geometry_review_sha256':hashlib.sha256(geometry_path.read_bytes()).hexdigest(),'source_contours':rows,
            'figures':figures,'complete_source_contours_displayed':len(rows)==75,'derived_raster_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'raster_shape_zyx':list(np.stack(stack).shape),'source_crop_start_xy':lo.tolist(),'source_crop_stop_exclusive_xy':hi.tolist(),
            'raster_method':'Even/odd polygon membership at actual source CT pixel centres; strict ray inequality determines boundary ties. No subpixel supersampling, smoothing or fitted transformation.',
            'source_contour_points_changed':False,'source_ct_values_changed':False,'between_plane_interpolation_performed':False,
            'ends_closed_as_anatomical_surface':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Source contours remain authoritative continuous planar boundaries; the pixel-centre raster is a measured conversion candidate, not original segmentation truth.',
                      'Every boundary-distance upper bound includes a conservative half-arclength sampling gap, not only vertices or selected planes.',
                      'Absent contour planes and missing source end-surface definitions are not asserted clinically negative or automatically closed.',
                      'No kidney cortex, collecting system, vessels, histological identity or complete renal reporting scope is supplied by this ROI.']}
    (output/'contour-raster-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print('All',len(rows),'contours; selected pixels',sum(r['native_centre_selected_pixels'] for r in rows),'max source-to-raster bound',max(r['source_to_raster_boundary']['conservative_whole_boundary_upper_bound_mm'] for r in rows),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--derived',type=Path,required=True)
    a=parser.parse_args();review(a.source_root,a.output,a.derived)
