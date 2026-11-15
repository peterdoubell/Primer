#!/usr/bin/env python3
"""Bind the complete acute-aortic reporting scope without granting clinical completeness."""
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for

ROOT=Path(__file__).resolve().parents[2]
IDENT='ra.ct-acute-aortic-syndrome'
URLS=['https://radiologyassistant.nl/cardiovascular/thoracic-aorta/acute-aortic-syndrome',
      'https://pmc.ncbi.nlm.nih.gov/articles/PMC3505562/','https://pmc.ncbi.nlm.nih.gov/articles/PMC9860464/',
      'https://www.sts.org/sites/default/files/content/TBAD_Guideline_2022.pdf']

def build():
    ref=detail(Curriculum(),resolve(IDENT))['radiology_reference'];guide=ref['reporting'];structures=[]
    def parts(text):return [(p,p.replace('_',' ').capitalize()) for p in text.split()]
    def add(key,name,leaves,steps,side='not_applicable',pathology=False,modality=None,condition=None):
        structures.append({'id':'aas.'+key,'name':name,'tissue_class':'acute_aortic_reportable_structure_or_interface',
            'required_parts':[{'id':'aas.'+key+'.'+p,'name':label} for p,label in leaves],
            'laterality':side,'modality_scope':modality or ['CT'],
            'condition':condition or 'Instantiate every actual site and source-resolved variant. Preserve actual patient, side, phase, coverage, timing and unresolved boundaries; nonvisualisation or a local schematic cannot prove normality or absent disease.',
            'requirement_basis':'effective_acute_aortic_reporting_and_conditional_complication_scope',
            'report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in steps],
            'walkthrough_step_indices':steps,'source_urls':URLS,'requires_site_instantiation':True,
            'context_requirements':{'purpose':'pathology_example' if pathology else 'anatomical_reference'}})
    course=parts('proximal_limit distal_limit centreline_and_tortuosity outer_wall_contour lumen_wall_interface each_disease_transition each_branch_relation orthogonal_measurement_level unresolved_or_uncovered_extent')
    for key,label in [('root','Aortic root'),('sinotubular_junction','Sinotubular junction'),('ascending_aorta','Ascending aorta'),
                      ('proximal_arch','Proximal aortic arch'),('distal_arch','Distal aortic arch'),('isthmus','Aortic isthmus'),
                      ('descending_thoracic_aorta','Descending thoracic aorta'),('diaphragmatic_aorta','Diaphragmatic aorta'),
                      ('suprarenal_aorta','Suprarenal abdominal aorta'),('juxtarenal_aorta','Juxtarenal abdominal aorta'),
                      ('infrarenal_aorta','Infrarenal abdominal aorta'),('bifurcation','Aortic bifurcation')]:
        add(key,label,course,[0,1,4])
    add('extent','Every actual continuous or separate disease extent',parts('proximal_disease_limit distal_disease_limit ascending_involvement entry_site_if_resolved arch_pattern each_discontinuous_focus each_variant_arch_course named_classification_and_version classification_uncertainty temporal_onset_and_comparison_limit uncovered_aorta'),[0],pathology=True)
    add('wall','Covered aortic wall, calcium and adjacent plaque',parts('complete_covered_longitudinal_extent circumferential_extent inner_interface outer_interface source_resolved_thickness each_calcified_segment each_displaced_calcification each_plaque_region each_wall_disruption unresolved_layer_boundaries'),[1,4],pathology=True)
    for key,label in [('true_lumen','Actual true-lumen course'),('false_lumen','Each actual false-lumen course')]:
        add(key,label,parts('proximal_limit distal_limit continuity_and_identity complete_covered_boundary orthogonal_calibre each_compressed_or_collapsed_segment each_patent_segment each_thrombus_region each_branch_supply_connection each_lumen_communication contrast_phase_and_delayed_filling identity_and_uncovered_extent_limit'),[1,2],pathology=True)
    add('flap','Every actual intimo-medial flap',parts('proximal_limit distal_limit circumferential_attachment source_resolved_thickness each_fenestration_or_disruption each_branch_extension each_intussusception_if_present root_or_valve_interface motion_and_visibility_limit'),[1,2],pathology=True)
    add('tears','Each entry/re-entry or limited intimal tear',parts('source_resolved_site complete_local_boundary communication_to_each_lumen width_length_and_plane wall_bulge_or_undermined_edge branch_or_valve_relation each_separate_communication timepoint_and_unresolved_tears'),[0,1,4],pathology=True)
    add('intramural_haematoma','Every actual intramural haemorrhagic region',parts('proximal_limit distal_limit circumferential_extent inner_wall_interface outer_wall_interface greatest_thickness_and_plane unenhanced_attenuation_reference each_focal_intimal_disruption each_intramural_blood_pool each_branch_connection adjacent_haemorrhage comparison_and_overlap_limit'),[1,4],pathology=True)
    add('ulcerative_lesions','Each actual PAU, ULP or focal wall outpouching',parts('precise_segment atherosclerotic_background neck_or_orifice complete_boundary depth_width_and_plane length_along_aorta wall_and_lumen_communication intramural_extension branch_relation each_pseudoaneurysm_or_leak comparison_and_morphology_framework_limit'),[1,4],pathology=True)
    add('mural_thrombus','Each actual mural/luminal thrombus region',parts('complete_boundary proximal_limit distal_limit circumferential_extent lumen_interface wall_interface each_fissuration_or_crescent unenhanced_and_enhanced_references thrombosed_dissection_vs_aneurysm_limit'),[1],pathology=True)
    add('annulus','Actual aortic annulus and valve apparatus',parts('annular_plane annular_contour root_relation each_commissure_if_resolved each_attachment_or_flap_interface coverage_motion_and_functional_assessment_limit'),[0,1,3])
    for key,label,side in [('right_sinus','Right coronary sinus','right'),('left_sinus','Left coronary sinus','left'),('noncoronary_sinus','Non-coronary sinus','not_applicable')]:
        add(key,label,parts('sinus_wall contour cusp_or_leaflet_if_resolved commissural_interfaces coronary_or_adjacent_sinus_relation each_flap_or_wall_extension motion_and_unresolved_leaflet_limit'),[0,1,2],side)
    add('valve_function_if_assessed','Conditional valve haemodynamic correlation',parts('actual_available_modality regurgitation_evidence actual_functional_measurement clinical_or_echo_confirmation static_ct_and_unavailable_function_limit'),[3],modality=['CT','Ultrasound','MRI'])
    arteries=parts('ostium covered_proximal_course covered_distal_course each_actual_branch_or_variant lumen_and_wall each_dissection_extension each_stenosis_occlusion_or_thrombus source_resolved_true_false_or_shared_supply covered_distal_territory actual_phase_and_supply_uncertainty')
    for key,label,side in [('right_coronary','Right coronary artery','right'),('left_main_coronary','Left main coronary artery','left'),
        ('left_anterior_descending','Covered left anterior descending artery','left'),('left_circumflex','Covered circumflex artery','left'),
        ('brachiocephalic','Brachiocephalic artery','right'),('right_common_carotid','Right common carotid artery','right'),
        ('left_common_carotid','Left common carotid artery','left'),('right_subclavian','Right subclavian artery','right'),
        ('left_subclavian','Left subclavian artery','left'),('right_vertebral','Covered right vertebral artery','right'),
        ('left_vertebral','Covered left vertebral artery','left')]:
        add(key,label,arteries,[2],side)
    add('arch_variants','Every actual arch/neck vessel variant',parts('each_origin common_trunk_if_present aberrant_course_if_present side_and_branch_identity each_ostial_relationship each_dissection_interface unresolved_variant_or_branch_limit'),[0,2])
    for key,label in [('coeliac','Coeliac artery'),('sma','Superior mesenteric artery'),('ima','Inferior mesenteric artery')]:
        add(key,label,arteries,[2])
    for side in ('right','left'):
        for key,label in [('renal','renal artery'),('accessory_renal','each actual accessory renal artery'),
                          ('common_iliac','common iliac artery'),('internal_iliac','internal iliac artery'),
                          ('external_iliac','external iliac artery'),('common_femoral','covered common femoral artery')]:
            add(side+'_'+key,side.capitalize()+' '+label,arteries,[2],side)
    add('intercostal_spinal_supply','Actual covered intercostal and spinal-supply branches',parts('each_covered_origin side_and_level source_resolved_course lumen_supply_and_patency each_dissection_or_compromise actual_cord_perfusion_or_neurologic_evidence uncovered_supply_and_resolvability_limit'),[2])
    perfusion=parts('actual_covered_extent source_phase_and_reference each_hypoenhancing_or_infarct_region source_vascular_supply each_collateral_or_venous_context clinical_confirmation uncovered_extent_and_viability_limit')
    for side in ('right','left'):
        for key,label in [('kidney','kidney'),('cerebral_territory','covered cerebral/head-neck territory'),('upper_limb','covered upper-limb territory'),('lower_limb','covered lower-limb territory')]:
            add(side+'_'+key,side.capitalize()+' '+label,perfusion,[2],side,modality=['CT','MRI'] if key=='cerebral_territory' else ['CT'])
    for key,label in [('liver','Covered hepatic perfusion'),('spleen','Covered splenic perfusion'),
                      ('small_bowel','Every actually affected small-bowel segment'),('colon','Every actually affected colonic segment'),
                      ('myocardium','Covered myocardial perfusion'),('spinal_cord','Conditional spinal cord assessment')]:
        add(key,label,perfusion,[2],modality=['CT','MRI'] if key=='spinal_cord' else ['CT'])
    add('malperfusion_mechanisms','Each suspected malperfusion site/mechanism',parts('source_ostial_interface branch_flap_extension distal_branch_patency true_lumen_compression each_observed_organ_finding actual_dynamic_or_temporal_evidence clinical_biochemical_confirmation mechanism_and_malperfusion_syndrome_uncertainty'),[2],pathology=True)
    add('rupture_sites','Every suspected rupture or leakage site',parts('wall_site circumferential_location longitudinal_extent lumen_connection each_contrast_leak_focus actual_phase_and_reference contained_or_free_connection each_haemorrhage_endpoint unresolved_extent_and_urgent_communication'),[3],pathology=True)
    compartments=parts('complete_covered_boundary proximal_extent distal_extent aortic_or_branch_connection_if_resolved each_haemorrhage_focus source_attenuation_and_phase adjacent_structure_displacement each_communication_to_other_spaces uncovered_extent')
    for key,label in [('periaortic','Periaortic soft tissue'),('mediastinum','Covered mediastinal spaces'),
                      ('pericardium','Pericardium and actual recesses'),('retroperitoneum','Each actual retroperitoneal haemorrhage compartment'),
                      ('peritoneum','Each actual peritoneal haemorrhage compartment')]:
        add(key,label,compartments,[3],pathology=True)
    for side in ('right','left'):add(side+'_pleural_space',side.capitalize()+' pleural space',compartments,[3],side,pathology=True)
    add('haemodynamic_complications','Conditional haemodynamic/pericardial complications',parts('source_pericardial_findings actual_chamber_or_valve_relationships available_echo_or_clinical_evidence measured_function_if_available tamponade_and_static_ct_limit'),[3],modality=['CT','Ultrasound','MRI'])
    for key,label in [('pulmonary_artery','Covered pulmonary artery relationship'),('oesophagus','Covered oesophageal relationship'),
                      ('airways','Covered tracheobronchial relationships'),('venous_structures','Covered central venous relationships')]:
        add(key,label,parts('actual_covered_course each_aortic_wall_interface each_compression_or_extension each_fistula_endpoint_if_present source_resolved_lumen_or_wall unresolved_course_and_cause'),[3])
    repair=parts('operative_history_and_interval each_actual_component covered_course each_anastomosis_or_seal each_branch_reimplantation_or_stent overlap_and_attachment each_kink_migration_or_disruption each_residual_lumen_or_thrombus each_pseudoaneurysm_or_contrast_focus each_perigraft_fluid_gas_or_fistula source_phase_comparison_and_uncovered_extent')
    add('open_repair','Actual open aortic/root/arch repair if present',repair,[0,2,3,4])
    add('endovascular_repair','Actual TEVAR/other endovascular repair if present',repair,[0,2,3,4])
    add('acquisition','Actual acquisition, measurement and comparison controls',parts('patient_and_study_identity cranial_and_caudal_coverage unenhanced_availability each_contrast_phase ecg_gating_and_motion original_voxel_spacing_and_units reconstruction_kernel_and_quality orthogonal_plane_and_centreline_method each_actual_comparison_date timepoint_registration_limit source_hu_and_measurement_calibration flat_rendering_and_slab_projection_limits unacquired_functional_or_dynamic_information'),[0,1,2,3,4])
    return {'investigation_id':IDENT,'module_id':'rad.5.aorta','title':'CT acute aortic syndrome',
        'scope_status':'expanded_draft_requires_independent_anatomical_and_clinical_review','modality_scope':['CT'],
        'sources':[{'title':t,'url':u,'reviewed_at':'2026-10-06','review_status':s} for t,u,s in zip(
            ['Radiology Assistant acute aortic syndrome','ECG-gated AAS original clinical source review','ACC/AHA 2022 aortic disease guideline','STS/AATS 2022 type B dissection guideline'],URLS,
            ['effective_source_sections_reviewed','publisher_XML_and_complete_captions_reviewed','primary_classification_extract_reviewed_full_web_fetch_blocked','primary_mechanism_and_syndrome_extract_reviewed'])],
        'source_contract_sha256':digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')}),
        'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':structures,
        'expansion_rules':['Instantiate every actual lesion, lumen, communication, branch, affected territory, haemorrhage space and repair component; listed children are a known floor.',
            'Each leaf needs independently reviewed image, schematic and model evidence; source rights, generic labels and numerical controls do not establish clinical fidelity.',
            'Retain both sides, real variants, actual source coverage/phases and conditional functional/repair evidence.'],
        'source_scope_issues':['Classic Stanford assignment depends on ascending involvement, not a mandatory distal-left-subclavian tear site; name arch-only/non-A/non-B frameworks and actual anatomy.',
            'Static branch extension does not alone prove dynamic obstruction or clinically confirmed malperfusion syndrome.',
            'Pericardial fluid volume alone does not establish tamponade; CT valve morphology alone does not establish regurgitant function.',
            'IMH, limited tears and ulcerative features may overlap; a nonvisualised flap does not prove absence of an intimal communication.',
            'Primary guideline extracts are not full contemporary multidisciplinary guideline review; independent source/clinical reconciliation remains required.',
            'Flat MIP/MPR/VR figures are not supplied voxel volumes, registered geometry, complete branch models or calibrated measurements.'],
        'functional_evidence_requirements':['Calibrated sizes require original source, orthogonal planes and named measurement convention.',
            'Malperfusion, valve dysfunction and haemodynamic consequences require actual imaging plus appropriate clinical/functional evidence.',
            'Suspected acute aortic syndrome, rupture or branch malperfusion requires immediate communication; unverified normal presets do not replace assessment.'],
        'clinical_validation_status':'draft_requires_cardiovascular_radiologist_and_aortic_team_review'}

if __name__=='__main__':
    item=build();path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    data['investigations']=[i for i in data['investigations'] if i['investigation_id']!=IDENT]+[item]
    data['scope']['catalog_investigation_ids']=[i['investigation_id'] for i in data['investigations']]
    path.write_text(json.dumps(data,indent=2)+'\n')
    print(len(item['structures']),'groups;',len(requirements_for(item)),'leaves;',len(requirements_for(item))*3,'representation obligations')
