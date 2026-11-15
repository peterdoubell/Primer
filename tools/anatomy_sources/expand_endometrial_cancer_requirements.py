#!/usr/bin/env python3
"""Name the actual endometrial MRI reporting sites, layers and interfaces.

Inventory expansion makes missing fidelity visible. It grants no anatomical,
clinical, measurement or source-registration approval.
"""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_msk_fidelity import requirements_for
from tools.check_radiology_fidelity import digest

INV = 'ra.mri-endometrial-cancer'
SOURCES = [
    'https://doi.org/10.1002/ijgo.14923',
    'https://doi.org/10.1002/ijgo.15193',
    'https://doi.org/10.1007/s00330-025-11700-3',
    'https://doi.org/10.1007/s00330-026-12705-2',
    'https://pmc.ncbi.nlm.nih.gov/articles/PMC11119523/',
    'https://pmc.ncbi.nlm.nih.gov/articles/PMC12830431/',
    'https://pmc.ncbi.nlm.nih.gov/articles/PMC13025262/',
    'https://pmc.ncbi.nlm.nih.gov/articles/PMC7643338/',
    'https://radiologyassistant.nl/abdomen/unsorted/mr-in-endometrial-cancer',
]


def build():
    ref = catalog.detail(Curriculum(), catalog.resolve(INV))['radiology_reference']
    guide = copy.deepcopy(ref['reporting'])
    groups = []
    whole = 'actual_covered_identity_and_extent source_endpoints_and_boundaries adjacent_tissue_or_organ_interface source_resolution_unresolved_or_unacquired_extent'
    layer = 'actual_named_site_and_extent source_inner_and_outer_boundaries thickness_or_explicitly_unresolved_layer adjacent_layer_lumen_or_lesion_interface source_resolution_and_uncertainty'
    lesion = 'each_actual_lesion_identity_site_and_extent source_signal_and_acquired_phase source_outer_and_internal_boundaries adjacent_organ_layer_lumen_vessel_or_node_interface source_measurement_plane_scale_and_uncertainty source_unresolved_or_unacquired_extent'

    def add(key, name, parts, indices, side='midline', pathology=False, condition=None):
        prefix = 'endometrial_cancer.' + key
        groups.append({'id': prefix, 'name': name, 'laterality': side,
            'tissue_class': 'uterine_cervical_adnexal_vaginal_parametrial_urinary_bowel_vascular_nodal_peritoneal_or_covered_staging_structure',
            'modality_scope': ['MRI'],
            'required_parts': [{'id': prefix+'.'+part, 'name': part.replace('_', ' ')} for part in parts.split()],
            'report_refs': [{'checklist_index': i, **guide['checklist'][i]} for i in indices],
            'walkthrough_step_indices': indices, 'source_urls': SOURCES,
            'requirement_basis': 'effective_full_endometrial_MRI_reporting_contract_and_primary_staging_anatomy',
            'requires_site_instantiation': True,
            'context_requirements': {'purpose': 'pathology_example' if pathology else 'anatomical_reference'},
            'condition': condition or 'Instantiate each actually covered/reported site, side, lesion and interface. Preserve source resolution and missing/unacquired boundaries. Parent organs, publication figures and atlas surface names cannot approve separated fine tissues.'})

    for site in ['whole_uterine_body_and_orientation', 'uterine_fundus', 'anterior_uterine_body', 'posterior_uterine_body',
                 'uterine_isthmus_lower_segment', 'uterine_cavity', 'internal_cervical_os', 'endocervical_canal',
                 'external_cervical_os', 'anterior_cervical_lip', 'posterior_cervical_lip', 'cervical_stroma_covered_extent']:
        add('central.'+site, site.replace('_', ' ').capitalize(), whole, [0, 1, 2, 7])
    for side in ['left', 'right']:
        for site in ['uterine_lateral_wall', 'uterine_cornu', 'tubal_uterine_interface']:
            add(side+'.uterine.'+site, side.capitalize()+' '+site.replace('_', ' '), whole, [0, 1, 3, 7], side)
    for site in ['source_visible_endometrium', 'endometrial_cavity_luminal_interface', 'endometrial_myometrial_interface',
                 'source_visible_junctional_zone', 'inner_myometrium', 'outer_myometrium', 'subserosal_interface',
                 'serosal_outer_contour', 'endocervical_canal_stromal_interface', 'source_visible_cervical_stromal_ring',
                 'outer_cervical_stromal_parametrial_interface']:
        add('central_layer.'+site, site.replace('_', ' ').capitalize(), layer, [0, 1, 2, 3])
    for site in ['each_actual_primary_tumour', 'each_polypoid_mass_or_diffuse_thickening_component',
                 'each_source_supported_myometrial_invasive_front', 'each_cornual_tumour_wall_interface',
                 'each_canal_protrusion_or_cervical_stromal_extension', 'each_subserosal_or_serosal_extension',
                 'each_actual_leiomyoma', 'each_actual_adenomyosis_focus_or_zone', 'each_actual_endometriosis_finding',
                 'each_other_observed_benign_or_indeterminate_mimic', 'each_source_visible_biopsy_or_procedure_change',
                 'each_actual_developmental_or_positional_variant']:
        add('primary.'+site, site.replace('_', ' ').capitalize(), lesion, [0, 1, 2, 3, 7], pathology=True)
    add('measure.myometrial_depth', 'Deepest invasion and same-site full myometrial thickness',
        'actual_invasive_front_identity reconstructed_inner_myometrial_boundary local_outer_wall_reference source_aligned_plane_and_scale depth_and_thickness_endpoints uncertainty_and_evaluability', [1])
    add('measure.tumour_axes', 'Actual maximal and orthogonal tumour dimensions',
        'each_actual_tumour_boundary longest_and_orthogonal_source_axes source_plane_scale_and_units uncertainty_or_unresolved_margin', [0, 7])
    add('measure.uterine_axes', 'Actual whole uterine size and orientation',
        'actual_whole_uterine_extent including_cervical_reference maximal_and_orthogonal_source_axes source_plane_scale_and_units variant_distortion_and_unacquired_extent', [0, 7])
    for side in ['left', 'right']:
        for site in ['ovary', 'fallopian_tube_covered_extent', 'tubal_interstitial_uterine_part', 'tubal_isthmus',
                     'tubal_ampulla', 'source_resolved_infundibular_fimbrial_extent', 'ovarian_uterine_attachment',
                     'covered_broad_ligament_fold', 'covered_parametrial_tissue', 'uterosacral_origin_and_covered_course',
                     'parametrial_vessel_interface', 'parametrial_ureter_interface', 'covered_pelvic_sidewall_interface']:
            add(side+'.adnexal_pelvic.'+site, side.capitalize()+' '+site.replace('_', ' '), whole, [3, 4, 7], side)
        for site in ['source_visible_ovarian_capsular_interface', 'tubal_lumen_wall_interface', 'tubal_outer_wall_adjacent_tissue_interface']:
            add(side+'.adnexal_layer.'+site, side.capitalize()+' '+site.replace('_', ' '), layer, [3], side)
        for site in ['each_actual_adnexal_mass_or_deposit', 'each_tubal_or_ovarian_tumour_interface',
                     'each_actual_parametrial_or_vascular_extension', 'each_actual_sidewall_contact_or_extension']:
            add(side+'.adnexal_lesion.'+site, side.capitalize()+' '+site.replace('_', ' '), lesion, [3, 4], side, True)
        for site in ['covered_ureter', 'distal_ureter', 'ureteric_orifice', 'covered_renal_pelvis_and_calyces']:
            add(side+'.urinary.'+site, side.capitalize()+' '+site.replace('_', ' '), whole, [4], side)
        add(side+'.urinary_obstruction', side.capitalize()+' each actual obstruction or periureteral lesion', lesion, [4], side, True)
        for station in ['obturator', 'internal_iliac', 'external_iliac', 'common_iliac', 'inguinal']:
            add(side+'.node_station.'+station, side.capitalize()+' covered '+station.replace('_', ' ')+' station', whole, [5], side)
            add(side+'.node.'+station, side.capitalize()+' each actual suspicious '+station.replace('_', ' ')+' node', lesion, [5], side, True)
    for site in ['anterior_vaginal_fornix', 'posterior_vaginal_fornix', 'left_vaginal_fornix', 'right_vaginal_fornix',
                 'covered_vaginal_extent', 'vesicovaginal_interface', 'rectovaginal_interface']:
        add('vaginal.'+site, site.replace('_', ' ').capitalize(), whole, [4])
    for site in ['anterior_vaginal_wall', 'posterior_vaginal_wall', 'left_vaginal_wall', 'right_vaginal_wall',
                 'vaginal_lumen_wall_interface', 'vaginal_outer_wall_adjacent_tissue_interface']:
        add('vaginal_layer.'+site, site.replace('_', ' ').capitalize(), layer, [4])
    add('vaginal.each_actual_deposit_or_extension', 'Each actual vaginal deposit or contiguous extension', lesion, [4], pathology=True)
    for site in ['bladder_covered_extent', 'bladder_base_trigone', 'bladder_posterior_wall_tumour_interface',
                 'covered_rectum', 'covered_sigmoid', 'each_other_actual_contacted_bowel_segment',
                 'each_other_reported_adjacent_organ']:
        add('adjacent.'+site, site.replace('_', ' ').capitalize(), whole, [4])
    for organ in ['bladder', 'rectum', 'actual_contacted_bowel_segment']:
        for tissue in ['source_visible_mucosal_luminal_interface', 'submucosa_or_explicitly_unresolved_interface',
                       'muscular_wall', 'outer_wall_adjacent_tissue_interface']:
            add('adjacent_layer.'+organ+'.'+tissue, organ.replace('_', ' ').capitalize()+' '+tissue.replace('_', ' '), layer, [4])
        for site in ['each_actual_contact', 'each_suspected_wall_or_mucosal_extension', 'each_oedema_or_other_mimic',
                     'each_luminal_abnormality_or_fistula']:
            add('adjacent_lesion.'+organ+'.'+site, organ.replace('_', ' ').capitalize()+' '+site.replace('_', ' '), lesion, [4], pathology=True)
    for site in ['presacral_station', 'covered_paraaortic_below_renal_vessels', 'covered_paraaortic_above_renal_vessels',
                 'actual_renal_vessel_reference', 'covered_other_distant_nodal_station']:
        add('nodes.'+site, site.replace('_', ' ').capitalize(), whole, [5])
    for site in ['each_actual_suspicious_presacral_node', 'each_actual_suspicious_paraaortic_node_with_level',
                 'each_actual_other_distant_node', 'each_actual_node_short_axis_and_morphology']:
        add('nodes_lesion.'+site, site.replace('_', ' ').capitalize(), lesion, [5], pathology=True)
    for site in ['covered_pelvic_peritoneal_surface', 'covered_extrapelvic_peritoneal_surface', 'covered_omentum',
                 'covered_mesentery', 'covered_diaphragmatic_or_organ_surface', 'covered_lung', 'covered_liver',
                 'covered_bone', 'each_other_actually_acquired_distant_site']:
        add('spread.'+site, site.replace('_', ' ').capitalize(), whole, [6])
    for site in ['each_actual_pelvic_peritoneal_deposit', 'each_actual_extrapelvic_peritoneal_or_omental_deposit',
                 'each_actual_mesenteric_or_organ_surface_lesion', 'each_actual_ascites_or_indeterminate_fluid_finding',
                 'each_actual_distant_organ_or_skeletal_lesion']:
        add('spread_lesion.'+site, site.replace('_', ' ').capitalize(), lesion, [6], pathology=True)
    for site in ['each_actual_surgical_vaginal_cuff_or_uterine_remnant', 'each_actual_suspected_residual_or_recurrent_lesion',
                 'each_observed_fibrotic_oedematous_or_postprocedural_interface', 'each_actual_matched_comparison_site',
                 'each_actual_post_treatment_organ_wall_or_fistula_change']:
        add('comparison.'+site, site.replace('_', ' ').capitalize(), lesion, [8], pathology=True,
            condition='Required for the actual supplied treatment/comparison examination. Instantiate altered anatomy, real dates/sequences, matching method and each lesion/interface. Missing serial sources remain missing; baseline publication recurrence is not a response sequence or patient registration.')
    return {'investigation_id': INV, 'module_id': 'rad.5.uterine-mr',
        'title': 'Endometrial cancer — MRI staging, planning and supplied comparison',
        'scope_status': 'expanded_draft_requires_independent_specialist_pelvic_MRI_and_clinical_review',
        'modality_scope': ['MRI'],
        'sources': [{'title': 'Primary endometrial MRI/reporting scope', 'url': url, 'reviewed_at': '2026-10-11',
                     'review_status': 'effective_assigned_reporting_scope_reconciled_with_primary_staging'} for url in SOURCES],
        'source_contract_sha256': digest({k: ref.get(k) for k in ['reporting', 'report_templates', 'walkthrough', 'reading']}),
        'reporting_checklist': guide['checklist'], 'reporting_template_sections': guide['template_sections'],
        'structures': groups,
        'expansion_rules': [
            'For every actual named site, side, fine layer, lesion and measured interface, clinical image, schematic and 3D obligations remain distinct and unapproved until independently evidenced.',
            'MRI zones, histological tissues and source morphological surfaces are distinct. Preserve age, cycle, treatment, source resolution and explicitly unresolved layers.',
            'Conditional nodes, distant sites and follow-up findings require actual acquired coverage and site instantiation; no inventory count establishes exhaustive complete anatomy.',
        ],
        'source_scope_issues': [
            'Primary FIGO 2023 separates pelvic peritoneal, extrapelvic peritoneal and other distant spread. Secondary source errors and historical stage versions are retained as source context, not imported as current criteria.',
            'MRI cannot independently assign histology/grade, LVSI, molecular status, nodal micro/macrometastatic burden or microscopic response.',
            'Complete licensed source figures preserve their real cases/phases and annotations; they do not prove each fine-layer boundary or calibrate/register another patient.',
            'The original HRA surfaces have preserved source-level provenance conflicts, open boundaries and shared uterine-wall triangles. They do not supply independently validated endometrium, myometrium, junctional zone, organ-wall layers or current-patient lesions.',
        ],
        'functional_evidence_requirements': [
            'Each measurement requires actual acquired endpoints, plane, scale and uncertainty; atlas coordinates and published raster dimensions are not patient calibration.',
            'Staging, fertility planning, obstruction and response require actual clinical/pathological/acquisition context. Preserve missing coverage and unknown interfaces.',
        ],
        'clinical_validation_status': 'draft_requires_specialist_pelvic_MRI_and_gynaecological_oncology_review'}


def main():
    path = ROOT / 'data/radiology/non-msk-structure-requirements.json'
    data = json.loads(path.read_text())
    item = build()
    data['investigations'] = [old for old in data['investigations'] if old['investigation_id'] != INV] + [item]
    data['scope']['catalog_investigation_ids'] = [old['investigation_id'] for old in data['investigations']]
    data['updated_at'] = '2026-10-11'
    path.write_text(json.dumps(data, indent=2) + '\n')
    leaves = list(requirements_for(item))
    print(len(item['structures']), 'groups;', len(leaves), 'fine leaves;', len(leaves)*3,
          'distinct representation obligations; no clinical approval.')


if __name__ == '__main__':
    main()
