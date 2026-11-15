#!/usr/bin/env python3
"""Sample the validated original FE faces without refitting, seam welding, closing or smoothing."""
import argparse,gzip,hashlib,json,struct
from pathlib import Path
from tools.anatomy_sources.evaluate_sunnybrook_native_model import evaluate_prolate,prolate_to_cartesian,project,patient_matrix,verified_model_inputs
from tools.anatomy_sources.review_sunnybrook_source_parameters import OUT,parse_exnode,parse_exelem

def sample(resolution=32):
    import numpy as np
    if resolution<4 or resolution>128:raise ValueError('Source sampling resolution outside supported audit range')
    original_inputs=verified_model_inputs()
    review=json.loads((OUT/'native-model-evaluation-review.json').read_text())
    from tools.anatomy_sources import evaluate_sunnybrook_native_model as evaluator
    if review.get('evaluator_script_sha256')!=hashlib.sha256(Path(evaluator.__file__).read_bytes()).hexdigest() or review['original_model_inputs']!=original_inputs:raise ValueError('Independent source basis comparison is stale')
    if not review['source_model_basis_and_coordinate_projection_numerically_compared']:raise ValueError('Independent source basis comparison required')
    output=OUT/'evaluated-source-surfaces';output.mkdir(exist_ok=True);source=json.loads((OUT/'original-parameter-source-review.json').read_text());elements=parse_exelem((OUT/'original-case-model/GlobalHermiteParam.exelem').read_bytes());matrix=patient_matrix(source['original_transform_16_values']);cells=[]
    for patch in range(16):
        offset=patch*(resolution+1)**2
        for i in range(resolution):
            for j in range(resolution):
                a=offset+i*(resolution+1)+j;b=a+resolution+1;c=b+1;d=a+1;cells.extend([(a,b,c),(a,c,d)])
    triangles=np.asarray(cells,dtype='<u4');tpath=output/'source-face-triangles.u32.gz'
    with gzip.GzipFile(filename=str(tpath),mode='wb',mtime=0) as f:f.write(triangles.tobytes())
    records=[]
    for phase in range(1,21):
        focus,nodes=parse_exnode((OUT/'original-case-model'/f'SCD0000101_{phase}.model.exnode').read_bytes())
        for face,source_role in [(0,'source_epicardial'),(1,'source_endocardial')]:
            points=[];error=0.
            def point(element,u,v):return project(prolate_to_cartesian(evaluate_prolate(nodes,element,[u,v,float(face)]),focus),matrix)
            for element in elements:
                patch=np.asarray([point(element,i/resolution,j/resolution) for i in range(resolution+1) for j in range(resolution+1)]).reshape(resolution+1,resolution+1,3);points.extend(patch.reshape(-1,3))
                # Check both actual triangle barycentres against the curved original face.
                for i in range(resolution):
                    for j in range(resolution):
                        a,b,c,d=patch[i,j],patch[i+1,j],patch[i+1,j+1],patch[i,j+1]
                        for u,v,linear in [((i+2/3)/resolution,(j+1/3)/resolution,(a+b+c)/3),((i+1/3)/resolution,(j+2/3)/resolution,(a+c+d)/3)]:error=max(error,float(np.linalg.norm(np.asarray(point(element,u,v))-linear)))
            values=np.asarray(points,dtype='<f8');path=output/f'phase-{phase:02d}-xi3-{face}.positions.f64.gz'
            with gzip.GzipFile(filename=str(path),mode='wb',mtime=0) as f:f.write(values.tobytes())
            records.append({'source_file_phase':phase,'model_frame':phase-1,'source_face_xi3':face,'inspected_CAP_reader_face_role_claim':source_role,'clinical_tissue_role_assigned':False,'file':str(path.relative_to(OUT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'vertices':len(values),'triangles':len(triangles),'source_patient_bounds':[values.min(axis=0).tolist(),values.max(axis=0).tolist()],'maximum_sampled_triangle_barycentre_deviation_from_original_FE_face':error})
        print('Original phase',phase,'both FE faces sampled',flush=True)
    report={'sampling_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'original_model_inputs':original_inputs,'source_surface_role_validation':'unresolved_original_conversion_vs_inspected_CAP_renderer_conflict','source_evaluation_review_sha256':hashlib.sha256((OUT/'native-model-evaluation-review.json').read_bytes()).hexdigest(),'subdivisions_per_source_element_axis':resolution,'original_surface_elements_per_face':16,'triangles_file':str(tpath.relative_to(OUT)),'triangles_sha256':hashlib.sha256(tpath.read_bytes()).hexdigest(),'triangle_index_dtype':'little_endian_uint32','position_dtype':'little_endian_float64','records':records,'all_20_original_model_phases_sampled':True,'original_xml_projection_applied':True,'source_patient_units':'DICOM/model-declared physical coordinates; independent scanner calibration unverified','source_files_changed':False,'fitting_smoothing_decimation_cap_addition_or_seam_welding_applied':False,'native_DICOM_registration_or_clinical_fidelity_approved':False,'closed_manifold_or_tissue_volume_verified':False,'runtime_promoted':False,'limits':['Each original element remains a separate sampled patch; duplicate boundary vertices and source angular rounding are retained, not silently welded.','Only source xi3_0/xi3_1 LV fitted surfaces; basal cap, RV, tissue layers, valves and scar are not newly supplied.','Barycentre deviation is numerical sampling evidence, not a global error bound, source fit accuracy or voxel calibration.','Inspected CAP reader face-role claims conflict with apparent inner/outer nesting in this converted case; neutral xi3 face IDs retained and tissue roles not approved.']}
    (OUT/'source-surface-sampling-review.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--resolution',type=int,default=32);sample(p.parse_args().resolution)
