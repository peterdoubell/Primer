#!/usr/bin/env python3
"""Retain full source-based TAVI anatomy, candidate access routes and conditional valve-in-valve planning."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for

ROOT=Path(__file__).resolve().parents[2]
IDENT='ra.ct-tavi'
URLS=['https://radiologyassistant.nl/cardiovascular/thoracic-aorta/acute-aortic-syndrome-1',
 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7160220/','https://www.jacc.org/doi/10.1016/j.jcmg.2018.12.003',
 'https://pmc.ncbi.nlm.nih.gov/articles/PMC9743261/','https://pmc.ncbi.nlm.nih.gov/articles/PMC12281215/']

def build():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];g=ref['reporting'];structures=[]
    def add(key,name,children,steps,side='not_applicable',conditional=None):
        structures.append({'id':'tavi.'+key,'name':name,'tissue_class':'tavi_reportable_anatomy_or_planning_interface',
            'required_parts':[{'id':'tavi.'+key+'.'+p,'name':p.replace('_',' ').capitalize()} for p in children.split()],
            'laterality':side,'modality_scope':['CT'],'requires_site_instantiation':True,
            'condition':conditional or 'Instantiate every actual site, variant and source-defined plane. Preserve patient, side, phase, coverage, calibration and uncertainty; no generic model or isolated measurement establishes procedural suitability.',
            'requirement_basis':'effective_tavi_reporting_and_conditional_device_access_scope',
            'report_refs':[{'checklist_index':i,**g['checklist'][i]} for i in steps],'walkthrough_step_indices':steps,
            'source_urls':URLS,'context_requirements':{'purpose':'anatomical_reference'}})
    add('annulus','Actual virtual basal annular ring','each_attachment_nadir source_defined_basal_plane complete_contour area perimeter orthogonal_minimum_diameter orthogonal_maximum_diameter actual_phase edge_and_endpoint_conventions calibration_and_unresolved_contour',[0])
    add('lvot','Actual left ventricular outflow tract','covered_wall_and_lumen annular_relation subannular_levels minimum_maximum_diameters area_perimeter_if_measured septal_and_fibrous_interfaces each_calcium_focus phase_and_unresolved_extent',[1])
    for side,label in [('right','Right coronary'),('left','Left coronary'),('noncoronary','Non-coronary')]:
        lateral=side if side in ('right','left') else 'not_applicable'
        add(side+'_cusp',label+' cusp','actual_cusp_morphology hinge_attachment_nadir commissural_boundaries free_margin cusp_length_height_if_measured each_leaflet_calcium_focus leaflet_to_coronary_or_stj_relation unresolved_cusp_or_motion',[1,2],lateral)
        add(side+'_sinus',label+' sinus','complete_wall_boundary sinus_width_and_axis each_asymmetric_dimension height_and_plane annulus_stj_relation coronary_origin_relation cusp_commissural_interfaces phase_edge_and_unresolved_boundary',[2,3],lateral)
    for key,label in [('right_left','Right/left'),('right_noncoronary','Right/non-coronary'),('left_noncoronary','Left/non-coronary')]:
        add(key+'_commissure',label+' commissural/interleaflet interface','source_resolved_commissure actual_cusp_correspondence interleaflet_triangle_if_resolved annulus_stj_relation device_alignment_reference_if_used unresolved_interface',[1,2,3])
    add('bicuspid_variants','Every actual bicuspid/other valve variant','cusp_number_and_fusion each_raphe each_calcified_raphe actual_attachment_nadirs sinus_and_commissural_correspondence root_asymmetry supra_annular_plane_if_actually_used unresolved_variant_or_sizing_method',[0,1,3])
    add('calcium','Each actually observed calcium region','leaflet_site annular_site lvot_site circumferential_and_longitudinal_extent bulk_and_protrusion neighbouring_coronary_or_septal_interfaces actual_scoring_acquisition_and_method score_or_unavailable_status contrast_and_blooming_limit',[1,2])
    add('membranous_septum','Actual membranous/septal interface if assessed','source_resolved_boundary annular_lvot_relation actual_length_and_plane calcium_or_device_relation conduction_risk_context unresolved_visibility_or_function',[1])
    add('aortic_mitral_interface','Covered aortic-mitral/root support interface','actual_fibrous_continuity lvot_relation cusp_root_relationship each_calcium_or_repair_interface unresolved_boundary',[1])
    for side in ('right','left'):
        add(side+'_coronary_ostium',side.capitalize()+' coronary ostium','actual_sinus_origin inferior_ostial_margin annular_plane_reference ostial_height_and_plane ostial_width_if_measured sinus_width_at_ostium leaflet_length_bulk_relation stj_relation prior_valve_or_graft_relation unresolved_measurement_or_obstruction_context',[2],side)
        add(side+'_coronary_course',side.capitalize()+' covered proximal coronary course','covered_course lumen_and_wall each_variant_or_graft_origin each_stenosis_or_device_if_resolved neighbouring_leaflet_or_root_relation uncovered_coronary_or_function_limit',[2],side)
    add('obstruction_anatomy','Actual combined obstruction-risk anatomy','coronary_heights sinus_dimensions stj_dimensions leaflet_length_bulk_and_calcium displaced_leaflet_or_neoskirt_assumptions coronary_sinus_sequestration_interfaces actual_virtual_model_if_performed device_deployment_assumptions_and_uncertainty',[2,3])
    add('stj','Actual sinotubular junction','complete_contour orthogonal_minimum_maximum_diameters annular_plane_reference height_to_reference_plane sinus_ascending_transition leaflet_coronary_and_device_interfaces phase_edge_and_unresolved_boundary',[3])
    add('ascending_aorta','Covered ascending aorta','covered_course outer_inner_contours orthogonal_maximum_diameter named_level local_axis_and_tortuosity each_wall_abnormality prior_graft_or_repair unresolved_extent',[3,4])
    add('root_angulation','Actual root/ascending angulation and projection method','source_axis_reference patient_reference_plane angle_and_method annular_plane_orientation fluoroscopic_projection_if_planned actual_device_approach_relation phase_position_and_uncertainty',[3])
    add('aortic_access_course','Complete actual aortic access course','arch_branch_origins thoracic_course diaphragmatic_course abdominal_course bifurcation each_curvature_or_tortuosity each_stenosis_thrombus_ulcer_dissection_or_aneurysm each_graft_or_stent proposed_route_and_uncovered_extent',[4])
    artery='actual_origin covered_course inner_lumen_contour outer_wall_boundary minimum_orthogonal_lumen_and_location calcification_extent_distribution tortuosity_centreline each_stenosis_occlusion_or_aneurysm each_thrombus_dissection_or_graft actual_device_or_sheath_context uncovered_route_extent'
    for side in ('right','left'):
        for key,name in [('common_iliac','common iliac artery'),('external_iliac','external iliac artery'),
                         ('internal_iliac','internal iliac branch relationship'),('common_femoral','common femoral artery'),
                         ('femoral_bifurcation','femoral bifurcation and covered branches')]:
            add(side+'_'+key,side.capitalize()+' '+name,artery,[4],side)
        for key,name in [('subclavian','subclavian candidate route'),('axillary','axillary candidate route'),('carotid','carotid candidate route')]:
            add(side+'_'+key,side.capitalize()+' '+name,artery,[4],side,
                'Conditional on the actual proposed alternative access and acquired source. Instantiate the whole candidate route and critical neighbouring branches; unacquired routes remain unassessed.')
        add(side+'_vertebral_relation',side.capitalize()+' alternative-access vertebral relation','actual_origin source_resolved_course access_vessel_interface each_variant_or_compromise uncovered_neurological_supply',[4],side)
    add('brachiocephalic_access','Actual brachiocephalic/arch access relationship','origin complete_covered_course carotid_subclavian_bifurcation source_lumen_wall_and_calcium route_angle_device_relation uncovered_extent',[4])
    add('bypass_grafts','Actual coronary/vascular grafts affecting access','each_graft_identity operative_history actual_origin_and_course access_vessel_relationship source_patency_or_stenosis unvisualised_graft_and_planning_limit',[2,4])
    add('transcaval_target','Conditional transcaval aortic/caval target','aortic_wall_target caval_wall_target interposed_tissue_or_bowel no_crossing_structure_assumption actual_calcium_window source_level_and_geometry closure_device_assumptions uncovered_route_and_uncertainty',[4])
    add('transapical_target','Conditional transapical target','actual_lv_apical_wall source_ventricular_geometry proposed_entry_and_device_axis neighbouring_coronary_or_thoracic_interfaces clinical_function_and_source_limits',[4])
    add('transaortic_target','Conditional direct aortic target','actual_entry_wall covered_route root_arch_branch_relations each_calcium_or_device_obstacle source_plane_and_proposed_axis surgical_and_uncovered_extent_limits',[4])
    add('access_complications_context','Actual pre-existing access/pathology interfaces','each_prior_device_or_surgery each_graft_anastomosis each_pseudoaneurysm_or_dissection each_venous_or_bowel_interface each_hazardous_wall_region clinical_history_and_full_route_limit',[4])
    add('prior_surgical_valve','Actual prior surgical valve if present','operative_identifier_and_model labelled_size_vs_actual_internal_diameter frame_or_strut_course leaflet_or_stentless_morphology coronary_ostia_relation stj_relation each_pannus_thrombus_or_calcified_region source_history_and_artefact_limits',[0,1,2,3])
    add('prior_transcatheter_valve','Actual prior transcatheter valve if present','identifier_model_and_deployment_history frame_dimensions_and_shape implantation_depth commissural_orientation leaflet_or_neoskirt_geometry coronary_access_relation stj_seal_and_sequestration_relation source_quality_and_unknown_device_geometry',[0,1,2,3])
    add('virtual_valve_model','Conditional actual virtual device model','source_segmentation_boundaries chosen_device_geometry assumed_expansion deployment_depth tilt_and_commissural_alignment virtual_valve_to_coronary_distances virtual_valve_to_stj_distances source_method_and_uncertainty original_measurement_vs_simulation_distinction',[0,2,3])
    add('clinical_valve_context','Actual clinical/functional valve context','available_echo_or_clinical_diagnosis stenosis_or_regurgitation_source actual_functional_measurement_if_supplied treatment_and_prior_procedure_context ct_morphology_not_function_limit heart_team_device_and_risk_source',[0,1,2,3,4])
    add('adjacent_chambers','Actual source-covered neighbouring chamber findings','lv_geometry_and_lvot each_intracavitary_filling_defect_if_present left_atrial_root_relationship myocardial_or_pericardial_context clinical_or_alternative_modality_confirmation source_phase_and_uncovered_extent',[1,3])
    add('planning_limits','Actual acquisition and planning controls','patient_and_study_identity root_and_route_coverage actual_ecg_gating cardiac_phase_and_reconstruction_quality annular_landmark_plane voxel_calibration_and_units contrast_or_scoring_protocol each_actual_measurement_endpoint comparison_and_registration_if_used device_specific_instructions_and_version multidisciplinary_decision_and_unresolved_assumptions',[0,1,2,3,4])
    return {'investigation_id':IDENT,'module_id':'rad.5.tavi-ct','title':'CT TAVI/TAVR planning',
        'scope_status':'expanded_draft_requires_independent_anatomical_and_clinical_review','modality_scope':['CT'],
        'sources':[{'title':title,'url':url,'reviewed_at':'2026-10-06','review_status':status} for title,url,status in zip(
            ['Radiology Assistant TAVI/TAVR','ESCR acquisition/measurement consensus','SCCT TAVI/TAVR consensus','CTA step-by-step planning source','Conditional native/SAVR/TAVR planning source'],URLS,
            ['effective_source_scope_reviewed','primary_protocol_and_coverage_extract_reviewed','primary_risk_scoring_and_VIV_extract_reviewed','original_XML_and_figures_reviewed','primary_planning_group_extract_reviewed'])],
        'source_contract_sha256':digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')}),
        'reporting_checklist':g['checklist'],'reporting_template_sections':g['template_sections'],'structures':structures,
        'expansion_rules':['Instantiate every actual cusp, calcium focus, coronary/device interface and candidate access route. Conditional/unacquired anatomy is not normal.',
            'Each leaf requires independently reviewed image, schematic and model evidence; labels or a generic model do not provide clinical fidelity.',
            'Preserve source-derived measurements separately from device simulations and heart-team decisions.'],
        'source_scope_issues':['Clinical stenosis/regurgitation, rupture/conduction/obstruction risk and procedural suitability are not established by an isolated static feature.',
            'No universal coronary-height, sinus-width, access-diameter or device-sizing threshold is introduced.',
            'Bicuspid/other valve anatomy may require adapted landmark/plane methods; do not force a three-cusp assumption.',
            'Actual calcium scoring acquisition/method is separate from qualitative calcium in contrast CT.',
            'Virtual coronary/STJ distances require actual device/deployment assumptions; prior SAVR/TAVR and native anatomy are not interchangeable.',
            'Primary consensus extracts and local worksheet review are not full current device-specific or multidisciplinary approval.'],
        'functional_evidence_requirements':['Annular/root/access dimensions require actual acquisition quality, calibrated source and defined planes.',
            'Valve function and obstruction/complication outcomes require clinical evidence and source-based heart-team planning.',
            'Published annotated snapshots are not independently calibrated patient models or simulation outcomes.'],
        'clinical_validation_status':'draft_requires_cardiovascular_radiologist_and_structural_heart_team_review'}

if __name__=='__main__':
    item=build();path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    data['investigations']=[i for i in data['investigations'] if i['investigation_id']!=IDENT]+[item]
    data['scope']['catalog_investigation_ids']=[i['investigation_id'] for i in data['investigations']]
    path.write_text(json.dumps(data,indent=2)+'\n')
    print(len(item['structures']),'groups;',len(requirements_for(item)),'leaves;',len(requirements_for(item))*3,'representation obligations')
