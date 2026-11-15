#!/usr/bin/env python3
"""Enumerate actual sinonasal regions, drainage, operative landmarks and extension routes."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for
from tools.anatomy_sources.update_sinonasal_reporting import URLS

ROOT = Path(__file__).resolve().parents[2]
IDENT = 'ra.mri-sinuses'
SOURCES = URLS + ['https://pmc.ncbi.nlm.nih.gov/articles/PMC6472854/']


def build():
    ref = detail(Curriculum(), resolve(IDENT))['radiology_reference']
    guide = ref['reporting']
    structures = []

    def add(key, name, parts, reports, steps, side='not_applicable', modes=None, pathology=False):
        structures.append({
            'id': 'sinonasal.'+key, 'name': name,
            'tissue_class': 'sinonasal_tissue_boundary_compartment_or_route',
            'required_parts': [{'id': 'sinonasal.'+key+'.'+p, 'name': p.replace('_', ' ').capitalize()} for p in parts.split()],
            'laterality': side, 'modality_scope': modes or ['MRI', 'CT'],
            'condition': 'Instantiate every actual covered side, sinus cell, subdivision, variant, lesion, wall and connection. A named standard region is a floor, not a fixed patient cell count. Require source-resolved boundaries with actual acquisition, contrast/sequence and sampling limits; unresolved, microscopic or uncovered anatomy remains missing.',
            'requirement_basis': 'effective_sinonasal_MRI_and_complementary_CT_reporting_scope',
            'report_refs': [{'checklist_index': i, **guide['checklist'][i]} for i in reports],
            'walkthrough_step_indices': steps, 'source_urls': SOURCES,
            'requires_site_instantiation': True,
            'context_requirements': {'purpose': 'pathology_example' if pathology else 'anatomical_reference'},
        })

    region_parts = 'every_actual_cell_or_subdivision full_obtained_lumen_and_content_extent every_resolved_mucosal_or_wall_interface septa_and_adjacent_tissue_relations actual_drainage_connection_if_resolved unassessed_or_variant_extent'
    drainage_parts = 'actual_origin_and_full_obtained_course source_resolved_lumen_and_surrounding_boundaries every_actual_connection_and_endpoint each_source_obstruction_contact_or_variant adjacent_cell_turbinate_septum_or_orbit_relation unresolved_extent_and_function_not_inferred'
    bone_parts = 'each_actual_landmark_and_obtained_extent source_resolved_cortex_boundary_or_unresolved_thin_bone local_orthogonal_planes_and_calibrated_dimensions adjacent_soft_tissue_nerve_vessel_or_orbit_relation every_actual_variant_attachment_defect_or_asymmetry source_sampling_partial_volume_and_unassessed_extent'
    soft_parts = 'actual_named_site_and_full_obtained_extent every_resolved_tissue_boundary each_acquired_signal_enhancement_or_diffusion_component adjacent_bone_compartment_or_route_relation every_actual_variant_lesion_or_connection unresolved_microscopic_or_uncovered_extent'
    route_parts = 'actual_origin_and_full_obtained_course each_resolved_compartment_or_tissue_boundary every_connection_and_endpoint_if_resolved source_lesion_contact_continuity_encasement_or_uncertainty actual_sequence_phase_and_extent_support unassessed_microscopic_or_uncovered_route'

    for side in ['right', 'left']:
        title = side.capitalize()+' '
        for key in ['frontal_sinus', 'maxillary_sinus', 'anterior_ethmoid_cells', 'posterior_ethmoid_cells', 'sphenoid_sinus', 'additional_accessory_or_unassigned_cell']:
            add(side+'_'+key, title+key.replace('_', ' '), region_parts, [0, 2, 3], [0, 1, 3], side)
        for key in ['maxillary_natural_ostium', 'maxillary_accessory_ostia_if_present', 'ethmoid_infundibulum', 'hiatus_semilunaris', 'middle_meatus', 'frontal_recess_and_ostium', 'posterior_ethmoid_drainage_and_superior_meatus', 'sphenoethmoidal_recess_and_sphenoid_ostium', 'inferior_meatus', 'choana']:
            add(side+'_'+key, title+key.replace('_', ' '), drainage_parts, [0, 1, 4], [1, 2, 4], side)
        for key in ['inferior_turbinate', 'middle_turbinate_and_basal_lamella', 'superior_and_additional_turbinates', 'lateral_nasal_wall', 'olfactory_cleft', 'nasal_vestibule_and_floor']:
            add(side+'_'+key, title+key.replace('_', ' '), soft_parts, [0, 1, 3], [0, 1, 2, 3], side)
        for key in ['uncinate_process_and_superior_attachment', 'ethmoid_bulla', 'agger_nasi_and_frontal_recess_cells', 'supraorbital_and_other_actual_frontal_cells', 'haller_cell_if_present', 'onodi_cell_if_present', 'lamina_papyracea', 'fovea_ethmoidalis', 'lateral_lamella_and_olfactory_fossa', 'cribriform_plate', 'sphenoid_roof_sellar_and_clival_relations', 'sphenoid_septa_and_actual_neurovascular_attachments', 'optic_canal_boundary', 'carotid_canal_boundary', 'infraorbital_canal_boundary', 'anterior_ethmoidal_artery_canal', 'posterior_ethmoidal_artery_canal', 'maxillary_sinus_floor_and_dental_interfaces']:
            add(side+'_'+key, title+key.replace('_', ' '), bone_parts, [1, 2, 4], [2, 3, 4], side, ['CT'])
        for key in ['orbit_periorbita_and_extraconal_space', 'orbital_intraconal_space_and_muscles', 'orbital_apex_and_optic_nerve', 'pterygopalatine_fossa', 'infratemporal_and_masticator_spaces', 'premaxillary_retroantral_and_facial_soft_tissue', 'palatal_and_oral_interfaces', 'nasolacrimal_sac_and_duct', 'cavernous_sinus_and_covered_carotid', 'skull_base_marrow']:
            add(side+'_'+key, title+key.replace('_', ' '), soft_parts, [2, 3, 4], [3, 4], side)
        for key in ['V2_infraorbital_pterygopalatine_foramen_rotundum_route', 'vidian_canal_and_nerve_route', 'superior_orbital_fissure_and_covered_nerve_routes', 'additional_actual_foraminal_or_perineural_route', 'ethmoidal_neurovascular_route']:
            add(side+'_'+key, title+key.replace('_', ' '), route_parts, [1, 4], [2, 4], side)
        for key in ['focal_solid_or_polypoid_tissue', 'secretions_fluid_protein_blood_or_fungal_material', 'mucocele_or_other_expansile_component', 'bone_remodelling_sclerosis_calcification_or_destruction', 'postoperative_traumatic_or_repair_interface', 'extrasinus_abscess_or_other_collection', 'encephalocele_or_other_skull_base_communication']:
            add(side+'_'+key, title+'every actual '+key.replace('_', ' '), soft_parts+' each_distinct_lesion_component_and_source_supported_measurement', [0, 2, 3, 4], [0, 2, 3, 4], side, pathology=True)
    for key in ['nasal_septum_and_vomer', 'crista_galli_and_midline_skull_base', 'nasopharynx', 'dura_and_extraaxial_compartments', 'covered_brain_and_intracranial_extension', 'each_additional_cross_midline_or_unassigned_interface']:
        add(key, key.replace('_', ' ').capitalize(), soft_parts+' each_actual_side_or_cross_midline_extent', [0, 1, 2, 3, 4], [0, 1, 2, 3, 4])
    return {
        'investigation_id': IDENT, 'module_id': ref['investigation']['module_id'],
        'title': 'Sinonasal MRI with source-specific complementary CT anatomy',
        'scope_status': 'expanded_draft_requires_independent_sinonasal_anatomical_review',
        'modality_scope': ['MRI', 'CT'],
        'sources': [{'title': title, 'url': url, 'reviewed_at': '2026-10-07', 'review_status': 'source_scope_reviewed_no_graphics_reused'} for title, url in zip(['RA sinonasal CT/MRI', 'Sinonasal lesion review', 'Nasal mass source cases', 'Preoperative sinus CT anatomy'], SOURCES)],
        'source_contract_sha256': digest({k: ref.get(k) for k in ('reporting', 'report_templates', 'walkthrough', 'reading')}),
        'reporting_checklist': guide['checklist'], 'reporting_template_sections': guide['template_sections'],
        'structures': structures,
        'expansion_rules': [
            'All actual cells, subdivisions, drainage branches, variants and pathological connections require independent source instances; standard parent names do not close the inventory.',
            'Acquired thin-section CT is separately required for operative bone detail. MRI tissue signal cannot supply unacquired cortical, canal or dehiscence geometry.',
            'Native source labels and pixel/mesh checks do not establish complete walls, mucosa, nerves, vessels, source-effective resolution or anatomical approval.',
        ],
        'source_scope_issues': [
            'NasalSeg P001 contains only five regional labels; its truncated nasal-pharynx boundary and disconnected left nasal-cavity components remain original source facts.',
            'No NasalSeg native raw DICOM, HU calibration or operative effective-resolution lineage has been independently established.',
            'Source CT cases cannot supply MRI sequences, enhancement, ADC, perineural or histological tissue confirmation for another patient.',
            'Pneumatization, cells, nerve/canal relations and skull-base asymmetry vary by patient; absence and operative classifications require actual evaluated acquisition and measurements.',
        ],
        'functional_evidence_requirements': [
            'Drainage patency and physiological flow are separate clinical/endoscopic/functional claims, not proved by a mask or static lumen.',
            'Histology, organism, invasion and molecular identity need actual supplied clinical or tissue evidence; MRI signal and CT density are not unique diagnoses.',
            'Source ADC or enhancement measurements require their actual acquired sequence, phase, calibration and sampling; no borrowed quantitative values.',
        ],
        'clinical_validation_status': 'draft_requires_head_neck_radiologist_and_sinonasal_surgical_review',
    }


if __name__ == '__main__':
    item = build()
    path = ROOT/'data/radiology/non-msk-structure-requirements.json'
    data = json.loads(path.read_text())
    data['investigations'] = [i for i in data['investigations'] if i['investigation_id'] != IDENT]+[item]
    data['scope']['catalog_investigation_ids'] = [i['investigation_id'] for i in data['investigations']]
    path.write_text(json.dumps(data, indent=2)+'\n')
    n = len(requirements_for(item))
    print(len(item['structures']), 'groups;', n, 'parts;', n*3, 'representation obligations')
