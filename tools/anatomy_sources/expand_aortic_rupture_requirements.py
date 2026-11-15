#!/usr/bin/env python3
"""Expand the full effective AAA reporting contract; no reference presence grants fidelity."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for

ROOT=Path(__file__).resolve().parents[2]
IDENT='ra.aortic-aneurysm-rupture'
URLS=['https://radiologyassistant.nl/abdomen/aorta/aneurysm-rupture',
      'https://pmc.ncbi.nlm.nih.gov/articles/PMC4035490/',
      'https://pmc.ncbi.nlm.nih.gov/articles/PMC9154016/',
      'https://doi.org/10.1016/j.ejvs.2023.11.002']


def build():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];guide=ref['reporting'];structures=[]
    def add(key,name,parts,steps,side='not_applicable',pathology=False,condition=None):
        structures.append({'id':'aaa_rupture.'+key,'name':name,'tissue_class':'aortic_aneurysm_reportable_structure_or_interface',
          'required_parts':[{'id':'aaa_rupture.'+key+'.'+p,'name':label} for p,label in parts],
          'laterality':side,'modality_scope':['CT'],
          'condition':condition or 'Instantiate each actual source-resolved site and variant. Preserve actual patient, side, phase, plane, timing and coverage; retain unresolved boundaries and nonvisualised extent.',
          'requirement_basis':'effective_aaa_rupture_reporting_and_conditional_vascular_planning_scope',
          'report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in steps],
          'walkthrough_step_indices':steps,'source_urls':URLS,
          'context_requirements':{'purpose':'pathology_example' if pathology else 'anatomical_reference'},
          'requires_site_instantiation':True})
    def pairs(names):return [(key,key.replace('_',' ').capitalize()) for key in names.split()]
    add('aortic_course','Complete actual aortic course and longitudinal disease limits',pairs(
        'diaphragmatic_segment supracoeliac_segment suprarenal_segment juxtarenal_segment infrarenal_segment bifurcation '
        'thoracic_extension_if_present proximal_disease_limit distal_disease_limit each_separate_aneurysm_if_present '
        'centreline_and_tortuosity uncovered_aorta_and_screening_limit'),[0,3,4])
    add('aneurysm','Each actual aneurysm sac',pairs(
        'complete_outer_boundary proximal_limit distal_limit morphology_and_asymmetry each_saccular_lobule_if_present '
        'greatest_outer_diameter orthogonal_measurement_plane craniocaudal_extent lumen_relation branch_relation '
        'comparable_prior_plane interval_growth_and_method unresolved_boundary'),[0],pathology=True)
    add('lumen','Aortic patent lumen and internal interfaces',pairs(
        'complete_covered_course lumen_thrombus_boundary lumen_calibre each_stenosis_or_occlusion '
        'each_flap_or_channel_if_present each_fissuration_communication phase_and_opacification_limit'),[0,2,3],pathology=True)
    add('mural_thrombus','Every actual mural thrombus region',pairs(
        'longitudinal_extent circumferential_extent lumen_interface wall_interface thickness_and_plane '
        'each_fissuration_course each_crescent_extent each_crescent_unenhanced_reference unresolved_boundary'),[0,2],pathology=True)
    add('wall','Covered aortic wall and calcified contour',pairs(
        'outer_contour longitudinal_continuity circumferential_continuity source_resolved_thickness '
        'each_calcified_segment each_calcification_gap each_tangential_calcium_interface each_wall_disruption '
        'comparison_and_registration_limit unresolved_noncalcified_wall'),[0,2],pathology=True)
    add('proximal_neck','Actual proximal aneurysm neck and planning interface',pairs(
        'lowest_renal_origin_reference proximal_limit distal_sac_transition centreline_length orthogonal_inner_calibre '
        'orthogonal_outer_calibre taper_or_conicity suprarenal_angulation infrarenal_angulation circumferential_thrombus '
        'circumferential_calcification each_branch_origin actual_landing_or_clamp_zone_if_planned planning_and_device_limit'),[0,3])
    add('rupture_sites','Every suspected or established rupture site',pairs(
        'wall_site circumferential_location proximal_distal_extent lumen_to_wall_relation each_leak_focus '
        'contrast_phase_and_reference contained_or_free_communication haemorrhage_connection uncertainty_and_communication'),[1,2],pathology=True)
    add('posterior_containment','Posterior wall containment and vertebral interface',pairs(
        'posterior_wall_extent anterior_vertebral_contour intervening_fat_plane each_loss_of_plane '
        'wall_draping_extent each_adjacent_haematoma each_vertebral_erosion_if_present unresolved_containment'),[1,2],pathology=True)
    add('contrast_leak','Each actual extravasation focus',pairs(
        'source_arterial_connection focus_boundary contrast_phase temporal_change_if_acquired '
        'extramural_extent compartment_endpoint active_leak_vs_other_enhancement_limit'),[1],pathology=True)
    add('periaortic_tissues','Actual periaortic fat and soft tissue changes',pairs(
        'fat_plane circumferential_extent longitudinal_extent each_stranding_region each_fluid_region each_gas_focus '
        'each_soft_tissue_or_abscess_boundary_if_present aneurysm_and_adjacent_structure_interfaces '
        'inflammatory_infectious_or_other_cause_limit'),[1,2,4],pathology=True)
    # Each compartment remains distinct; one local haematoma image cannot cover the rest.
    compartment_parts=pairs('source_resolved_boundary proximal_extent distal_extent aortic_connection_if_resolved '
                            'adjacent_structure_displacement each_haemorrhage_focus communication_to_other_compartments uncovered_extent')
    for side in ('right','left'):
        for key,label in [('perirenal_space','perirenal space'),('anterior_pararenal_space','anterior pararenal space'),
                          ('posterior_pararenal_space','posterior pararenal space'),('psoas_region','psoas/iliopsoas region'),
                          ('pelvic_extraperitoneal_space','pelvic extraperitoneal extension'),('paracolic_gutter','paracolic gutter')]:
            add(side+'_'+key,side.capitalize()+' '+label,compartment_parts,[1],side,pathology=True)
    for key,label in [('central_retroperitoneum','Central retroperitoneal and great-vessel compartment'),
                      ('perihepatic_space','Perihepatic peritoneal space'),('perisplenic_space','Perisplenic peritoneal space'),
                      ('pelvic_peritoneal_recesses','Pelvic peritoneal recesses appropriate to actual anatomy'),
                      ('mesenteric_peritoneal_space','Mesenteric/interloop peritoneal spaces')]:
        add(key,label,compartment_parts,[1],pathology=True)
    artery_parts=pairs('ostium_and_origin covered_proximal_course covered_distal_course each_branch_or_variant '
                      'lumen_and_calibre wall_calcification_or_thrombus each_stenosis_or_occlusion '
                      'neck_sac_and_repair_relation downstream_territory_if_covered phase_and_coverage_limit')
    for key,label in [('coeliac_artery','Coeliac artery'),('superior_mesenteric_artery','Superior mesenteric artery'),
                      ('inferior_mesenteric_artery','Inferior mesenteric artery')]:
        add(key,label,artery_parts,[3])
    for side in ('right','left'):
        add(side+'_renal_artery',side.capitalize()+' main renal artery',artery_parts,[3],side)
        add(side+'_accessory_renal_arteries',side.capitalize()+' every actual accessory renal artery',artery_parts,[3],side,
            condition='If an accessory renal branch is present or unresolved, instantiate each actual origin, course and supplied territory without borrowing the contralateral anatomy or assuming a device-preservation rule.')
        for key,label in [('common_iliac','common iliac artery'),('internal_iliac','internal iliac artery'),
                          ('external_iliac','external iliac artery'),('common_femoral','common femoral artery')]:
            add(side+'_'+key,side.capitalize()+' '+label,artery_parts+pairs(
                'centreline_and_tortuosity each_aneurysmal_segment minimum_access_lumen_and_plane '
                'proximal_distal_landing_relation_if_planned uncovered_access_and_device_suitability_limit'),[4],side)
        add(side+'_distal_access_runoff',side.capitalize()+' actual distal access and runoff assessment if acquired',pairs(
            'femoral_bifurcation deep_femoral_origin superficial_femoral_covered_course popliteal_covered_course '
            'each_stenosis_occlusion_or_aneurysm covered_distal_branches unacquired_runoff_limit'),[4],side,
            condition='If vascular planning or the acquired source covers distal access/runoff, preserve each actual branch and disease site. Routine abdominal snapshots do not establish whole-limb runoff or operative suitability.')
        add(side+'_distal_seal_zone',side.capitalize()+' actual distal seal/landing zone if planned',pairs(
            'proximal_limit distal_limit orthogonal_calibre centreline_length each_branch_relation '
            'circumferential_thrombus circumferential_calcification angulation device_and_planning_limit'),[4],side)
    perfusion_parts=pairs('complete_covered_extent each_source_enhancement_region vascular_supply_relation '
                          'reference_tissue_and_phase each_hypoperfusion_or_infarct_focus collateral_or_venous_context '
                          'viability_and_uncovered_extent_limit')
    for side in ('right','left'):
        add(side+'_kidney',side.capitalize()+' kidney and covered renal perfusion',perfusion_parts,[1,3],side)
        add(side+'_ureter',side.capitalize()+' covered ureter/collecting-system relationship',pairs(
            'covered_course collecting_system_relation each_compression_or_obstruction_site '
            'haematoma_or_inflammatory_interface uncovered_extent'),[1,4],side)
    for key,label in [('liver','Covered hepatic perfusion'),('spleen','Covered splenic perfusion'),
                      ('duodenum','Duodenum including third portion'),('jejunum','Covered jejunum'),
                      ('ileum','Covered ileum'),('colon','Each covered colonic segment')]:
        add(key,label,perfusion_parts+pairs('each_wall_mesentery_interface each_actual_affected_segment'),[3,4])
    add('aortoenteric_fistula','Every actual aortoenteric or graft-enteric connection if suspected',pairs(
        'aortic_or_graft_endpoint bowel_endpoint each_intervening_course each_wall_interface '
        'sac_or_perigraft_gas bowel_lumen_relation contrast_leak_into_bowel each_secondary_tract '
        'prior_repair_and_timing unresolved_endpoints_and_alternative_cause'),[1,4],pathology=True)
    add('ivc','Covered inferior vena cava and aortocaval interface',pairs(
        'covered_course lumen outer_wall aorta_to_ivc_plane each_fistula_site each_contrast_connection '
        'actual_phase_and_early_enhancement each_compression_or_thrombosis '
        'renal_and_iliac_venous_relations_if_covered flow_and_complete_tract_limit'),[1,4])
    for side in ('right','left'):
        add(side+'_iliac_veins',side.capitalize()+' covered iliac venous relationship',pairs(
            'common_iliac_covered_course internal_external_iliac_covered_course lumen_and_wall '
            'arterial_haematoma_or_device_interface each_compression_or_thrombosis uncovered_extent'),[1,4],side)
    repair_condition='Conditional on actual prior repair or planning history and acquired sources. Instantiate each graft/device, anastomosis, component and complication; nonvisualisation does not prove absence or procedural success.'
    add('open_graft','Actual open aortic graft if present',pairs(
        'complete_covered_graft_course proximal_native_anastomosis distal_native_anastomoses '
        'graft_lumen each_limb_if_present each_clip_or_suture_interface_if_resolved '
        'each_perigraft_collection_or_gas each_pseudoaneurysm each_enteric_or_venous_connection '
        'operative_history_timing_and_uncovered_extent'),[0,1,4],condition=repair_condition)
    add('endograft','Actual aortic endograft if present',pairs(
        'main_body_covered_course proximal_seal attachment_to_native_wall each_component_overlap '
        'each_branch_fenestration_or_stent_if_present each_migration_or_separation each_device_defect_if_resolved '
        'residual_sac_boundary sac_diameter_and_comparable_plane each_sac_contrast_focus '
        'phase_and_endoleak_classification_limit device_history_and_complete_coverage_limit'),[0,1,3,4],condition=repair_condition)
    for side in ('right','left'):
        add(side+'_repair_limb',side.capitalize()+' actual graft/stent-graft limb if present',pairs(
            'component_course component_overlap distal_anastomosis_or_seal branch_relation lumen_and_calibre '
            'each_kink_stenosis_or_occlusion each_leak_or_pseudoaneurysm device_and_timing_limit'),[3,4],side,condition=repair_condition)
    add('repair_complications','Each actual repair-related abnormality if present',pairs(
        'each_sac_enhancement_focus source_phase_and_interval inflow_outflow_if_resolved '
        'each_perigraft_fluid_boundary each_perigraft_gas_focus each_collection_connection '
        'each_device_vessel_or_bowel_interface clinical_microbiological_cause_limit dynamic_and_uncovered_extent_limit'),[1,3,4],pathology=True,condition=repair_condition)
    add('acquisition','Actual acquisition, measurement and comparison controls',pairs(
        'patient_and_examination_identity actual_cranial_coverage actual_caudal_coverage '
        'unenhanced_availability each_actual_contrast_phase bolus_timing reconstructed_slice_spacing '
        'voxel_calibration_and_units orthogonal_planes centreline_method motion_and_metal_artefact '
        'each_actual_comparison_date comparable_source_plane registration_limit '
        'bitmap_hu_and_rendering_limit physiologic_and_clinical_confirmation_limit'),[0,1,2,3,4])
    return {'investigation_id':IDENT,'module_id':'rad.5.aorta','title':'CT aortic aneurysm rupture',
      'scope_status':'expanded_draft_requires_independent_anatomical_and_clinical_review','modality_scope':['CT'],
      'sources':[{'title':t,'url':u,'reviewed_at':'2026-10-06','review_status':s} for t,u,s in zip(
        ['Radiology Assistant aortic aneurysm rupture','Vu et al. original clinical figures and mechanisms',
         'Stoecker et al. isolated crescent-sign cohort','ESVS 2024 abdominal aorto-iliac guidelines'],URLS,
        ['effective_source_scope_reviewed','original_xml_pdf_and_all_13_figures_reviewed',
         'primary_search_extract_reviewed_full_text_web_fetch_blocked','primary_imaging_table_search_extract_reviewed_full_pdf_fetch_blocked'])],
      'source_contract_sha256':digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')}),
      'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':structures,
      'expansion_rules':['Instantiate every actual sac, leak, compartment, branch, access vessel, tract and repair component. Listed children are a known floor; multiple sites are never collapsed into one label.',
        'All leaves require independently reviewed image, schematic and model evidence; anatomy labels, source rights and numeric controls do not grant clinical fidelity.',
        'Preserve both sides, actual variants, acquired phases/coverage and conditional prior-repair/device history.',
        'Uncovered aorta, runoff, organ territories and fistula endpoints remain unresolved rather than normal.'],
      'source_scope_issues':['Original 2014 illustrations describe historical rupture mechanisms, not universal prediction or current device-selection rules.',
        'The isolated crescent cohort is retrospective and excludes definitive rupture at index imaging; it does not justify deferring suspected rupture communication or introduce a universal size/triage threshold.',
        'Guideline imaging-table search extracts are not a full guideline review; complete vascular-radiologist/vascular-team reconciliation remains required.',
        'Aortoenteric examples include different patients; source figures 5/13 share one patient. No patient geometries may be joined across cases.',
        'Flat CT volume renderings and parametric colour maps do not provide acquired geometry, centreline calibration or registered comparison.',
        'Generic arch-focused procedural landmarks do not satisfy abdominal sac, branch, compartment, access, fistula or repair coverage.'],
      'functional_evidence_requirements':['Rupture assessment requires actual acquired phases, wall/leak interfaces, covered haemorrhage extent and immediate clinical communication when suspected.',
        'Calibre, size and growth require original calibrated voxel series, orthogonal plane/centreline method and comparable acquisition; bitmap HU or colour-map estimates are insufficient.',
        'Perfusion, shunt flow, organ viability, fistula continuity and endoleak classification need appropriate source phases/dynamics and clinical confirmation.',
        'Device suitability, operative outcome and infection diagnosis require actual planning/history and clinical evidence rather than a generic model or isolated negative view.'],
      'clinical_validation_status':'draft_requires_vascular_radiologist_and_multidisciplinary_review'}


if __name__=='__main__':
    item=build();path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    data['investigations']=[r for r in data['investigations'] if r['investigation_id']!=IDENT]+[item]
    data['scope']['catalog_investigation_ids']=[r['investigation_id'] for r in data['investigations']]
    path.write_text(json.dumps(data,indent=2)+'\n')
    print(len(item['structures']),'groups;',len(requirements_for(item)),'leaves;',len(requirements_for(item))*3,'representation obligations')
