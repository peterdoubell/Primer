"""Numerical source-basis equivalence does not approve source shifts or conflicting tissue roles."""
import gzip,hashlib,json,math,struct
from pathlib import Path
import pytest
from tools.anatomy_sources.evaluate_sunnybrook_native_model import OUT,evaluate_prolate,prolate_to_cartesian,project,patient_matrix,verified_model_inputs
from tools.anatomy_sources.review_sunnybrook_source_parameters import parse_exnode,parse_exelem

def load(name):return json.loads((OUT/name).read_text())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_recorded_independent_Zinc_samples_replay_from_original_parameters():
    proof=load('native-model-evaluation-review.json');source=load('original-parameter-source-review.json');elements=parse_exelem((OUT/'original-case-model/GlobalHermiteParam.exelem').read_bytes());matrix=patient_matrix(source['original_transform_16_values']);by_phase={phase:parse_exnode((OUT/'original-case-model'/f'SCD0000101_{phase}.model.exnode').read_bytes()) for phase in range(1,21)}
    assert verified_model_inputs()==proof['original_model_inputs'] and len(proof['original_model_inputs'])==22
    assert proof['all_original_phases_evaluated']==20 and len(proof['independent_scalar_basis_vs_Zinc'])==20
    assert sum(r['evaluated_points'] for r in proof['independent_scalar_basis_vs_Zinc'])==34560
    for row in proof['independent_scalar_basis_vs_Zinc']:
        assert row['maximum_cartesian_error']<1e-8 and row['maximum_patient_projection_error']<1e-8
    for sample in proof['samples']:
        focus,nodes=by_phase[sample['source_file_phase']];ps=evaluate_prolate(nodes,elements[sample['element_id']-1],sample['xi']);point=project(prolate_to_cartesian(ps,focus),matrix)
        assert max(abs(a-b) for a,b in zip(point,sample['zinc_patient']))<1e-8
    assert not proof['clinical_epicardial_endocardial_roles_assigned'] and not proof['spatial_registration_to_unadjusted_native_DICOM_validated'] and not proof['clinical_function_or_geometry_approved']

def test_original_image_adjustments_cannot_be_silently_called_native_registration():
    proof=load('native-model-evaluation-review.json');native={r['sop_uid']:r['native'] for r in load('native-cine-linkage-review.json')['linked_images']};groups=proof['original_XML_plane_adjustments'];assert len(groups)==18
    shifted=[g for g in groups if g['source_shift_length_in_declared_DICOM_mm']>0];assert {g['label'] for g in shifted}=={'LA2','SA2','SA4','SA5','SA6','SA7','SA8','SA9','SA10'}
    assert max(g['source_shift_length_in_declared_DICOM_mm'] for g in groups)==pytest.approx(5.744915221193431)
    for group in groups:
        assert len(group['frames'])==20
        for row in group['frames']:
            assert row['native_image_position_patient']==native[row['sop_uid']]['image_position_patient'] and not row['source_positions_changed_by_us']
            assert [a-b for a,b in zip(row['original_XML_image_position'],row['native_image_position_patient'])]==row['original_XML_minus_DICOM_position']
    assert proof['source_surface_parameter_order_review']=={'same_xi_surface_pairs':11520,'xi3_0_lambda_less_than_xi3_1':11520,'xi3_0_lambda_greater_than_xi3_1':0,'lambda_equal':0}
    assert proof['surface_tissue_role_validation']=='unresolved_original_conversion_vs_inspected_CAP_renderer_conflict'

def test_sampled_faces_preserve_all_original_phases_and_source_coordinates():
    proof=load('source-surface-sampling-review.json');elements=parse_exelem((OUT/'original-case-model/GlobalHermiteParam.exelem').read_bytes());matrix=patient_matrix(load('original-parameter-source-review.json')['original_transform_16_values']);resolution=proof['subdivisions_per_source_element_axis'];triangle_file=OUT/proof['triangles_file'];assert sha(triangle_file.read_bytes())==proof['triangles_sha256'];indices=struct.unpack('<'+str(len(gzip.decompress(triangle_file.read_bytes()))//4)+'I',gzip.decompress(triangle_file.read_bytes()));assert max(indices)<16*(resolution+1)**2
    assert {(r['source_file_phase'],r['source_face_xi3']) for r in proof['records']}=={(phase,face) for phase in range(1,21) for face in [0,1]}
    for row in proof['records']:
        path=OUT/row['file'];assert sha(path.read_bytes())==row['sha256'];raw=gzip.decompress(path.read_bytes());assert len(raw)==row['vertices']*24
        values=struct.unpack('<'+str(len(raw)//8)+'d',raw);assert all(math.isfinite(v) for v in values);focus,nodes=parse_exnode((OUT/'original-case-model'/f'SCD0000101_{row["source_file_phase"]}.model.exnode').read_bytes())
        # Replay several interior and boundary vertices from every patch, not just metadata counts.
        for element_index,element in enumerate(elements):
            for u,v in [(0,0),(7,19),(resolution,resolution)]:
                index=element_index*(resolution+1)**2+u*(resolution+1)+v;expected=project(prolate_to_cartesian(evaluate_prolate(nodes,element,[u/resolution,v/resolution,float(row['source_face_xi3'])]),focus),matrix)
                assert max(abs(a-b) for a,b in zip(values[index*3:index*3+3],expected))<1e-10
        assert row['maximum_sampled_triangle_barycentre_deviation_from_original_FE_face']<.03 and not row['clinical_tissue_role_assigned']
    assert not proof['fitting_smoothing_decimation_cap_addition_or_seam_welding_applied'] and not proof['closed_manifold_or_tissue_volume_verified'] and not proof['native_DICOM_registration_or_clinical_fidelity_approved'] and not proof['runtime_promoted']

def test_scientific_plane_intersection_retains_vertex_crossings():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.render_sunnybrook_model_correspondence import plane_segments
    # A plane through a triangle vertex and the opposite edge still has a line segment.
    vertices=np.array([[0.,0.,0.],[1.,0.,1.],[0.,1.,-1.]])
    result=plane_segments(vertices,np.array([[0,1,2]]),np.array([0.,0.,0.]),np.array([1.,0.,0.,0.,1.,0.]),np.array([1.,1.]))
    assert len(result)==1 and any(np.allclose(p,[0,0]) for p in result[0]) and any(np.allclose(p,[.5,.5]) for p in result[0])

def test_actual_Zinc_evaluates_seam_and_derivatives_without_relabelled_surfaces():
    Context=pytest.importorskip('cmlibs.zinc.context').Context
    elements=parse_exelem((OUT/'original-case-model/GlobalHermiteParam.exelem').read_bytes());matrix=patient_matrix(load('original-parameter-source-review.json')['original_transform_16_values'])
    for phase in range(1,21):
        context=Context('OriginalSourceTest');region=context.getDefaultRegion();assert region.readFile(str(OUT/'original-case-model'/f'SCD0000101_{phase}.model.exnode'))==1;assert region.readFile(str(OUT/'original-case-model/GlobalHermiteParam.exelem'))==1
        fm=region.findChildByName('heart').getFieldmodule();cache=fm.createFieldcache();field=fm.findFieldByName('coordinates');rc=fm.createFieldCoordinateTransformation(field);patient=fm.createFieldProjection(rc,fm.createFieldConstant([v for row in matrix for v in row]));mesh=fm.findMeshByDimension(3);focus,nodes=parse_exnode((OUT/'original-case-model'/f'SCD0000101_{phase}.model.exnode').read_bytes())
        for element in elements:
            for xi in [[.37,.63,0.],[.37,.63,1.],[.93,.25,.5]]:
                cache.setMeshLocation(mesh.findElementByIdentifier(element['element_id']),xi);status,actual=patient.evaluateReal(cache,3);expected=project(prolate_to_cartesian(evaluate_prolate(nodes,element,xi),focus),matrix)
                assert status==1 and max(abs(a-b) for a,b in zip(actual,expected))<1e-8

def test_model_and_plane_display_keeps_source_adjustments_and_role_conflict_explicit():
    proof=load('native-model-display-review.json');native={r['sop_uid']:r for r in load('native-cine-linkage-review.json')['linked_images']}
    assert not proof['source_pixels_changed'] and not proof['new_plane_registration_fit_or_model_repair_applied'] and not proof['quantitative_fit_accuracy_independently_approved'] and not proof['clinical_approval'] and not proof['surface_tissue_roles_assigned']
    assert len(proof['artifacts'])==3
    for artifact in proof['artifacts']:assert sha((OUT/artifact['file']).read_bytes())==artifact['sha256']
    assert len(proof['comparisons'])==12
    for row in proof['comparisons']:
        assert row['source_native_file_sha256']==native[row['sop_uid']]['native']['sha256']
        assert (row['label'],row['model_frame'])==(native[row['sop_uid']]['label'],native[row['sop_uid']]['frame'])
        assert all(n>0 for n in row['source_face_intersection_segment_counts'])

def test_changed_original_model_cannot_be_validated_against_itself(tmp_path,monkeypatch):
    import tools.anatomy_sources.evaluate_sunnybrook_native_model as evaluator
    (tmp_path/'model.exnode').write_bytes(b'altered source')
    (tmp_path/'original-parameter-source-review.json').write_text(json.dumps({'source_model_members':[{'file':'model.exnode','bytes':14,'sha256':sha(b'original data!')}]}))
    monkeypatch.setattr(evaluator,'OUT',tmp_path)
    with pytest.raises(ValueError,match='Original model file differs'):evaluator.verified_model_inputs()
