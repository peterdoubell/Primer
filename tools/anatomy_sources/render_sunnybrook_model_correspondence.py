#!/usr/bin/env python3
"""Compare original fitted FE faces with unchanged native pixels in native and source-adjusted planes."""
import argparse,gzip,hashlib,io,json,warnings,zipfile
from pathlib import Path
from tools.anatomy_sources.review_sunnybrook_source_parameters import OUT

def plane_segments(vertices,triangles,origin,orientation,spacing):
    import numpy as np
    normal=np.cross(orientation[:3],orientation[3:]);normal/=np.linalg.norm(normal);distance=(vertices-origin)@normal;selected=triangles[(distance[triangles].min(axis=1)<=0)&(distance[triangles].max(axis=1)>=0)];segments=[]
    for triangle in selected:
        intersections=[]
        for a,b in [(0,1),(1,2),(2,0)]:
            ia,ib=triangle[a],triangle[b];da,db=distance[ia],distance[ib]
            if abs(da)<1e-10:intersections.append(vertices[ia])
            if da*db<0:
                t=da/(da-db);intersections.append(vertices[ia]+t*(vertices[ib]-vertices[ia]))
        unique=[]
        for point in intersections:
            if not any(np.linalg.norm(point-prior)<1e-9 for prior in unique):unique.append(point)
        projected=[]
        for point in unique:
            delta=point-origin;projected.append([float(delta@orientation[:3]/spacing[1]),float(delta@orientation[3:]/spacing[0])])
        if len(projected)==2:segments.append(projected)

    return segments

def render(root):
    import numpy as np,pydicom
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    report=json.loads((OUT/'source-surface-sampling-review.json').read_text());eval_report=json.loads((OUT/'native-model-evaluation-review.json').read_text());native=json.loads((OUT/'native-cine-linkage-review.json').read_text());tri_path=OUT/report['triangles_file']
    if hashlib.sha256(tri_path.read_bytes()).hexdigest()!=report['triangles_sha256']:raise ValueError('Sampled original surface triangles changed')
    if report['source_evaluation_review_sha256']!=hashlib.sha256((OUT/'native-model-evaluation-review.json').read_bytes()).hexdigest():raise ValueError('Sampled surfaces refer to changed evaluation evidence')
    triangles=np.frombuffer(gzip.decompress(tri_path.read_bytes()),dtype='<u4').reshape(-1,3);adjustments={r['label']:r for r in eval_report['original_XML_plane_adjustments']};display=json.loads((OUT/'native-display-review.json').read_text());low,high=display['display_window_values'];records=[]
    warnings.filterwarnings('ignore',message='Invalid value for VR UI:.*',category=UserWarning,module='pydicom.valuerep')
    with zipfile.ZipFile(root/native['source_archive']['file']) as archive:
        for frame in [0,10]:
            fig,axes=plt.subplots(3,2,figsize=(11,15),layout='constrained')
            for row_index,label in enumerate(['LA2','SA6','SA8']):
                row=next(r for r in native['linked_images'] if r['label']==label and r['frame']==frame);raw=archive.read(row['native']['member'])
                if hashlib.sha256(raw).hexdigest()!=row['native']['sha256']:raise ValueError('Original native image changed')
                pixels=pydicom.dcmread(io.BytesIO(raw)).pixel_array;shift=next(r for r in adjustments[label]['frames'] if r['frame']==frame);orientation=np.asarray(row['native']['image_orientation_patient']);spacing=np.asarray(row['native']['pixel_spacing'])
                for col,(name,origin) in enumerate([('Unadjusted native DICOM plane',shift['native_image_position_patient']),('Original XML-adjusted fit plane',shift['original_XML_image_position'])]):
                    ax=axes[row_index,col];ax.imshow(pixels,cmap='gray',vmin=low,vmax=high,interpolation='nearest');counts=[]
                    for face,colour in [(0,'#47e85e'),(1,'#ff4b55')]:
                        mesh=next(r for r in report['records'] if r['model_frame']==frame and r['source_face_xi3']==face);path=OUT/mesh['file']
                        if hashlib.sha256(path.read_bytes()).hexdigest()!=mesh['sha256']:raise ValueError('Source-derived surface samples changed')
                        vertices=np.frombuffer(gzip.decompress(path.read_bytes()),dtype='<f8').reshape(-1,3);segments=plane_segments(vertices,triangles,np.asarray(origin),orientation,spacing);ax.add_collection(LineCollection(segments,colors=colour,linewidths=.85));counts.append(len(segments))
                    ax.set_xlim(-.5,255.5);ax.set_ylim(255.5,-.5);ax.axis('off');ax.set_title(f'{label} · frame {frame}\n{name}\nSource shift {adjustments[label]["source_shift_length_in_declared_DICOM_mm"]:.3f} declared mm',fontsize=10)
                    records.append({'label':label,'model_frame':frame,'sop_uid':row['sop_uid'],'source_native_file_sha256':row['native']['sha256'],'plane_display':name,'source_plane_origin':origin,'source_face_intersection_segment_counts':counts})
            fig.suptitle('Original fitted LV model: green source face xi3=0 / red source face xi3=1\nSame unchanged native pixels in both columns; source fit-plane shifts retained, not new registration\nInspected CAP code tissue roles conflict with apparent nesting; no clinical surface roles assigned',fontsize=12)
            filename=f'native-model-plane-comparison-frame-{frame:02d}.png';fig.savefig(OUT/filename,dpi=130);plt.close(fig)
    proof={'artifacts':[{'file':f'native-model-plane-comparison-frame-{frame:02d}.png','sha256':hashlib.sha256((OUT/f'native-model-plane-comparison-frame-{frame:02d}.png').read_bytes()).hexdigest()} for frame in [0,10]],'comparisons':records,'source_pixels_changed':False,'new_plane_registration_fit_or_model_repair_applied':False,'quantitative_fit_accuracy_independently_approved':False,'clinical_approval':False}
    (OUT/'native-model-display-review.json').write_text(json.dumps(proof,indent=2)+'\n');print('Original model/native-plane comparisons rendered with both coordinate origins explicit.')
def render_surface_views():
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    report=json.loads((OUT/'source-surface-sampling-review.json').read_text());triangles=np.frombuffer(gzip.decompress((OUT/report['triangles_file']).read_bytes()),dtype='<u4').reshape(-1,3);fig=plt.figure(figsize=(12,7),layout='constrained')
    for index,frame in enumerate([0,10]):
        ax=fig.add_subplot(1,2,index+1,projection='3d');bounds=[]
        for face,colour in [(0,'#47e85e'),(1,'#ff4b55')]:
            row=next(r for r in report['records'] if r['model_frame']==frame and r['source_face_xi3']==face);raw=(OUT/row['file']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Original evaluated surface file changed')
            vertices=np.frombuffer(gzip.decompress(raw),dtype='<f8').reshape(-1,3);ax.add_collection3d(Poly3DCollection(vertices[triangles],facecolors=colour,edgecolors='none',alpha=.22,rasterized=True));bounds.extend([vertices.min(axis=0),vertices.max(axis=0)])
        low=np.asarray(bounds).min(axis=0);high=np.asarray(bounds).max(axis=0);centre=(low+high)/2;radius=(high-low).max()/2
        ax.set_xlim(centre[0]-radius,centre[0]+radius);ax.set_ylim(centre[1]-radius,centre[1]+radius);ax.set_zlim(centre[2]-radius,centre[2]+radius);ax.set_box_aspect((1,1,1));ax.set_proj_type('ortho');ax.view_init(elev=18,azim=-65);ax.set_xlabel('Source patient X');ax.set_ylabel('Source patient Y');ax.set_zlabel('Source patient Z');ax.set_title(f'Original model frame {frame} / source file phase {frame+1}')
    fig.suptitle('Original finite-element LV surface samples in source patient coordinates\nGreen xi3=0 / red xi3=1; source tissue-role conflict unresolved\nBoth original faces only: no added basal cap, valves, RV, scar or repaired seams',fontsize=12)
    path=OUT/'original-fe-surface-phase-context.png';fig.savefig(path,dpi=130);plt.close(fig)
    p=OUT/'native-model-display-review.json';proof=json.loads(p.read_text());proof['artifacts'].append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()});proof['surface_frames_displayed']=[0,10];proof['surface_tissue_roles_assigned']=False;p.write_text(json.dumps(proof,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);render(p.parse_args().source_root);render_surface_views()
