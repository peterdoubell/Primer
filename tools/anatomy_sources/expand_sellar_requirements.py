#!/usr/bin/env python3
"""Require actual sellar tissues/interfaces without treating a five-shape schematic as anatomy."""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for

IDENT = 'ra.mri-sella'
SOURCES = [
    ('Effective sellar reporting source', 'https://radiologyassistant.nl/neuroradiology/sella-turcica/sella-turcica-and-parasellar-region'),
    ('Tsukamoto and Miki: PitNET imaging', 'https://link.springer.com/article/10.1007/s11604-023-01400-7'),
    ('Correction of Figure5b and reference2', 'https://link.springer.com/article/10.1007/s11604-023-01414-1'),
    ('Tsukamoto and Miki: other sellar lesions and mimics', 'https://link.springer.com/article/10.1007/s11604-023-01407-0'),
]


def build():
    ref = catalog.detail(Curriculum(), catalog.resolve(IDENT))['radiology_reference']
    guide = copy.deepcopy(ref['reporting'])
    groups = []

    def add(key, name, parts, reports, steps, side='midline', modalities=None, pathology=False, condition=None):
        prefix = 'sella.' + key
        groups.append({'id': prefix, 'name': name, 'laterality': side,
            'tissue_class': 'sellar_neural_vascular_dural_bone_lesion_or_actual_treatment_interface',
            'modality_scope': modalities or ['MRI'],
            'required_parts': [{'id': prefix + '.' + part, 'name': part.replace('_', ' ')} for part in parts.split()],
            'report_refs': [{'checklist_index': i, **guide['checklist'][i]} for i in reports],
            'walkthrough_step_indices': steps, 'source_urls': [u for _, u in SOURCES],
            'requirement_basis': 'effective_sellar_report_and_primary_acquired_structure_interface_scope',
            'requires_site_instantiation': True,
            'context_requirements': {'purpose': 'pathology_example' if pathology else 'anatomical_reference'},
            'condition': condition or ('Instantiate every actually reported site, side, lesion/component and acquired interface. '
                'Required anatomical parts are not supplied automatically by a parent gland or vessel label. '
                'Source resolution, coverage and sequence quality must support the particular tissue/observation; '
                'unresolved microscopic or unacquired extent remains missing. No anatomical surface supplies hormones, visual function or histology.')})

    add('gland', 'Whole source pituitary gland', 'source_extent anterior_posterior_right_left_superior_inferior_boundaries capsule_or_unresolved_capsule residual_normal_gland lesion_gland_interface sellar_dural_interface actual_axes source_unresolved_extent', [0,1], [0,1])
    for key, name, parts in [
        ('adenohypophysis','Anterior pituitary tissue','source_extent anterior_posterior_lateral_superior_inferior_regions posterior_lobe_interface stalk_pars_tuberalis_relation lesion_compressed_gland_interface age_sex_pregnancy_treatment_context source_unresolved_tissue'),
        ('neurohypophysis','Posterior pituitary tissue','source_extent anterior_lobe_interface infundibular_continuity source_precontrast_T1_bright_spot displaced_or_ectopic_tissue lesion_interface source_unresolved_tissue'),
        ('pars_intermedia','Encountered pars intermedia / Rathke cleft region','actual_source_region anterior_lobe_interface posterior_lobe_interface cyst_or_lesion_interface unresolved_microscopic_extent'),
        ('stalk','Pituitary stalk and infundibulum','source_whole_course proximal_distal_junctions anterior_posterior_lateral_surfaces actual_thickness_axes gland_attachment hypothalamic_attachment lesion_or_displacement_interface source_unresolved_extent'),
        ('pars_tuberalis','Encountered pars tuberalis','source_obtained_extent stalk_surface_relation gland_continuity lesion_or_ectopic_relation unresolved_tissue_identity'),
        ('hypothalamus','Source hypothalamus','actual_obtained_extent third_ventricular_floor optic_and_infundibular_relations lesion_contact_displacement_or_supported_extension_interface internal_source_signal_components unresolved_extent'),
        ('tuber_cinereum','Encountered tuber cinereum / median eminence','actual_obtained_extent infundibular_relation hypothalamic_interface hamartoma_or_other_lesion_interface source_unresolved_substructure'),
        ('mammillary_bodies','Encountered mammillary-body region','actual_obtained_extent paired_source_components hypothalamic_interface adjacent_cistern_interface lesion_or_displacement_relation unresolved_extent'),
    ]:
        add(key, name, parts, [0,1,2], [0,1,2])
    add('optic_chiasm','Complete obtained optic chiasm','source_extent anterior_posterior_right_left_superior_inferior_surfaces actual_prefixed_or_postfixed_configuration nerve_and_tract_junctions lesion_contact_elevation_compression_interface source_T2_signal_and_evaluability unresolved_fibre_and_tissue_extent', [0,2], [2,3])
    for side in ['right','left']:
        for key, name in [('optic_nerve','Prechiasmatic optic nerve'),('optic_tract','Postchiasmatic optic tract')]:
            add(side + '.' + key, side.capitalize() + ' ' + name, 'whole_obtained_course source_endpoints_and_junctions neural_surface sheath_CSF_or_unresolved_interface adjacent_artery_cistern_relation lesion_contact_displacement_compression_or_extension_interface source_signal_components unacquired_or_unresolved_extent', [0,2,3], [2,3,4], side)
        add(side + '.cavernous_sinus', side.capitalize() + ' cavernous sinus', 'whole_obtained_extent source_venous_spaces medial_superior_inferior_lateral_walls anterior_posterior_endpoints source_ICA_relation neural_region_relations tumour_wall_or_channel_interface source_unresolved_compartments', [0,3,4], [4], side)
        for region in ['medial_wall','lateral_wall','superior_wall','inferior_wall','anterior_interface','posterior_interface','superior_ICA_compartment','inferior_ICA_compartment','lateral_ICA_compartment']:
            add(side + '.cavernous.' + region, side.capitalize() + ' cavernous sinus ' + region.replace('_',' '), 'source_obtained_extent individual_tissue_or_channel_boundaries adjacent_gland_ICA_neural_or_dural_interface lesion_contact_displacement_or_supported_extension_interface unresolved_thin_wall_or_compartment_extent', [3,4], [4], side)
        for nerve in ['III_oculomotor','IV_trochlear','V1_ophthalmic','V2_maxillary','VI_abducens','encountered_ICA_sympathetic_plexus']:
            add(side + '.neural.' + nerve, side.capitalize() + ' encountered ' + nerve.replace('_',' '), 'actual_obtained_course source_endpoints neural_surface_or_unresolved_surface cavernous_wall_ICA_or_channel_relationship lesion_contact_displacement_or_supported_extension_interface unresolved_fascicles_and_unacquired_extent', [0,3,4], [4], side)
        for artery in ['cavernous_ICA','clinoid_ICA','supraclinoid_ICA','covered_ophthalmic_origin','covered_ACA_origin','covered_MCA_origin','encountered_PCom','encountered_superior_hypophyseal_branches','encountered_inferior_hypophyseal_branches']:
            add(side + '.artery.' + artery, side.capitalize() + ' ' + artery.replace('_',' '), 'actual_source_course_and_branches source_lumen source_wall_or_unresolved_wall source_origin_endpoints_bends lesion_contact_displacement_encasement_or_narrowing_interface optic_dural_bone_relations actual_variant_or_aneurysm_interface unresolved_or_unacquired_extent', [0,3,4], [3,4], side, ['MRI','CT'])
        for vein in ['covered_superior_inferior_ophthalmic_veins','covered_superior_petrosal_sinus','covered_inferior_petrosal_sinus','encountered_other_cavernous_connections']:
            add(side + '.vein.' + vein, side.capitalize() + ' ' + vein.replace('_',' '), 'actual_source_course_and_connections source_lumen source_wall_or_unresolved_wall cavernous_or_neural_connection lesion_thrombus_or_fistula_interface uncovered_or_unresolved_extent', [3,4], [4], side, ['MRI','CT'])
        for key in ['optic_canal_if_covered','anterior_clinoid','posterior_clinoid','carotid_protuberance_or_dehiscence_if_encountered','optic_protuberance_or_dehiscence_if_encountered']:
            add(side + '.bone.' + key, side.capitalize() + ' ' + key.replace('_',' '), 'actual_obtained_bone_extent cortical_boundary_and_thickness_or_unresolved_cortex marrow_or_air_cells adjacent_neural_vascular_sinus_interface remodelling_erosion_or_treatment_interface unresolved_or_unacquired_extent', [0,3,4], [4], side, ['MRI','CT'])
    for key, name in [('diaphragma_sellae','Sellar diaphragm'),('sellar_dura','Sellar dura and gland/dural interface'),('encountered_basal_meninges','Encountered basal meninges'),('intercavernous_connections','Encountered intercavernous venous connections')]:
        add(key, name, 'actual_obtained_extent source_tissue_or_channel_boundary gland_stalk_cistern_or_sinus_interface actual_opening_junction_or_variant lesion_contact_displacement_or_supported_extension_interface source_unresolved_extent', [0,2,3,4], [2,3,4], modalities=['MRI','CT'])
    for key in ['suprasellar_cistern','prechiasmatic_cistern','covered_carotid_cisterns','third_ventricle_floor_and_infundibular_recess','covered_other_ventricles_and_hydrocephalus']:
        add('CSF.' + key, key.replace('_',' '), 'actual_obtained_space_extent neural_dural_or_vascular_boundaries source_CSF_or_other_contents lesion_contact_obstruction_or_extension_interface unacquired_or_unresolved_extent', [0,1,2,3], [0,1,2,3])
    for key in ['sellar_floor','right_sellar_wall','left_sellar_wall','tuberculum_sellae','dorsum_sellae','clivus','sphenoid_body','sphenoid_sinus_lumen','sphenoid_sinus_mucosa','sphenoid_sinus_septa','sphenoid_pneumatization_variants_if_present','covered_nasopharynx_or_ectopic_tissue']:
        add('skull_base.' + key, key.replace('_',' '), 'whole_actual_obtained_extent source_inner_outer_boundaries cortex_marrow_air_mucosa_or_other_actual_components neural_vascular_dural_or_gland_interface lesion_remodelling_erosion_or_extension_interface actual_variant_or_postoperative_interface source_unresolved_extent', [0,1,4], [0,1,4], modalities=['MRI','CT'])
    for key in ['every_gland_lesion','every_stalk_lesion','every_suprasellar_or_hypothalamic_lesion','every_parasellar_or_cavernous_lesion','every_bone_or_sinus_lesion','every_encountered_ectopic_or_additional_lesion']:
        add('lesion.' + key, key.replace('_',' '), 'every_actual_lesion_identity_and_epicentre whole_obtained_lesion_extent source_three_dimensional_axes each_solid_cystic_or_other_component source_external_and_internal_margins gland_neural_vascular_dural_bone_CSF_interfaces source_unresolved_or_unacquired_extent', [0,1,2,3,4], [0,1,2,3,4], modalities=['MRI','CT'], pathology=True)
    for key in ['each_solid_component','each_cyst_fluid_component','each_septum_or_mural_nodule','each_haemorrhagic_appearing_component','each_infarct_or_necrotic_appearing_component','each_calcific_or_other_susceptibility_component','each_fluid_fluid_interface','each_dynamic_enhancing_or_unresolved_region']:
        add('lesion_component.' + key, key.replace('_',' '), 'actual_component_identity_and_extent source_signal_or_material_observations source_outer_and_internal_interfaces adjacent_residual_gland_or_lesion_tissues named_acquisition_phase_timepoint_and_evaluability unverified_tissue_or_unacquired_extent', [0,1,2,3], [0,1,2,3], modalities=['MRI','CT'], pathology=True)
    for key in ['optic_contact_or_compression','cavernous_wall_or_channel_extension','ICA_encasement_narrowing_or_aneurysm_mimic','hypothalamic_or_ventricular_extension','sellar_floor_or_clival_extension','sphenoid_or_nasopharyngeal_extension','actual_multiple_structure_or_other_extension']:
        add('lesion_interface.' + key, key.replace('_',' '), 'each_actual_host_structure_and_contact_extent source_lesion_side_boundary source_host_side_boundary intervening_tissue_plane_or_unresolved_plane displacement_contact_or_supported_extension_geometry source_confidence_unresolved_or_uncovered_extent', [0,1,2,3,4], [0,1,2,3,4], modalities=['MRI','CT'], pathology=True)
    for key in ['actual_residual_gland_and_lesion','actual_resection_cavity','actual_graft_flap_or_packing','actual_blood_fluid_or_air','actual_sellar_floor_dural_or_sinus_defect','actual_treated_optic_or_cavernous_interface','actual_prior_radiotherapy_or_medical_response_region']:
        add('treatment.' + key, key.replace('_',' '), 'actual_case_treatment_identity_and_timepoint whole_obtained_component_extent source_internal_external_interfaces adjacent_neural_vascular_dural_bone_or_sinus_relations source_same_case_comparison_and_registration_limits residual_recurrence_postoperative_material_or_unresolved_tissue source_unacquired_extent', [0,1,2,3,4], [0,1,2,3,4], modalities=['MRI','CT'], pathology=True)
    return {'investigation_id': IDENT, 'module_id': ref['investigation']['module_id'],
        'title': 'Complete acquired sellar gland neural vascular dural skull-base and lesion-interface scope',
        'scope_status': 'expanded_draft_requires_independent_sellar_anatomical_and_clinical_review',
        'clinical_validation_status': 'draft_requires_neuroradiologist_anatomist_and_relevant_endocrine_neurosurgical_review',
        'modality_scope': ['MRI','CT'], 'required_representations': ['image','schematic','model'],
        'sources': [{'title': title, 'url': url, 'reviewed_at': '2026-10-09', 'review_status': 'primary_source_or_effective_report_scope_reviewed_no_image_licence_inferred'} for title,url in SOURCES],
        'reporting_checklist': guide['checklist'], 'reporting_template_sections': guide['template_sections'], 'structures': groups,
        'source_contract_sha256': digest({k: ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']}),
        'expansion_rules': ['Every actual side/site/lesion/component and reported acquired field is instantiated separately; this list is a floor, not a complete patient denominator.',
            'MRI, actual dynamic acquisition, CT bone/calcification and actual angiographic observations require their own source and quality; no modality borrows missing observations.',
            'Age, sex, pregnancy, clinical endocrine/visual context, variants and prior treatment must match the particular source and intended use.',
            'Published images and five-shape schematic orientation do not fulfil their unresolved tiny walls, branch courses, nerves, tissues or full interfaces automatically.'],
        'source_scope_issues': ['Fine sellar/optic/cavernous/ICA/skull-base interfaces remain unapproved; inherited remote image reuse and native source registration require separate evidence.',
            'Clinical hormone production, tissue lineage, microscopic invasion, visual dysfunction and apoplexy require appropriate supplied clinical/tissue context; they are not fabricated model components.'],
        'functional_evidence_requirements': ['Actual contrast dynamics require sequence timestamps, bolus context, complete relevant frames and source ROIs; a published90-second still is not a kinetic curve.',
            'Vessel patency, aneurysm exclusion, shunt flow and perfusion require adequate actual corresponding acquisitions; a flow void or neutral 3D tube is insufficient.',
            'Diffusion/ADC, haemorrhage timing and tissue identity require appropriate source acquisition/calibration and clinical correlation; displayed signal is not an unverified physical or pathological measurement.']}


def update():
    item = build()
    path = ROOT / 'data/radiology/non-msk-structure-requirements.json'
    data = json.loads(path.read_text())
    data['investigations'] = [r for r in data['investigations'] if r['investigation_id'] != IDENT] + [item]
    data['scope']['catalog_investigation_ids'] = [r['investigation_id'] for r in data['investigations']]
    path.write_text(json.dumps(data, indent=2) + '\n')
    parts = len(requirements_for(item))
    print(len(item['structures']), 'sellar groups;', parts, 'component requirements;', parts * 3, 'representation obligations; no approval granted')


if __name__ == '__main__':
    update()
