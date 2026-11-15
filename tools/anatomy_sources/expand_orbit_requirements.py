#!/usr/bin/env python3
"""Enumerate complete reported ocular/orbital anatomy; source examples cannot replace every interface."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for
from tools.anatomy_sources.update_orbit_reporting import URLS
ROOT=Path(__file__).resolve().parents[2];IDENT='ra.ct-mri-eye'

def build():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];guide=ref['reporting'];structures=[]
    def add(key,parts,reports,steps,side,modes=None,pathology=False):
        structures.append({'id':'orbit.'+side+'_'+key,'name':side.capitalize()+' '+key.replace('_',' '),'tissue_class':'ocular_orbital_tissue_compartment_route_or_interface',
            'required_parts':[{'id':'orbit.'+side+'_'+key+'.'+p,'name':p.replace('_',' ').capitalize()} for p in parts.split()],
            'laterality':side,'modality_scope':modes or ['CT','MRI'],'condition':'Instantiate every actual covered layer, side, muscle/tendon/insertion, branch, compartment, variant, lesion, device and connection. Use genuinely resolving acquired source planes, sequence/phase and calibration; an allowed modality does not automatically resolve every boundary. Microscopic, overlapped or unassessed anatomy remains missing, not inferred normal.',
            'requirement_basis':'effective_ocular_orbital_CT_MRI_reporting_scope','report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in reports],
            'walkthrough_step_indices':steps,'source_urls':URLS,'requires_site_instantiation':True,'context_requirements':{'purpose':'pathology_example' if pathology else 'anatomical_reference'}})
    tissue='full_actual_component_and_obtained_extent every_source_resolved_layer_or_tissue_boundary adjacent_globe_compartment_muscle_nerve_or_wall_relation source_signal_enhancement_diffusion_or_material_if_acquired every_actual_variant_lesion_or_repair sampling_artifact_microscopic_and_unassessed_extent'
    compartment='every_actual_subcompartment_and_full_obtained_extent source_resolved_boundary_and_content each_actual_connection_or_extension_route adjacent_globe_muscle_nerve_vessel_or_skull_base_interface every_source_lesion_variant_or_collection unresolved_or_uncovered_extent'
    muscle='full_actual_belly_tendon_or_insertion_extent every_source_resolved_boundary_and_attachment adjacent_globe_cone_nerve_wall_or_fracture_interface every_actual_variant_lesion_or_repair actual_acquired_sequence_planes_and_calibration unresolved_tissue_or_function_and_uncovered_extent'
    route='actual_origin_and_full_obtained_course each_source_resolved_branch_and_boundary every_connection_and_endpoint_if_resolved adjacent_globe_muscle_canal_vessel_or_device_interface actual_variant_contact_encasement_or_defect unresolved_microscopic_or_uncovered_extent'
    bone='full_actual_landmark_wall_or_canal_extent source_resolved_cortical_boundary_and_thin_bone_limit every_actual_defect_fracture_or_variant adjacent_orbital_sinus_nerve_vessel_or_device_interface appropriate_local_planes_and_source_calibrated_measurement partial_volume_artifact_and_unassessed_extent'
    lesion='every_actual_named_site_component_and_obtained_extent each_source_resolved_margin_layer_and_internal_component adjacent_globe_cone_nerve_vessel_bone_or_other_interface every_actual_connection_extension_or_comparison source_acquired_phase_diffusion_and_measurement_method differential_microscopic_and_unassessed_extent'
    for side in ['left','right']:
        for key in ['globe_contour_and_each_actual_wall_region','corneal_anterior_segment_if_resolved','anterior_chamber_if_reported','posterior_chamber_if_reported','iris_and_ciliary_region_if_resolved','lens_and_capsular_interface','zonular_or_other_lens_attachment_if_reported','vitreous_and_each_source_intraocular_component','retina_and_source_detachment_interfaces','choroid_and_source_detachment_interfaces','sclera_and_extrascleral_interface','optic_disc_and_globe_nerve_junction','each_actual_additional_ocular_layer_or_variant','eyelid_and_preseptal_tissue','orbital_septum_if_resolved','conjunctival_or_other_surface_region_if_reported']:
            add(key,tissue,[0,1,2],[0,1,2],side)
        for key in ['extraconal_compartment','intraconal_compartment','muscle_cone_and_intermuscular_interfaces','subperiosteal_compartment','orbital_fat_and_each_actual_subregion','each_cross_compartment_or_additional_route']:
            add(key,compartment,[0,2,3,4],[1,2,3,4],side)
        for name in ['superior_rectus','inferior_rectus','medial_rectus','lateral_rectus','superior_oblique','inferior_oblique','levator_palpebrae']:
            for component in ['belly','tendon','insertion_or_attachment']:
                add(name+'_'+component,muscle,[0,2,4],[1,2,4],side)
        for key in ['superior_oblique_trochlear_relation','annulus_and_source_apical_musculotendinous_attachment_if_resolved','optic_nerve_intraocular_junction','optic_nerve_intraorbital_segment','optic_nerve_intracanalicular_segment','optic_nerve_covered_intracranial_segment','optic_nerve_sheath_and_perineural_interfaces','covered_optic_chiasm','covered_optic_tract_or_other_visual_pathway','each_actual_covered_orbital_motor_or_sensory_nerve_route']:
            add(key,route,[0,2,3],[1,2,3],side,['MRI'])
        for key in ['lacrimal_gland_orbital_lobe','lacrimal_gland_palpebral_lobe','lacrimal_sac_and_actual_drainage_interfaces','nasolacrimal_duct_and_source_connections','orbital_apex_and_each_actual_compartment','cavernous_sinus_and_covered_parasellar_interfaces','pterygopalatine_infratemporal_or_other_actual_fossa_extension','covered_dura_brain_and_intracranial_routes']:
            add(key,compartment,[0,2,3,4],[1,2,3,4],side)
        for key in ['orbital_floor','orbital_roof','orbital_medial_wall','orbital_lateral_wall','orbital_rim_and_each_actual_bone_interface','optic_canal_bony_boundaries','superior_orbital_fissure_bony_boundaries','inferior_orbital_fissure_bony_boundaries','nasolacrimal_canal_bony_boundaries','each_actual_additional_foramen_or_variant','adjacent_ethmoid_sinus_bony_interface','adjacent_maxillary_sinus_bony_interface','adjacent_frontal_sinus_bony_interface','adjacent_sphenoid_sinus_bony_interface']:
            add(key,bone,[3,4],[3,4],side,['CT'])
        for key in ['covered_ophthalmic_arterial_origin_and_course','every_relevant_source_resolved_orbital_arterial_branch','superior_ophthalmic_vein_and_connections','inferior_ophthalmic_vein_and_connections','each_actual_orbital_venous_or_variceal_route','covered_cavernous_carotid_interface','each_actual_arteriovenous_or_other_vascular_connection']:
            add(key,route,[0,2,3],[1,2,3],side)
        for key in ['each_actual_intraocular_mass_or_other_component','each_actual_orbital_mass_or_infiltrative_component','each_actual_orbital_collection_abscess_or_mimic','each_actual_intraocular_or_orbital_haemorrhagic_component','each_actual_foreign_material_component_and_interface','each_actual_fracture_defect_or_herniated_component','each_actual_muscle_nerve_sheath_or_vascular_lesion','each_actual_congenital_or_additional_variant','each_actual_postoperative_graft_device_or_repair','each_actual_perineural_intracranial_or_other_extension']:
            add(key,lesion,[0,1,2,3,4],[0,1,2,3,4],side,pathology=True)
        add('each_actual_adjacent_sinus_inflammatory_tissue_and_source_connection',compartment,[0,3,4],[1,3,4],side,pathology=True)
    return {'investigation_id':IDENT,'module_id':ref['investigation']['module_id'],'title':'CT/MRI eye and orbit, source-dependent complete reported anatomy',
        'scope_status':'expanded_draft_requires_independent_orbital_anatomical_review','modality_scope':['CT','MRI'],
        'sources':[{'title':title,'url':url,'reviewed_at':'2026-10-07','review_status':'effective_reported_anatomical_scope_source_reviewed'} for title,url in zip(['RA eye/orbit CT MRI','Paediatric orbital lesion scope','Original orbital MRI source review'],URLS)],
        'source_contract_sha256':digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')}),'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':structures,
        'expansion_rules':['Every actual layer, muscle/tendon/insertion, branch, lesion, variant and connection must be independently instantiated; standard labels do not close the patient-specific scope.',
            'CT bone and foreign-material sources cannot borrow unperformed MRI neural/layer/contrast/ADC information, and MRI cannot supply unresolved thin-wall integrity.',
            'Every clinical image, schematic and model must match the required actual source state, extent, population, side and modality; a conceptual compartment diagram is not native complete geometry.'],
        'source_scope_issues':['The current sixteen MRI case figures and one schematic are selected source examples, not full acquisitions or validated all-structure coverage.',
            'Source paediatric/adult ages, unreported sequence/phase roles and caption-plane disagreements remain distinct; source histology/dimensions are not new patient evidence.',
            'Foreign-body material and MRI safety require actual clinical source assessment; a model or teaching picture cannot clear a patient.',
            'Tendon sparing, sheath appearance, enhancement or DWI brightness can overlap across diagnoses; no unique histology or physiological function is provided by morphology alone.'],
        'functional_evidence_requirements':['Vision, motility, pressure, clinical entrapment, perfusion/flow and symptoms require actual clinical/functional sources, not static coordinates.',
            'ADC, enhancement kinetics, vascular filling/patency or proptosis require their actual acquisition, reference plane, calibration and uncertainty; no borrowed values.',
            'Infectious causality, unique tissue identity and molecular diagnosis require corresponding supplied clinical/tissue evidence; adjacent sinus change alone does not prove origin.'],
        'clinical_validation_status':'draft_requires_orbital_radiologist_and_ophthalmic_review'}
if __name__=='__main__':
    item=build();path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text());data['investigations']=[i for i in data['investigations'] if i['investigation_id']!=IDENT]+[item];data['scope']['catalog_investigation_ids']=[i['investigation_id'] for i in data['investigations']];path.write_text(json.dumps(data,indent=2)+'\n');n=len(requirements_for(item));print(len(item['structures']),'groups;',n,'parts;',n*3,'representation obligations')
