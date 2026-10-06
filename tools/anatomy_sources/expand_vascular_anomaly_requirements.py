#!/usr/bin/env python3
"""Expand actual arch, airway, pulmonary and systemic vascular anomaly requirements."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for
ROOT=Path(__file__).resolve().parents[2]
IDENT='ra.vascular-anomalies'
URLS=['https://radiologyassistant.nl/cardiovascular/thoracic-aorta/vascular-anomalies-of-aorta-pulmonary-and-systemic-vessels','https://pmc.ncbi.nlm.nih.gov/articles/PMC4141344/','https://pmc.ncbi.nlm.nih.gov/articles/PMC9705143/','https://pmc.ncbi.nlm.nih.gov/articles/PMC7561662/','https://pmc.ncbi.nlm.nih.gov/articles/PMC3038141/','https://pmc.ncbi.nlm.nih.gov/articles/PMC8052389/']
def build():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];guide=ref['reporting'];structures=[]
    def add(key,name,children,steps,side='not_applicable',purpose='anatomical_reference'):
        structures.append({'id':'vascular_anomaly.'+key,'name':name,'tissue_class':'vascular_anomaly_structure_or_control',
            'required_parts':[{'id':'vascular_anomaly.'+key+'.'+p,'name':p.replace('_',' ').capitalize()} for p in children.split()],
            'laterality':side,'modality_scope':['CT','MRI','Ultrasound'],
            'condition':'Instantiate every actual patent, interrupted, accessory, common, atretic, repaired or anomalous channel and its connections. Preserve original laterality, modality, patient, phase, source calibration, coverage and uncertainty. An inferred non-opacified structure is not directly seen.',
            'requirement_basis':'effective_vascular_anomaly_reporting_scope','report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in steps],
            'walkthrough_step_indices':steps,'source_urls':URLS,'requires_site_instantiation':True,'context_requirements':{'purpose':purpose}})
    vessel='actual_origin proximal_course complete_covered_course distal_endpoint lumen_and_wall_if_resolved minimum_orthogonal_axes_and_site local_axis_or_centreline adjacent_airway_oesophagus_or_vessel_relation patency_opacification_and_artefact uncovered_or_unresolved_extent'
    for key,name in [('ascending','Ascending aorta'),('arch','Actual arch'),('isthmus','Aortic isthmus'),('descending','Covered descending aorta')]:add(key,name,vessel+' actual_side_and_branch_order',[0,1])
    for key,name,side in [('right_brachiocephalic','Right brachiocephalic trunk if present','right'),('left_brachiocephalic','Left brachiocephalic trunk if present','left'),('right_carotid','Right common carotid','right'),('left_carotid','Left common carotid','left'),('right_subclavian','Right subclavian','right'),('left_subclavian','Left subclavian','left'),('right_vertebral','Right vertebral origin if relevant','right'),('left_vertebral','Left vertebral origin if relevant','left')]:add(key,name,vessel,[0],side)
    for key,name,side in [('right_arch_component','Right component in double arch','right'),('left_arch_component','Left component in double arch','left')]:add(key,name,vessel+' dominance_relative_calibre junction_with_other_arch atretic_extent_and_inference_basis',[0,1],side)
    add('arch_variant','Each actual arch/branch configuration','arch_side_and_level descending_aortic_side branch_number_and_order each_common_origin_or_separate_branch aberrant_subclavian_full_course mirror_image_configuration circumflex_or_cervical_course complete_potential_ring_component_map patent_vs_atretic_or_inferred_components source_resolved_vs_unresolved_relations',[0,1])
    add('diverticulum','Each actual Kommerell/ductal diverticulum','actual_origin_and_branch attachment_and_neck source_resolved_wall_and_lumen orthogonal_dimensions_and_named_axes relationship_to_opposite_wall_if_measured thrombus_or_calcification_if_present airway_oesophageal_relation differentiation_from_other_bulge source_calibration_and_unresolved_boundary',[0,1])
    add('coarctation','Each coarctation/hypoplastic or interrupted region','proximal_distal_landmarks relation_to_branch_and_ductus minimum_orthogonal_lumen lesion_length adjacent_reference_diameters wall_morphology hypoplastic_arch_extent discontinuity_vs_non_opacification collateral_origins_and_routes actual_gradient_or_functional_source uncovered_or_unresolved_extent',[0],purpose='pathology_example')
    for side in ['right','left']:
        add(side+'_collaterals',side.capitalize()+' systemic arterial collateral pathways','each_actual_origin internal_thoracic_route intercostal_route bronchial_route other_actual_route pulmonary_or_systemic_endpoint vessel_calibre_and_aneurysm_if_present uncovered_or_unresolved_extent',[0,2],side)
        add(side+'_ductal_component',side.capitalize()+' ductal/ligamentous component','aortic_attachment pulmonary_attachment full_patent_course actual_side relative_airway_oesophageal_course calcified_or_non_opacified_extent source_visualisation_or_inference_basis ring_completion_relation patency_and_flow_evidence unavailable_attachment_or_function',[0,1,2],side)
    add('ring_map','Every actual vascular-ring component','each_arterial_component each_ductal_or_ligamentous_component anterior_posterior_lateral_relations complete_connection_topology patent_vs_atretic_components directly_seen_vs_inferred_segments airway_enclosure oesophageal_enclosure exact_uncertainty_and_unresolved_component',[0,1])
    airway='proximal_distal_extent source_resolved_lumen_and_wall minimum_orthogonal_axes compression_level_and_length adjacent_vessel_relation respiratory_phase cartilage_or_posterior_membrane_if_resolved dynamic_source_and_limits uncovered_or_unresolved_extent'
    for key,name in [('trachea','Covered trachea'),('carina','Actual carina and branching level')]:add(key,name,airway,[1,2])
    for side in ['right','left']:
        add(side+'_main_bronchus',side.capitalize()+' main bronchus',airway+' actual_origin_and_branching',[1,2],side)
        add(side+'_lobar_bronchi',side.capitalize()+' actual lobar/segmental bronchial branches','each_actual_origin each_covered_course actual_supplied_lobe_or_segment compression_or_stenosis aberrant_or_bridging_connection source_resolved_vs_unresolved_cartilage uncovered_extent',[1,2],side)
        add(side+'_lung',side.capitalize()+' lung and hilar development','actual_lobes_and_covered_parenchyma volume_and_hypoplasia actual_bronchus_and_distal_arterial_tree compensatory_overinflation_or_herniation mediastinal_shift systemic_collateral_supply actual_venous_drainage source_coverage_and_developmental_uncertainty',[2,3],side)
    add('airway_variant','Each actual airway variant','tracheal_bronchus_origin bridging_bronchus_course bronchus_intermedius_if_present actual_lobar_supply carina_level_and_configuration complete_cartilage_ring_if_resolved associated_long_segment_stenosis dynamic_malacia_evidence_and_limits',[1,2])
    add('oesophagus','Covered oesophagus','covered_wall_and_lumen level_and_side_of_impression proximal_distal_extent adjacent_vascular_component anterior_posterior_relation source_distension_and_coverage functional_swallowing_source_if_performed unresolved_or_uncovered_extent',[1])
    add('main_pulmonary_artery','Main pulmonary artery',vessel+' actual_branching_and_ductal_attachment',[2])
    for side in ['right','left']:
        add(side+'_pulmonary_artery',side.capitalize()+' proximal pulmonary artery',vessel+' sling_course_if_present interruption_vs_hypoplasia_vs_non_opacification',[1,2],side)
        add(side+'_distal_pulmonary_arteries',side.capitalize()+' distal pulmonary arterial branches','each_actual_lobar_segmental_origin each_covered_course distal_patency actual_systemic_collateral_connection associated_lung_and_bronchus source_opacification_and_uncovered_extent',[2],side)
        for lobe in (['upper','middle','lower'] if side=='right' else ['upper','lingular','lower']):
            add(side+'_'+lobe+'_pulmonary_veins',side.capitalize()+' '+lobe+' actual venous channels','each_actual_segmental_channel source_lobar_identity hilar_course every_common_trunk_or_accessory_channel every_dual_connection complete_covered_collector_route each_atrial_or_systemic_endpoint minimum_calibre_or_obstruction_if_present actual_crossing_vessel_airway_relation source_opacification_and_uncovered_extent',[3],side)
    for key,name in [('vertical_collector','Each vertical/anomalous venous collector'),('scimitar','Each scimitar-pattern channel'),('venous_confluence','Each pulmonary venous confluence/common trunk')]:add(key,name,vessel+' every_pulmonary_tributary every_systemic_or_atrial_connection obstruction_level_if_present collateral_or_dual_drainage',[3])
    for side in ['right','left']:
        add(side+'_svc',side.capitalize()+' superior vena cava',vessel+' every_tributary actual_coronary_sinus_or_atrial_endpoint',[3,4],side)
        add(side+'_brachiocephalic_vein',side.capitalize()+' brachiocephalic/bridging venous pathway',vessel+' bridging_presence_or_absence_and_basis anomalous_pulmonary_connection',[3,4],side)
    for side in ['right','left']:
        add(side+'_levoatriocardinal',side.capitalize()+' levoatriocardinal-type connection if present','actual_atrial_or_pulmonary_venous_origin complete_covered_course relation_to_pulmonary_artery actual_systemic_endpoint every_dual_or_collateral_connection obstructive_or_postoperative_context source_opacification dynamic_flow_source_if_available bidirectional_or_unresolved_function uncovered_extent',[3,4],side)
        add(side+'_pericardiophrenic',side.capitalize()+' pericardiophrenic collateral channel if present','actual_cranial_origin complete_covered_course lateral_cardiac_and_diaphragm_relation each_transdiaphragmatic_connection actual_hepatic_or_systemic_endpoint obstruction_or_portal_context source_opacification dynamic_flow_source_if_available differential_from_caval_or_pulmonary_channel uncovered_extent',[4],side)
        add(side+'_atrial_appendage',side.capitalize()+' actual atrial appendage if resolved','actual_sidedness source_resolved_morphology attachment_to_atrium relevant_isomerism_context source_phase_and_coverage unresolved_morphology',[3,4],side)
    add('venous_collaterals','Every actual systemic venous obstruction/collateral pathway','obstruction_site_and_extent actual_proximal_distal_connections every_mediastinal_or_chest_wall_channel azygos_hemiazygos_relation hepatic_or_portosystemic_relation each_channel_minimum_calibre_if_measured source_phase_and_opacification flow_source_if_available acquired_vs_congenital_context uncovered_extent',[4])
    add('coronary_sinus','Coronary sinus and atrial interface','source_resolved_course wall_and_lumen actual_systemic_venous_connections right_atrial_ostium roof_and_left_atrial_relation unroofed_or_other_septal_defect_if_resolved actual_drainage_endpoint uncertainty_and_functional_limits',[4])
    for key,name in [('hepatic_ivc','Hepatic IVC segment'),('suprarenal_ivc','Suprarenal IVC segment if covered'),('renal_ivc','Renal IVC segment if covered'),('infrarenal_ivc','Infrarenal IVC segment if covered')]:add(key,name,vessel+' continuity_or_interruption actual_tributaries_and_continuation',[4])
    for key,name in [('hepatic_veins','Each actual hepatic vein'),('azygos','Azygos and arch'),('hemiazygos','Hemiazygos/accessory hemiazygos pathway'),('left_superior_intercostal','Left superior intercostal vein')]:add(key,name,vessel+' each_actual_tributary continuation_and_systemic_endpoint distinction_from_anomalous_pulmonary_channel',[3,4])
    for key,name in [('left_atrium','Left atrium and venous ostia'),('right_atrium','Right atrium and systemic venous junctions'),('right_ventricle','Right ventricular size/covered morphology'),('atrial_septum','Covered atrial/sinus-venosus septal interfaces')]:add(key,name,'source_resolved_boundary each_actual_vascular_connection chamber_or_defect_dimensions_if_measured actual_septal_morphology phase_and_coverage actual_functional_source unresolved_or_uncovered_extent',[3,4])
    add('repair','Every actual prior repair or device','operative_history_and_date each_actual_graft_patch_stent_or_reimplantation native_to_repaired_interface proximal_distal_anastomoses branch_and_airway_relation restenosis_or_residual_compression pseudoaneurysm_or_leak_if_present device_artefact source_coverage_and_unresolved_extent',[0,1,2,3,4])
    add('acquisition','Actual acquisition and reconstruction controls','source_patient_and_series_identity actual_modality anatomical_coverage contrast_injection_and_opacification phase_or_cardiac_gating respiratory_phase voxel_units_and_calibration reconstruction_thickness_and_increment original_planes_and_coordinates derived_projection_vs_native_volume artefact_and_unavailable_source_regions',[0,1,2,3,4])
    add('functional_context','Actual clinical and haemodynamic interpretation','age_body_size_and_symptoms source_clinical_correspondence measured_gradient_source_if_available shunt_direction_and_quantification_source ventricular_function_source dynamic_airway_assessment_source swallowing_assessment_source comparison_dates_and_protocol operative_confirmation_if_available unresolved_clinical_significance',[0,1,2,3,4])
    return {'investigation_id':IDENT,'module_id':'rad.5.congenital-ct','title':'CT vascular anomalies',
        'scope_status':'expanded_draft_requires_independent_anatomical_and_clinical_review','modality_scope':['CT','MRI','Ultrasound'],
        'sources':[{'title':t,'url':u,'reviewed_at':'2026-10-06','review_status':s} for t,u,s in zip(['Radiology Assistant vascular anomalies','CT evaluation of rings/slings','Thoracic vascular variants','Persistent left SVC review','Anomalous pulmonary vein multimodality case','Published left-SVC review correction'],URLS,['effective_reporting_and_relevant_source_sections_reviewed','original_XML_body_and_ring_airway_tables_reviewed','original_XML_relevant_systemic_venous_and_pulmonary_sections_reviewed','original_XML_venous_differentials_and_selected_captions_reviewed','original_XML_complete_case_and_multimodality_figure_reviewed','original_XML_complete_reference_numbering_and_name_correction_reviewed'])],
        'source_contract_sha256':digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')}),
        'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':structures,
        'expansion_rules':['Instantiate every actual variant/channel/connection and conditional repair; this leaf inventory is a known floor, not an exhaustive congenital classification.',
            'Each leaf requires independently reviewed image, schematic and model evidence with actual modality/state/laterality; a generic arch or flat rendering cannot grant coverage.',
            'Conditional CT/MRI/ultrasound capabilities require source-resolved anatomy and do not imply every modality depicts every leaf.'],
        'source_scope_issues':['Atretic arch/ligamentous components may be inferred but must not be relabelled directly visible.',
            'Actual pulmonary venous number, common trunks, accessory and dual drainage require complete tracing.',
            'Left SVC drainage is not universally to the coronary sinus/right atrium.',
            'Static compression, morphology, chamber size and single-phase contrast density do not independently prove dynamic dysfunction, flow direction or shunt haemodynamics; published case Qp/Qs and treatment context are not universal recommendations.',
            'PMC9705143 is CC BY-NC-ND 4.0; no figures are commercially reused from that grant.',
            'Original ring/slings source is CC BY 4.0; all 11 complete original figures have reviewed grants/pixels and explicit schematic/rendered roles, but native geometry and complete independent anatomical review remain outstanding.'],
        'functional_evidence_requirements':['Clinical significance requires actual functional/source evidence; no universal severity or procedural recommendation is inferred from instructional geometry.',
            'Acquire adequate actual source coverage/opacification; non-visualisation is not absence and extra phases are not automatic.',
            'Report measurement calibration/planes, respiratory/cardiac phase and unresolved connections.'],
        'clinical_validation_status':'draft_requires_congenital_cardiovascular_radiologist_and_clinical_team_review'}
if __name__=='__main__':
    item=build();path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    data['investigations']=[i for i in data['investigations'] if i['investigation_id']!=IDENT]+[item]
    data['scope']['catalog_investigation_ids']=[i['investigation_id'] for i in data['investigations']]
    path.write_text(json.dumps(data,indent=2)+'\n')
    print(len(item['structures']),'groups;',len(requirements_for(item)),'leaves;',len(requirements_for(item))*3,'representation obligations')
