#!/usr/bin/env python3
"""Compare unmodified author contours with both fitted FE faces across explicit coordinate-origin hypotheses."""
import argparse,gzip,hashlib,io,json,zipfile,warnings
from pathlib import Path
from tools.anatomy_sources.review_sunnybrook_source_parameters import OUT
from tools.anatomy_sources.render_sunnybrook_model_correspondence import plane_segments

def distance_to_segments(points,segments):
    import numpy as np
    lines=np.asarray(segments,dtype=float)
    if len(lines)==0:raise ValueError('Original fitted face does not intersect contour plane')
    a=lines[:,0,:];v=lines[:,1,:]-a;length2=(v*v).sum(axis=1);valid=length2>1e-16;a=a[valid];v=v[valid];length2=length2[valid]
    p=np.asarray(points);delta=p[:,None,:]-a[None,:,:];t=np.clip((delta*v[None,:,:]).sum(axis=2)/length2[None,:],0,1);nearest=a[None,:,:]+t[:,:,None]*v[None,:,:];distance=np.sqrt(((p[:,None,:]-nearest)**2).sum(axis=2)).min(axis=1)
    return {'mean_point_to_fitted_segment_distance_pixels':float(distance.mean()),'maximum_point_to_fitted_segment_distance_pixels':float(distance.max()),'median_point_to_fitted_segment_distance_pixels':float(np.median(distance))}

def compare(root):
    import numpy as np,pydicom
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    linkage=json.loads((OUT/'original-dicom-contour-linkage-review.json').read_text());surface=json.loads((OUT/'source-surface-sampling-review.json').read_text());evaluation=json.loads((OUT/'native-model-evaluation-review.json').read_text());native=json.loads((OUT/'native-cine-linkage-review.json').read_text());native_by_sop={r['sop_uid']:r for r in native['linked_images']};adjustments={r['label']:r for r in evaluation['original_XML_plane_adjustments']};tris_file=OUT/surface['triangles_file']
    if hashlib.sha256(tris_file.read_bytes()).hexdigest()!=surface['triangles_sha256']:raise ValueError('Source triangles changed')
    triangles=np.frombuffer(gzip.decompress(tris_file.read_bytes()),dtype='<u4').reshape(-1,3);records=[];geometry_cache={};positions={};display=json.loads((OUT/'native-display-review.json').read_text());low,high=display['display_window_values'];shapes={}
    for contour in linkage['original_contours']:
        path=OUT/contour['file'];raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=contour['sha256']:raise ValueError('Original contour changed')
        points=np.asarray([[float(v) for v in line.split()] for line in raw.decode().splitlines() if line.strip()]);shapes[path.name]=points
        if contour['author_contour_kind'] not in ['icontour','ocontour']:continue
        row=native_by_sop[contour['CAP_sop_uid']];shift=next(r for r in adjustments[row['label']]['frames'] if r['frame']==row['frame']);orientation=np.asarray(row['native']['image_orientation_patient']);spacing=np.asarray(row['native']['pixel_spacing']);hypotheses=[]
        for origin_name,origin in [('native_DICOM_origin',shift['native_image_position_patient']),('original_XML_fit_origin',shift['original_XML_image_position'])]:
            segments={}
            for face in [0,1]:
                key=(row['frame'],face)
                if key not in positions:
                    mesh=next(r for r in surface['records'] if r['model_frame']==row['frame'] and r['source_face_xi3']==face);path=OUT/mesh['file'];raw=path.read_bytes()
                    if hashlib.sha256(raw).hexdigest()!=mesh['sha256']:raise ValueError('Source surface samples changed')
                    positions[key]=np.frombuffer(gzip.decompress(raw),dtype='<f8').reshape(-1,3)
                cache_key=(row['label'],row['frame'],face,origin_name)
                if cache_key not in geometry_cache:geometry_cache[cache_key]=plane_segments(positions[key],triangles,np.asarray(origin),orientation,spacing)
                segments[face]=geometry_cache[cache_key]
            for pixel_centre_offset in [0.,.5,1.]:
                # Raw author vertices are immutable. Hypotheses only change their interpretation against native pixel centres.
                distances={str(face):distance_to_segments(points-pixel_centre_offset,segments[face]) for face in [0,1]};closest=min([0,1],key=lambda face:distances[str(face)]['mean_point_to_fitted_segment_distance_pixels']);hypotheses.append({'plane_origin':origin_name,'raw_contour_minus_offset_in_native_pixel_centre_coordinates':pixel_centre_offset,'face_distances':distances,'nearest_fitted_source_face_xi3':closest})
        records.append({'source_contour_file':contour['file'],'source_contour_sha256':contour['sha256'],'author_kind':contour['author_contour_kind'],'CAP_sop_uid':contour['CAP_sop_uid'],'CAP_label':row['label'],'CAP_model_frame':row['frame'],'hypotheses':hypotheses,'clinical_fit_accuracy_approved':False})
    # Show annotated planes at both author phases. Pixel display uses literal author zero-top-left-corner coordinates.
    artifacts=[];warnings.filterwarnings('ignore',message='Invalid value for VR UI:.*',category=UserWarning,module='pydicom.valuerep')
    with zipfile.ZipFile(root/native['source_archive']['file']) as archive:
        for frame in [7,18]:
            fig,axes=plt.subplots(3,2,figsize=(11,15),layout='constrained')
            for i,label in enumerate(['SA8','SA7','SA6']):
                contour=next(c for c in linkage['original_contours'] if c['CAP_model_label']==label and c['CAP_model_frame']==frame and c['author_contour_kind']=='icontour');row=native_by_sop[contour['CAP_sop_uid']];raw=archive.read(row['native']['member'])
                if hashlib.sha256(raw).hexdigest()!=row['native']['sha256']:raise ValueError('Native source image changed')
                pixels=pydicom.dcmread(io.BytesIO(raw)).pixel_array
                for j,origin_name in enumerate(['native_DICOM_origin','original_XML_fit_origin']):
                    ax=axes[i,j];ax.imshow(pixels,cmap='gray',vmin=low,vmax=high,interpolation='nearest',extent=(0,256,256,0))
                    for face,colour in [(0,'#47e85e'),(1,'#ff4b55')]:
                        segments=np.asarray(geometry_cache[(label,frame,face,origin_name)])+.5;ax.add_collection(LineCollection(segments,colors=colour,linewidths=.8))
                    for kind,colour in [('icontour','#ffffff'),('ocontour','#ffcc33'),('p1contour','#42bcff'),('p2contour','#cb8bff')]:
                        found=[c for c in linkage['original_contours'] if c['CAP_model_label']==label and c['CAP_model_frame']==frame and c['author_contour_kind']==kind]
                        for c in found:
                            xy=shapes[Path(c['file']).name];closed=np.concatenate([xy,xy[:1]]);ax.plot(closed[:,0],closed[:,1],color=colour,linewidth=.8)
                    ax.set_xlim(0,256);ax.set_ylim(256,0);ax.axis('off');ax.set_title(f'{label} · model frame {frame} / author phase {frame+1}\n{origin_name}',fontsize=10)
            fig.suptitle('Original author contours: white inner / yellow outer / blue and violet papillary\nOriginal fitted faces: green xi3=0 / red xi3=1; no source contour or fit changes\nAuthor zero-corner display; pixel-centre hypotheses compared separately; clinical accuracy unapproved',fontsize=11)
            path=OUT/f'original-contour-model-phase-{frame+1:02d}-context.png';fig.savefig(path,dpi=130);plt.close(fig);artifacts.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    agreements={}
    for kind in ['icontour','ocontour']:
        selected=[r for r in records if r['author_kind']==kind];agreements[kind]={'contours':len(selected),'nearest_face_counts_across_all_six_origin_hypotheses':{str(face):sum(h['nearest_fitted_source_face_xi3']==face for r in selected for h in r['hypotheses']) for face in [0,1]}}
    supported=all(len([r for r in records if r['author_kind']==kind])==count and all(h['face_distances'][str(face)]['mean_point_to_fitted_segment_distance_pixels']<h['face_distances'][str(1-face)]['mean_point_to_fitted_segment_distance_pixels'] for r in records if r['author_kind']==kind for h in r['hypotheses']) for kind,count,face in [('icontour',18,0),('ocontour',9,1)])
    proof={'original_linkage_review_sha256':hashlib.sha256((OUT/'original-dicom-contour-linkage-review.json').read_bytes()).hexdigest(),'source_surface_sampling_review_sha256':hashlib.sha256((OUT/'source-surface-sampling-review.json').read_bytes()).hexdigest(),'comparisons':records,'nearest_face_summary':agreements,'source_contour_supported_face_roles':({'0':'source LV inner/endocardial boundary','1':'source LV outer/epicardial boundary'} if supported else {}),'source_semantic_evidence_is_clinical_geometry_approval':False,'distance_measurement_method':'one-way source-vertex to nearest piecewise-linear fitted-face intersection segment; not the author APD/perpendicular-normal benchmark','display_artifacts':artifacts,'original_contours_or_model_changed':False,'original_pixel_centre_convention_independently_calibrated':False,'source_face_semantics_supported_by_contour_comparison_only':supported,'clinical_geometry_or_function_approval':False,'papillary_contours_are_complete_3D_papillary_geometry':False,'complete_reportable_structures_verified':False,'runtime_promoted':False}
    (OUT/'original-contour-model-correspondence-review.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(agreements),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);compare(p.parse_args().source_root)
