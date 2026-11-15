#!/usr/bin/env python3
"""Bind reproducible aortic-level, root-landmark and measurement-convention fidelity requirements."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for

ROOT=Path(__file__).resolve().parents[2]
IDENT='ra.thoracic-aorta-measurement'
URLS=['https://radiologyassistant.nl/cardiovascular/thoracic-aorta/aorta-dilatation-measurements',
      'https://pmc.ncbi.nlm.nih.gov/articles/PMC9860464/','https://pmc.ncbi.nlm.nih.gov/articles/PMC3874367/',
      'https://pmc.ncbi.nlm.nih.gov/articles/PMC10405341/']

def build():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];guide=ref['reporting'];structures=[]
    def parts(s):return [{'id':p,'name':p.replace('_',' ').capitalize()} for p in s.split()]
    def add(key,name,children,steps,side='not_applicable'):
        structures.append({'id':'aortic_measurement.'+key,'name':name,'tissue_class':'aortic_measurement_structure_or_control',
            'required_parts':[{'id':'aortic_measurement.'+key+'.'+r['id'],'name':r['name']} for r in parts(children)],
            'laterality':side,'modality_scope':['CT','MRI','Ultrasound'],
            'condition':'Instantiate each actual measured level, anatomy/variant and source plane. Preserve actual patient, modality, phase, edge convention, calibration, coverage and uncertainty; unmeasured regions are not normal.',
            'requirement_basis':'effective_thoracic_aorta_measurement_reporting_scope',
            'report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in steps],
            'walkthrough_step_indices':steps,'source_urls':URLS,'requires_site_instantiation':True,
            'context_requirements':{'purpose':'anatomical_reference'}})
    level='source_resolved_outer_contour source_resolved_inner_contour proximal_distal_extent local_axis_or_centreline orthogonal_plane named_measurement_landmark maximum_diameter_and_axis perpendicular_minor_diameter_if_relevant wall_abnormality_and_edge_convention phase_calibration_and_unresolved_boundary unresolved_or_uncovered_extent'
    for key,name,steps in [('annulus','Virtual basal annular ring',[0,1]),('sinotubular_junction','Sinotubular junction',[1]),
        ('proximal_ascending','Proximal ascending aorta',[2]),('maximal_ascending','Actual maximal ascending level',[2]),
        ('distal_ascending','Distal ascending/arch transition',[2,3]),('proximal_arch','Proximal arch',[3]),
        ('mid_arch','Mid arch',[3]),('distal_arch','Distal arch',[3]),('isthmus','Isthmus',[3,4]),
        ('proximal_descending','Proximal descending aorta',[4]),('distal_descending','Distal descending aorta',[4]),
        ('diaphragmatic_level','Diaphragmatic aorta if measured',[4]),('abdominal_protocol_levels','Each actual abdominal protocol level',[4])]:
        add(key,name,level,steps)
    for key,name,side in [('right_sinus','Right coronary sinus','right'),('left_sinus','Left coronary sinus','left'),('noncoronary_sinus','Non-coronary sinus','not_applicable')]:
        add(key,name,'complete_covered_sinus_wall cusp_attachment_nadir_if_resolved commissural_boundaries maximum_bulge_plane each_sinus_to_sinus_pair each_sinus_to_commissure_axis root_asymmetry_and_orthogonal_dimensions coronary_or_adjacent_structure_relation edge_phase_and_comparison_method unresolved_cusp_or_sinus_identity',[0,1],side)
    for key,name in [('right_cusp','Right coronary cusp'),('left_cusp','Left coronary cusp'),('noncoronary_cusp','Non-coronary cusp')]:
        add(key,name,'actual_cusp_morphology attachment_hinge_course source_resolved_nadir commissural_attachments free_margin_if_resolved phase_motion_and_visibility_limit',[1])
    for key,name in [('right_left_commissure','Right/left commissural interface'),('right_noncoronary_commissure','Right/non-coronary commissural interface'),('left_noncoronary_commissure','Left/non-coronary commissural interface')]:
        add(key,name,'source_resolved_commissure cusp_and_sinus_identity interleaflet_triangle_if_resolved sinotubular_relation measurement_axis_endpoint uncertainty_or_variant',[1])
    add('basal_plane','Landmark-defined virtual basal plane','each_actual_attachment_nadir fitted_or_reformatted_plane_method orthogonal_major_minor_axes contour_area_if_measured perimeter_if_measured geometric_and_phase_limits not_assumed_fixed_slice_offset',[0,1])
    add('root_maximum','Maximum and asymmetric root dimensions','actual_maximum_sinus_to_sinus_axis each_additional_asymmetric_dimension named_edge_convention cardiac_phase exact_plane source_endpoint_coordinates_if_available separately_named_legacy_average_or_axis unresolved_maximum',[0,1])
    add('lvot','Covered left ventricular outflow tract and root transition','covered_wall_and_lumen basal_plane_relation muscular_fibrous_interfaces_if_resolved source_long_axis_plane phase_motion_and_uncovered_extent',[1])
    add('root_support','Covered root support and adjoining interfaces','aortic_mitral_continuity_if_resolved membranous_septal_interface_if_resolved ventricular_septal_interface_if_resolved left_atrial_relation each_actual_support_or_boundary_limit',[1])
    for key,name,side in [('right_coronary_ostium','Right coronary origin','right'),('left_coronary_ostium','Left coronary origin','left')]:
        add(key,name,'actual_ostial_position sinus_identity annulus_sinotubular_relation covered_proximal_course measurement_landmark_relation source_coverage_and_visibility_limit',[1],side)
    for key,name,side in [('brachiocephalic_origin','Brachiocephalic origin','right'),('left_carotid_origin','Left carotid origin','left'),('left_subclavian_origin','Left subclavian origin','left')]:
        add(key,name,'source_origin covered_course arch_level_reference local_axis_relation actual_variant_or_common_trunk uncovered_extent',[3],side)
    add('valve_root_variants','Each actual bicuspid/other root variant','actual_cusp_number_or_fusion raphe_if_present actual_attachment_nadirs sinus_and_commissural_correspondence root_asymmetry alternate_plane_method unresolved_variant_or_function',[0,1])
    add('arch_variants','Each actual arch/course variant','arch_side_and_course each_branch_origin_variant local_axis_or_centreline each_affected_measurement_level named_comparison_landmark uncovered_or_unresolved_extent',[2,3,4])
    add('ascending_length','Actual ascending length/elongation method','proximal_reference_endpoint distal_reference_endpoint complete_covered_centreline centreline_length_method curvature_and_tortuosity plane_and_source_limits',[2])
    add('wall_conditions','Each actual abnormal measured wall region','source_wall_boundary each_atherosclerotic_or_calcified_region each_thickened_or_thrombotic_region longitudinal_circumferential_extent inner_outer_edge_choice source_calibration_and_unresolved_interface',[0,1,2,3,4])
    add('repair_if_present','Actual prior root/aortic repair if present','operative_history_and_date every_actual_graft_or_prosthesis source_native_to_graft_interface each_anastomosis_or_seal every_reimplanted_branch_or_coronary actual_measured_lumen_and_outer_contour device_artefact_and_uncovered_extent',[1,2,3,4,5])
    add('comparison','Each actual level/timepoint comparison','current_and_prior_source_identity dates_and_interval identical_named_level source_phase_and_gating source_edge_and_axis_conventions comparable_plane_or_remeasurement current_and_prior_dimensions numerical_difference method_related_uncertainty unresolved_or_unavailable_comparison',[5])
    add('reference_context','Actual reference/indexing and clinical interpretation','age_sex_and_body_size_if_available named_reference_population_or_guideline indexing_formula_if_used source_height_weight_or_bsa index_units_and_measurement_method applicable_variant_or_disease_context uncertainty_and_clinical_threshold_source',[0,1,2,3,4,5])
    add('acquisition','Actual acquisition and measurement controls','actual_modality actual_cranial_caudal_coverage ecg_synchronisation cardiac_phase contrast_or_sequence reconstruction_thickness_and_increment original_voxel_units_and_calibration original_source_series_and_planes motion_or_metal_artefact plane_centreline_reconstruction_method edge_and_summary_convention unavailable_source_measurements_and_limits',[0,1,2,3,4,5])
    return {'investigation_id':IDENT,'module_id':'rad.5.aorta','title':'CT thoracic aorta measurement',
        'scope_status':'expanded_draft_requires_independent_anatomical_and_clinical_review','modality_scope':['CT','MRI','Ultrasound'],
        'sources':[{'title':t,'url':u,'reviewed_at':'2026-10-06','review_status':s} for t,u,s in zip(
            ['Radiology Assistant aorta measurement','ACC/AHA 2022 measurement recommendations','CT/MRI thoracic aorta review','Valve-sparing root imaging source'],URLS,
            ['effective_scope_reviewed','primary_recommendation_text_reviewed','original_XML_and_captions_reviewed','primary_basal_ring_and_variant_extract_reviewed'])],
        'source_contract_sha256':digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')}),
        'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':structures,
        'expansion_rules':['Instantiate every actual level, axis, contour, variant and comparison timepoint; children are a known floor.',
            'Each leaf requires independently reviewed image, schematic and model evidence; numerical calibration alone does not approve boundary or diagnostic interpretation.',
            'Preserve modality-specific edge/phase conventions and actual coverage; an average does not replace maximum/asymmetric dimensions.'],
        'source_scope_issues':['Virtual basal ring is landmark-defined; it is not a universal one-slice-below plane and variants must be identified.',
            'Maximum sinus-to-sinus and asymmetric root dimensions remain distinct from historical averaged/alternative-axis values.',
            'Inner/outer/leading-edge and phase conventions are not interchangeable; abnormal wall boundaries and modality need explicit source.',
            'No fixed small millimetre change or generic sex-only threshold is adopted as a universal surveillance/surgical rule.',
            'The 2024 proximal-aorta review is CC BY-NC; its images are not commercial-cleared or packaged from that grant.',
            'Clinical/variant/guideline and complete independent anatomical review remain outstanding.'],
        'functional_evidence_requirements':['Dimensions require actual source calibration, defined landmarks/planes and recorded phase/edge convention.',
            'Normality, true growth and clinical thresholds require valid reference context and comparable sources, not default text or a generic model.',
            'Valve function and operative suitability cannot be inferred from static contours or instructional figures.'],
        'clinical_validation_status':'draft_requires_cardiovascular_radiologist_and_aortic_team_review'}

if __name__=='__main__':
    item=build();path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    data['investigations']=[i for i in data['investigations'] if i['investigation_id']!=IDENT]+[item]
    data['scope']['catalog_investigation_ids']=[i['investigation_id'] for i in data['investigations']]
    path.write_text(json.dumps(data,indent=2)+'\n')
    print(len(item['structures']),'groups;',len(requirements_for(item)),'leaves;',len(requirements_for(item))*3,'representation obligations')
