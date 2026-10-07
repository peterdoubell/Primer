#!/usr/bin/env python3
"""Expand all reported temporal structures without borrowing neural/function detail from bone CT."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for
from tools.anatomy_sources.update_temporal_bone_reporting import URLS
ROOT = Path(__file__).resolve().parents[2]
IDENT = 'ra.ct-temporal-bone'


def build():
    ref = detail(Curriculum(),resolve(IDENT))['radiology_reference']; guide = ref['reporting']; structures = []
    def add(key,parts,reports,steps,side,modes=None,pathology=False):
        structures.append({'id':'temporal_bone.'+side+'_'+key,'name':side.capitalize()+' '+key.replace('_',' '),
            'tissue_class':'temporal_bone_compartment_tissue_boundary_route_or_device',
            'required_parts':[{'id':'temporal_bone.'+side+'_'+key+'.'+p,'name':p.replace('_',' ').capitalize()} for p in parts.split()],
            'laterality':side,'modality_scope':modes or ['CT','MRI'],
            'condition':'Instantiate every actual covered component, side, cell, variant, lesion, fracture, repair, device and connection. Use actual source-resolved anatomy, calibrated acquired planes and sampling/artifact limits. A named parent or schematic is not complete tiny wall/joint/nerve geometry; microscopic or unassessed boundaries remain missing.',
            'requirement_basis':'effective_temporal_bone_CT_and_actual_complementary_MRI_reporting_scope',
            'report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in reports],
            'walkthrough_step_indices':steps,'source_urls':URLS,'requires_site_instantiation':True,
            'context_requirements':{'purpose':'pathology_example' if pathology else 'anatomical_reference'}})
    bone = 'full_actual_component_and_obtained_extent every_resolved_cortex_or_articular_boundary adjacent_ossicle_canal_membrane_or_tissue_relation every_actual_attachment_variant_or_defect named_local_plane_measurement_and_calibration_if_supported partial_volume_artifact_and_unassessed_extent'
    compartment = 'every_actual_component_and_obtained_extent each_source_resolved_wall_and_content each_source_connection_and_endpoint adjacent_ossicular_neural_vascular_or_skull_base_interface source_lesion_variant_or_repair_if_present unresolved_or_uncovered_extent'
    soft = 'full_actual_obtained_tissue_extent every_source_resolved_boundary source_acquired_signal_contrast_or_diffusion_if_present adjacent_bone_compartment_or_device_interface each_actual_variant_or_lesion source_resolution_microscopic_and_unassessed_extent'
    route = 'actual_origin_and_full_obtained_course each_source_resolved_branch_and_boundary every_connection_and_endpoint_if_resolved adjacent_ear_bone_nerve_vessel_or_device_relation actual_variant_defect_or_lesion_and_evaluability unresolved_or_uncovered_extent'
    lesion = 'each_actual_site_component_and_full_obtained_extent source_resolved_margin_content_and_adjacent_boundary each_actual_connection_fracture_or_extension_route actual_acquired_sequence_phase_planes_and_measurement source_comparison_history_and_differential unassessed_tissue_function_or_uncovered_extent'
    device = 'each_actual_device_component_and_supplied_type source_entry_point_full_obtained_course_and_tip every_source_contact_with_ossicle_window_cochlea_or_other_tissue source_resolved_position_insertion_or_unresolved_scala actual_repair_cavity_graft_and_adjacent_neurovascular_relation artifact_calibration_and_unassessed_extent'
    for side in ['right','left']:
        for key in ['external_auditory_canal_cartilaginous_region','external_auditory_canal_bony_region','external_canal_anterior_posterior_superior_inferior_walls','tympanic_membrane_pars_flaccida','tympanic_membrane_pars_tensa','tympanic_membrane_annulus_umbo_and_malleal_attachment']:
            add(key,compartment,[0,4],[0,4],side)
        for key in ['epitympanum_attic','mesotympanum','hypotympanum','protympanum_and_tubal_opening','Prussak_space','facial_recess','sinus_tympani','supratubal_recess','anterior_epitympanic_recess','middle_ear_medial_lateral_roof_floor_and_anterior_posterior_interfaces']:
            add(key,compartment,[0,1,3,4],[0,1,3,4],side)
        for key in ['scutum','malleus_head','malleus_neck','malleus_manubrium','malleus_anterior_process','malleus_lateral_process','incus_body','incus_short_process','incus_long_process','incus_lenticular_process','incudomalleolar_articulation','incudostapedial_articulation','stapes_head','stapes_anterior_crus','stapes_posterior_crus','stapes_footplate']:
            add(key,bone,[0,4],[0,4],side,['CT'])
        for key in ['tensor_tympani_muscle_and_tendon','stapedius_muscle_and_tendon','ossicular_suspensory_ligament_or_other_reported_attachment','oval_window_membranous_interface','round_window_membrane']:
            add(key,soft,[0,2,4],[0,2,4],side)
        for key in ['aditus_ad_antrum','mastoid_antrum','every_actual_mastoid_cell_or_cell_group','mastoid_septa','mastoid_outer_cortex','mastoid_inner_cortex','tegmen_tympani','tegmen_mastoideum','petrous_apex_cells_and_actual_pneumatization','mastoid_tip_and_digastric_region']:
            add(key,compartment,[1,3,4],[1,3,4],side,['CT'])
        for key in ['otic_capsule','cochlear_basal_turn','cochlear_middle_turn','cochlear_apical_turn','cochlear_modiolus','osseous_spiral_lamina_and_interscalar_septa_if_resolved','cochlear_aperture_bony_boundary','vestibule_bony_boundary','superior_semicircular_canal','posterior_semicircular_canal','lateral_semicircular_canal','common_crus','each_actual_ampullary_bony_region','oval_window_bony_niche','round_window_bony_niche','vestibular_aqueduct_bony_course_and_opening','cochlear_aqueduct_bony_course_and_opening','fissula_ante_fenestram','cochlear_cleft_if_present','petromastoid_canal_if_present','pyramidal_eminence_and_cochleariform_process']:
            add(key,bone,[0,2,3,4],[0,2,3,4],side,['CT'])
        for key in ['source_resolved_scala_tympani_if_reported','source_resolved_scala_vestibuli_if_reported','membranous_cochlear_or_vestibular_region_if_reported','membranous_semicircular_and_ampullary_regions_if_reported','endolymphatic_duct_and_sac_if_reported','inner_ear_fluid_or_fibrous_tissue_component','each_actual_additional_inner_ear_subdivision']:
            add(key,soft,[2,4],[2,4],side,['MRI'])
        for key in ['facial_canal_labyrinthine_segment','geniculate_region_and_first_genu','facial_canal_tympanic_segment','facial_canal_second_genu','facial_canal_mastoid_segment','stylomastoid_foramen','greater_petrosal_canal_and_hiatus_if_covered','chorda_tympani_canal_route_if_reported','internal_auditory_canal_fundus_and_partitions','internal_auditory_canal_porus_and_full_covered_bony_course','carotid_canal_and_middle_ear_boundary','jugular_bulb_fossa_and_bony_plate','sigmoid_sinus_plate_and_bony_boundary','each_additional_actual_accessory_canal_or_foramen']:
            add(key,route,[2,3,4],[2,3,4],side,['CT'])
        for key in ['covered_facial_nerve_and_actual_branches','cochlear_nerve','superior_vestibular_nerve','inferior_vestibular_nerve','covered_cerebellopontine_angle_neural_interfaces']:
            add(key,route,[2,3,4],[2,3,4],side,['MRI'])
        for key in ['covered_internal_carotid_vessel','jugular_bulb_and_covered_venous_course','covered_sigmoid_sinus','actual_aberrant_or_dehiscent_neurovascular_connection','covered_dural_and_intracranial_interface']:
            add(key,route,[1,3,4],[1,3,4],side)
        for key in ['cholesteatoma_or_other_actual_soft_tissue_component','each_actual_ossicular_erosion_or_disruption','each_actual_otic_capsule_or_window_lesion','each_actual_canal_tegmen_or_cortical_defect','each_actual_fracture_course_and_interface','each_actual_infectious_collection_or_extraosseous_extension','each_actual_tumour_or_other_focal_mass','each_actual_congenital_or_additional_variant','each_actual_intracranial_herniation_or_communication','postoperative_fat_cartilage_or_other_graft_and_mimic','external_canal_cerumen_or_other_DWI_mimic']:
            add(key,lesion,[0,1,2,3,4],[0,1,2,3,4],side,pathology=True)
        for key in ['cochlear_implant_electrode_array_and_each_actual_contact','cochlear_implant_entry_tip_and_each_actual_extracochlear_component','ossicular_or_stapes_prosthesis','tympanostomy_tube_or_other_actual_device','mastoidectomy_or_other_source_surgical_cavity_and_repair']:
            add(key,device,[0,1,2,3,4],[0,1,2,3,4],side,['CT'])
    return {'investigation_id':IDENT,'module_id':ref['investigation']['module_id'],'title':'Temporal-bone CT and actually acquired complementary MRI anatomy',
        'scope_status':'expanded_draft_requires_independent_temporal_bone_anatomical_review','modality_scope':['CT','MRI'],
        'sources':[{'title':title,'url':url,'reviewed_at':'2026-10-07','review_status':'effective_anatomical_scope_source_reviewed'} for title,url in zip(['RA temporal anatomy1','RA temporal anatomy2','RA temporal pathology','ESHNR cholesteatoma source review'],URLS)],
        'source_contract_sha256':digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')}),
        'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':structures,
        'expansion_rules':['Instantiate every actual component, cell, variant, branch, lesion and device contact; named standard regions are a known floor, not a fixed patient count.',
            'Tiny bone/joint/canal anatomy requires resolving acquired CT; neural/membranous/fluid tissue requires its own appropriate acquired source and may remain unresolved even with MRI.',
            'A generic enlarged ear orientation model or source still does not establish full native tissue walls, scala identity, device trajectory, all branch extents or physiological function.'],
        'source_scope_issues':['Seven published CT/MRI comparison figures are selected local source examples and different patients; they cannot supply full native registered geometry.',
            'Healthy source reference panels cannot be pathological lesion evidence; graft/cerumen DWI mimics remain distinct cases and actual chronology.',
            'Published ADC ROI overlays and fusion are source display artifacts; independently calibrated values or newly registered native series are not provided.',
            'Device scala, contact count, tip/insertion and canal/tegmen integrity remain source-dependent; artifact or partial volume cannot become confirmed absence or a generic complete model.'],
        'functional_evidence_requirements':['Hearing, vestibular/neural function, ossicular sound transfer, pressure/flow and device performance require actual clinical/functional evidence, not static geometry.',
            'Tissue identity, infection and cholesteatoma diagnosis require appropriate actual clinical/otoscopic, MRI and supplied tissue context; nonspecific CT opacification or DWI brightness is not unique histology.',
            'ADC/contrast/defect or aqueduct measurements require the actual acquisition, site, plane, edge convention, calibration and uncertainty; source captions cannot provide a new patient measurement.'],
        'clinical_validation_status':'draft_requires_temporal_bone_radiologist_and_otologic_review'}


if __name__=='__main__':
    item=build();path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    data['investigations']=[i for i in data['investigations'] if i['investigation_id']!=IDENT]+[item]
    data['scope']['catalog_investigation_ids']=[i['investigation_id'] for i in data['investigations']]
    path.write_text(json.dumps(data,indent=2)+'\n');n=len(requirements_for(item));print(len(item['structures']),'groups;',n,'parts;',n*3,'representation obligations')
