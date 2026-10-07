#!/usr/bin/env python3
"""Enumerate map-specific nodal groups, actual nodes and every reported adjacent interface."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for
from tools.anatomy_sources.update_cervical_node_reporting import URLS
ROOT=Path(__file__).resolve().parents[2];IDENT='ra.cervical-lymph-nodes';MODES=['CT','MRI','Ultrasound']
def build():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];guide=ref['reporting'];structures=[]
    def add(key,parts,reports,steps,side='not_applicable',pathology=False,map_scope=None):
        structures.append({'id':'cervical_nodes.'+side+'_'+key,'name':side.replace('_',' ').capitalize()+' '+key.replace('_',' '),'tissue_class':'nodal_compartment_component_boundary_or_adjacent_interface',
            'required_parts':[{'id':'cervical_nodes.'+side+'_'+key+'.'+p,'name':p.replace('_',' ').capitalize()} for p in parts.split()],
            'laterality':side,'modality_scope':MODES,'condition':'Instantiate every actual covered node, group, component, side, variant, primary/repair and connection, using the explicitly named map/version and descriptive boundaries. A parent group or enlarged-node model is not every node or native tiny cortex/hilum/capsule. A permitted modality cannot supply unresolved, microscopic or unacquired anatomy; US only supplies actually surveyed accessible coverage.',
            'requirement_basis':'effective_cervical_nodal_CT_MRI_US_reporting_scope','map_scope':map_scope or 'Actual named map/version and descriptive source location; no automatic cross-map equivalence',
            'report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in reports],'walkthrough_step_indices':steps,'source_urls':URLS,
            'requires_site_instantiation':True,'context_requirements':{'purpose':'pathology_example' if pathology else 'anatomical_reference'}})
    region='every_actual_node_and_full_obtained_group_extent source_superior_inferior_anterior_posterior_medial_lateral_boundaries actual_named_map_version_and_descriptive_landmarks every_source_subgroup_variant_or_unassigned_region adjacent_gland_muscle_vessel_airway_or_skull_base_relation modality_specific_coverage_and_unresolved_extent'
    node='every_actual_named_node_identity_and_obtained_extent source_resolved_cortex source_resolved_hilum source_resolved_margin_capsular_interface every_resolved_internal_solid_fluid_necrotic_appearing_or_calcium_component each_source_perinodal_tissue_interface source_local_axis_measurement_and_acquisition_limits microscopic_or_uncovered_extent'
    adjacent='every_actual_named_component_and_obtained_extent each_source_resolved_boundary nodal_contact_or_extension_relation every_actual_variant_lesion_or_repair source_acquisition_phase_sequence_and_evaluability unresolved_microscopic_or_uncovered_extent'
    route='actual_origin_and_full_obtained_course every_source_resolved_branch_boundary_and_endpoint each_nodal_or_primary_tissue_connection actual_source_contact_displacement_encasement_or_mimic actual_phase_sequence_and_comparison_if_acquired unresolved_wall_flow_or_uncovered_extent'
    lesion='every_actual_node_component_and_full_obtained_extent each_source_resolved_internal_margin_and_content adjacent_node_fat_muscle_skin_gland_or_vessel_interface each_actual_connection_or_supported_extension source_phase_sequence_dimensions_and_comparison differential_microscopic_and_unassessed_extent'
    # Level Ia is a midline region, not two invented bilateral compartments.
    add('submental_Ia_midline',region,[0,1,2,3],[0,1,2,3])
    for side in ['left','right']:
        for key in ['submandibular_Ib','upper_jugular_IIa','upper_jugular_IIb','mid_jugular_III','lower_jugular_surgical_IV','posterior_triangle_surgical_Va','posterior_triangle_surgical_Vb','central_surgical_VI','covered_superior_mediastinal_surgical_VII_if_named']:
            add(key,region,[0,1,2,3],[0,1,2,3],side,map_scope='Actual surgical map/version with original descriptive source boundaries')
        for key in ['lower_jugular_extended_IVa','medial_supraclavicular_extended_IVb','posterior_triangle_extended_Va','posterior_triangle_extended_Vb','lateral_supraclavicular_extended_Vc','superficial_anterior_jugular_extended_VIa','deep_central_extended_VIb','retropharyngeal_extended_VIIa','retrostyloid_extended_VIIb','parotid_extended_VIII','buccofacial_extended_IX','retroauricular_extended_Xa','occipital_extended_Xb']:
            add(key,region,[0,1,2,3],[0,1,2,3],side,map_scope='Actual extended radiotherapy map/version; label is not automatically the surgical level with the same numeral')
        for key in ['each_actual_pre_laryngeal_node','each_actual_pretracheal_node','each_actual_paratracheal_node','each_actual_recurrent_laryngeal_chain_node','each_actual_perifacial_or_other_salivary_chain_node','each_actual_superficial_or_deep_node_not_assigned_to_standard_group']:
            add(key,node,[0,1,2,3,4],[0,1,2,3,4],side)
        for key in ['every_actual_index_node','every_actual_nonindex_covered_node','each_actual_conglomerate_component','each_actual_cystic_or_necrotic_appearing_component','each_actual_calcific_or_solid_component','each_actual_post_treatment_or_surgical_node_or_mimic','each_actual_imaging_ENE_tissue_interface']:
            add(key,lesion,[0,1,2,3,4],[0,1,2,3,4],side,pathology=True)
        for key in ['sternocleidomastoid_boundary_and_source_involvement','digastric_anterior_and_posterior_bellies','submandibular_gland_and_interfaces','parotid_gland_superficial_deep_and_periglandular_interfaces','mylohyoid_and_floor_of_mouth_interfaces','strap_muscle_and_previsceral_interfaces','prevertebral_scalene_or_other_actual_muscle_interfaces','skin_subcutaneous_and_superficial_fascial_interfaces','each_actual_deep_neck_space_or_fascial_interface','skull_base_and_styloid_region_boundaries','hyoid_laryngeal_cricoid_source_landmark_interfaces','clavicular_sternoclavicular_and_lower_neck_interfaces','thyroid_and_parathyroid_region_interfaces','each_actual_additional_group_boundary_or_variant']:
            add(key,adjacent,[0,2,3,4],[0,2,3,4],side)
        for key in ['common_internal_external_carotid_sources','each_actual_relevant_arterial_branch','internal_jugular_venous_course_and_connections','external_anterior_jugular_and_other_actual_venous_routes','subclavian_transverse_cervical_or_other_lower_neck_vascular_interfaces','covered_relevant_neural_route_and_source_contact']:
            add(key,route,[0,3,4],[0,3,4],side)
        for key in ['covered_oral_cavity_floor_tongue_and_mucosal_interfaces','covered_tonsillar_tongue_base_and_oropharyngeal_interfaces','covered_nasopharyngeal_and_retropharyngeal_interfaces','covered_hypopharyngeal_and_laryngeal_interfaces','covered_thyroid_salivary_or_other_actual_primary_site','covered_airway_and_periairway_interfaces','each_actual_primary_node_or_other_extension_connection','each_actual_deep_infected_collection_or_other_non_nodal_mimic']:
            add(key,adjacent,[0,2,3,4],[0,2,3,4],side)
    for key in ['midline_actual_pre_laryngeal_pretracheal_or_other_node','manubrial_lower_neck_and_covered_mediastinal_boundary','each_actual_cross_midline_or_unassigned_group_or_connection']:
        add(key,region+' every_actual_side_or_midline_assignment',[0,1,2,3,4],[0,1,2,3,4])
    return {'investigation_id':IDENT,'module_id':ref['investigation']['module_id'],'title':'Cervical nodal anatomy with named surgical/extended radiotherapy map and actual acquired sources',
        'scope_status':'expanded_draft_requires_independent_cervical_nodal_anatomical_review','modality_scope':MODES,
        'sources':[{'title':title,'url':url,'reviewed_at':'2026-10-07','review_status':'effective_map_or_source_morphology_reference_reviewed_no_graphics_reused'} for title,url in zip(['RA named cervical node map','ASHNR imaging ENE framework','HNCIG 2024 consensus','Source imaging ENE review'],URLS)],
        'source_contract_sha256':digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')}),'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':structures,
        'expansion_rules':['Every actual node/group/subgroup/component and boundary must be independently instantiated; index nodes and standard labels are a known floor, not complete native patient burden.',
            'Surgical VII and extended VIIa/VIIb are not equivalent; central/retropharyngeal/supraclavicular/parotid/buccofacial/occipital conventions require the actual named map and descriptive landmarks.',
            'CT/MRI/US sources remain separate; US cannot borrow deep unassessed skull-base/full-neck extent and static pictures cannot supply microscopic capsule, function or tissue identity.'],
        'source_scope_issues':['Restricted-source ENE figures remain reference-only; no noncommercial images or captions are promoted into commercial geometry/figure evidence.',
            'The generic neck/node companion and inherited source pictures do not establish all nodal levels, actual nodes, cortex/hilum/capsule or adjacent native tissue/vessel routes.',
            'Small size, cystic appearance, matting or vessel contact is not proof of benignity, unique metastasis/assay status, pathological ENE, patency or resectability.'],
        'functional_evidence_requirements':['Actual histology/biopsy/pathological ENE, HPV or other assays, primary/treatment and staging version are supplied clinical evidence, not structures to invent in 3D.',
            'Flow, vessel function/patency, airway function and clinical infection need actual corresponding sources, not contact geometry or a static capsule appearance.',
            'Node/conglomerate dimensions and interval change require actual identified source axes, planes, calibration, comparison and uncertainty; generic thresholds do not close missing morphology.'],
        'clinical_validation_status':'draft_requires_head_neck_radiologist_and_relevant_nodal_oncologic_review'}
if __name__=='__main__':
    item=build();path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text());data['investigations']=[i for i in data['investigations'] if i['investigation_id']!=IDENT]+[item];data['scope']['catalog_investigation_ids']=[i['investigation_id'] for i in data['investigations']];path.write_text(json.dumps(data,indent=2)+'\n');n=len(requirements_for(item));print(len(item['structures']),'groups;',n,'parts;',n*3,'representation obligations')
