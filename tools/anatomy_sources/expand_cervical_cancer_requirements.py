#!/usr/bin/env python3
"""Expand actual cervical MRI reporting anatomy without granting fine-layer coverage."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_msk_fidelity import requirements_for
from tools.check_radiology_fidelity import digest
INV='ra.mri-cervical-cancer'
SOURCES=['https://pmc.ncbi.nlm.nih.gov/articles/PMC10605640/','https://pmc.ncbi.nlm.nih.gov/articles/PMC10886638/','https://doi.org/10.1007/s00330-020-07632-9','https://radiologyassistant.nl/abdomen/unsorted/mr-in-cervical-cancer-1']
def build():
 ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];guide=copy.deepcopy(ref['reporting']);groups=[]
 whole='actual_covered_identity_and_extent source_origin_endpoints_or_boundaries adjacent_tissue_or_organ_interface source_resolution_unresolved_or_unacquired_extent'
 layer='actual_named_site_and_extent source_inner_and_outer_boundaries thickness_or_explicitly_unresolved_layer adjacent_layer_lumen_or_lesion_interface source_resolution_and_uncertainty'
 lesion='each_actual_lesion_identity_site_and_extent source_signal_or_material_observation source_outer_and_internal_boundaries adjacent_organ_layer_lumen_or_vessel_interface source_measurement_plane_scale_and_uncertainty source_unresolved_or_unacquired_extent'
 def add(key,name,parts,indices,side='midline',pathology=False,condition=None):
  prefix='cervical_cancer.'+key;groups.append({'id':prefix,'name':name,'laterality':side,'tissue_class':'cervical_uterine_vaginal_parametrial_urinary_bowel_vascular_nodal_or_covered_staging_structure','modality_scope':['MRI'],'required_parts':[{'id':prefix+'.'+p,'name':p.replace('_',' ')} for p in parts.split()],'report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in indices],'walkthrough_step_indices':indices,'source_urls':SOURCES,'requirement_basis':'effective_full_reporting_contract_and_primary_cervical_MRI_staging_anatomy','requires_site_instantiation':True,'context_requirements':{'purpose':'pathology_example' if pathology else 'anatomical_reference'},'condition':condition or 'Instantiate for each actually covered/reported site, side, lesion and interface. Preserve missing or unresolved source boundaries. Parent organs, selected source figures or atlas names do not approve separated fine tissues.'})
 for site in ['cervical_canal','external_cervical_os','internal_cervical_os','anterior_cervical_lip','posterior_cervical_lip','ectocervix_vaginal_interface','endocervical_uterine_interface','cervical_stroma_covered_extent','uterine_body_orientation_and_whole_size','uterine_cavity','covered_endometrial_cervical_interface','covered_uterine_fundus','covered_uterine_isthmus_lower_segment']:
  add('central.'+site,site.replace('_',' ').capitalize(),whole,[0,1,7])
 for site in ['cervical_canal_content_mucosal_interface','source_visible_inner_cervical_stromal_zone','source_visible_outer_low_signal_stromal_ring','outer_cervical_stromal_parametrial_interface','covered_uterine_endometrium','covered_uterine_junctional_zone','covered_inner_myometrium','covered_outer_myometrium_serosal_interface']:
  add('central_layer.'+site,site.replace('_',' ').capitalize(),layer,[0,1,2,7])
 for site in ['each_actual_primary_tumour','each_observed_exophytic_or_endocervical_component','each_suspected_cervical_extra_stromal_extension','each_uterine_cavity_or_body_extension','each_source_observed_biopsy_or_conization_change','each_associated_leiomyoma_or_endometriosis_finding','each_actual_variant_or_postoperative_anatomical_interface']:
  add('primary.'+site,site.replace('_',' ').capitalize(),lesion,[0,1,2,7],pathology=True)
 add('planning.internal_os_distance','Actual tumour-to-internal-os measurement endpoints','source_tumour_endpoint_identity_and_evaluability internal_os_reference_identity source_plane_method_and_scale source_measurement_uncertainty',[1,7])
 add('planning.whole_uterine_size','Whole uterine size in actual acquisition','actual_uterine_extent_and_orientation maximal_and_orthogonal_source_axes source_plane_method_and_scale source_unacquired_or_unresolved_extent',[0,1,7])
 for side in ['left','right']:
  for site in ['parametrial_cervical_attachment','covered_parametrial_fat_and_fascial_interface','covered_cardinal_paracervical_tissue','sacrouterine_uterosacral_ligament_origin','covered_sacrouterine_uterosacral_course','parametrial_vessel_interface','parametrial_ureter_interface']:
   add(side+'.parametrial.'+site,side.capitalize()+' '+site.replace('_',' '),whole,[2],side)
  for site in ['covered_internal_obturator','covered_levator_ani','covered_piriformis','covered_pelvic_sidewall_fascial_interface','covered_iliac_vessel_interface']:
   add(side+'.sidewall.'+site,side.capitalize()+' '+site.replace('_',' '),whole,[4],side)
  for site in ['covered_common_iliac_vessel','covered_internal_iliac_vessel','covered_external_iliac_vessel','source_resolved_parametrial_vessel']:
   add(side+'.vascular.'+site,side.capitalize()+' '+site.replace('_',' '),whole,[2,4,6],side)
  for site in ['covered_proximal_ureter','pelvic_ureter','distal_ureter','ureteric_orifice','covered_renal_pelvis','covered_renal_calyces']:
   add(side+'.urinary.'+site,side.capitalize()+' '+site.replace('_',' '),whole,[4,5],side)
  for site in ['ureter_lumen_wall_interface','ureter_outer_wall_periureteral_interface']:
   add(side+'.urinary_layer.'+site,side.capitalize()+' '+site.replace('_',' '),layer,[4],side)
  for site in ['each_parametrial_or_uterosacral_extension','each_vascular_encasement_or_adjacent_interface','each_pelvic_sidewall_extension_or_proximity','each_ureteric_obstruction_or_alternative_cause','each_covered_renal_collecting_system_obstruction']:
   add(side+'.lesion.'+site,side.capitalize()+' '+site.replace('_',' '),lesion,[2,4,5],side,True)
  for station in ['obturator','internal_iliac','external_iliac','common_iliac','inguinal']:
   add(side+'.node_station.'+station,side.capitalize()+' actually covered '+station.replace('_',' ')+' station',whole,[6],side)
   add(side+'.node.'+station,side.capitalize()+' each actual suspicious '+station.replace('_',' ')+' node',lesion,[6],side,True)
 for site in ['anterior_vaginal_fornix','posterior_vaginal_fornix','left_vaginal_fornix','right_vaginal_fornix','upper_vaginal_extent','lower_third_vaginal_relationship','covered_vaginal_introitus','vesicovaginal_interface','rectovaginal_interface']:
  add('vaginal.'+site,site.replace('_',' ').capitalize(),whole,[3,5])
 for site in ['anterior_vaginal_wall','posterior_vaginal_wall','left_vaginal_wall','right_vaginal_wall','vaginal_lumen_wall_interface','vaginal_outer_wall_adjacent_tissue_interface']:
  add('vaginal_layer.'+site,site.replace('_',' ').capitalize(),layer,[3,5])
 for site in ['bladder_covered_extent','bladder_posterior_wall_tumour_interface','bladder_base_trigone','covered_rectum','rectal_anterior_wall_tumour_interface','covered_adjacent_bowel_segment','each_other_actually_reported_adjacent_organ']:
  add('adjacent.'+site,site.replace('_',' ').capitalize(),whole,[5])
 for organ in ['bladder','rectum']:
  for tissue in ['source_resolved_mucosal_luminal_interface','submucosa_or_explicitly_unresolved_interface','muscular_wall','outer_wall_adjacent_tissue_interface']:
   add('adjacent_layer.'+organ+'.'+tissue,organ.capitalize()+' '+tissue.replace('_',' '),layer,[5])
  for site in ['each_actual_contact_interface','each_suspected_wall_or_mucosal_extension','each_oedema_or_other_tumour_mimic','each_actual_luminal_abnormality_or_fistula']:
   add('adjacent_lesion.'+organ+'.'+site,organ.capitalize()+' '+site.replace('_',' '),lesion,[5],pathology=True)
 for site in ['presacral_nodal_station','covered_paraaortic_below_renal_veins','covered_paraaortic_above_renal_veins','actual_renal_vein_level_reference','covered_other_distant_nodal_station','covered_peritoneal_surface','covered_distant_organ_or_skeletal_site']:
  add('spread.'+site,site.replace('_',' ').capitalize(),whole,[6])
 for site in ['each_actual_suspicious_presacral_node','each_actual_suspicious_paraaortic_node_with_level','each_actual_suspicious_other_distant_node','each_observed_peritoneal_focus','each_actual_covered_distant_organ_or_skeletal_lesion']:
  add('spread_lesion.'+site,site.replace('_',' ').capitalize(),lesion,[6],pathology=True)
 for site in ['each_actual_residual_or_recurrent_tumour_concern','each_source_observed_fibrotic_or_oedematous_interface','each_observed_post_treatment_organ_wall_or_fistula_change','each_actual_matched_pre_post_treatment_lesion_or_site']:
  add('response.'+site,site.replace('_',' ').capitalize(),lesion,[7],pathology=True,condition='Required for the actual supplied treatment/comparison examination. Preserve acquired timing, matching method, source signal and each uncertain interface; no published pre/post example is registered to another patient or proves microscopic complete response.')
 return {'investigation_id':INV,'module_id':'rad.5.uterine-mr','title':'Cervical Cancer — MRI staging and supplied follow-up','scope_status':'expanded_draft_requires_independent_specialist_pelvic_MRI_and_clinical_review','modality_scope':['MRI'],'sources':[{'title':'Primary cervical MRI/source scope','url':u,'reviewed_at':'2026-10-10','review_status':'primary_reporting_anatomy_and_effective_assigned_scope_reconciled'} for u in SOURCES],'source_contract_sha256':digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']}),'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':groups,'expansion_rules':['Clinical MRI, schematic and 3D obligations remain distinct for every actual side, fine layer, lesion and measured interface. Whole source figures and gross atlas meshes do not approve every boundary.','Source-visible MRI zones, histological tissues and morphological surfaces are distinct. Preserve age/treatment/source resolution and explicitly unresolved fine layers.','Conditional nodes, distant sites and response findings require actual site instantiation and acquisition, not invented complete extent.'], 'source_scope_issues':['Microscopic stage IA and proven organ mucosal invasion require their actual clinical/pathological evidence; MRI cannot manufacture those inputs.','FIGO/TNM versions and publication descriptions must remain explicit; no automatic stage, treatment eligibility or source threshold is supplied.','Original HRA source surfaces have source-level provenance conflicts/shared uterine-wall triangles and are not independently approved fine cervical/uterine layers or patient registration.','Actual acquisition planning and anatomical variants are separate from demonstrated tumour extension. Missing coverage and uncertain response/nodal findings remain unknown.'],'functional_evidence_requirements':['Obstruction, staging, fertility planning and response require their actual acquisition/clinical context. Static source shape or publication images cannot independently establish function or patient treatment.','Each measurement requires real source endpoints, plane, scale and uncertainty; published display pixels and atlas coordinates are not patient calibration.'],'clinical_validation_status':'draft_requires_specialist_pelvic_MRI_and_gynaecological_oncology_review'}
def main():
 p=ROOT/'data/radiology/non-msk-structure-requirements.json';d=json.loads(p.read_text());item=build();d['investigations']=[i for i in d['investigations'] if i['investigation_id']!=INV]+[item];d['scope']['catalog_investigation_ids']=[i['investigation_id'] for i in d['investigations']];d['updated_at']='2026-10-10';p.write_text(json.dumps(d,indent=2)+'\n');leaves=list(requirements_for(item));print(len(item['structures']),'groups;',len(leaves),'fine leaves;',len(leaves)*3,'representation obligations; no clinical approval.')
if __name__=='__main__':main()
