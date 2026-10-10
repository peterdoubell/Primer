#!/usr/bin/env python3
"""Expand the entire carotid report scope; gross envelopes never inherit wall, lesion or branch coverage."""
import copy
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_msk_fidelity import requirements_for
from tools.check_radiology_fidelity import digest

INV='ra.carotid-obstruction'
SOURCES=[
 ('Effective carotid obstruction reporting source','https://radiologyassistant.nl/neuroradiology/carotid-pathology/differentiating-carotid-pathology'),
 ('Johansson et al. 2020: CTA near-occlusion','https://pmc.ncbi.nlm.nih.gov/articles/PMC7160198/'),
 ('Johansson, Barud and Strömberg 2026: diagnostic review','https://doi.org/10.1093/esj/23969873251355158'),
 ('Acquired and conceptual arterial examples','https://pmc.ncbi.nlm.nih.gov/articles/PMC6377693/')]

def build():
 ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];guide=copy.deepcopy(ref['reporting']);groups=[]
 def add(key,name,parts,reports,side='midline',pathology=False,modalities=None,condition=None):
  prefix='carotid_obstruction.'+key
  groups.append({'id':prefix,'name':name,'laterality':side,
   'tissue_class':'carotid_vessel_wall_lumen_lesion_branch_or_acquired_interface',
   'modality_scope':modalities or ['CT','MRI','Ultrasound','Radiography'],
   'required_parts':[{'id':prefix+'.'+part,'name':part.replace('_',' ')} for part in parts.split()],
   'report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in reports],
   'walkthrough_step_indices':reports,'source_urls':[url for _,url in SOURCES],
   'requirement_basis':'effective_carotid_report_and_primary_source_anatomical_interface_scope',
   'requires_site_instantiation':True,
   'context_requirements':{'purpose':'pathology_example' if pathology else 'anatomical_reference'},
   'condition':condition or 'Instantiate separately for every actually acquired/reported side, segment, branch, lesion/component and source interface. Preserve unacquired or unresolved extent; an example or parent label does not imply complete coverage.'})
 vessel='actual_obtained_course source_origin_endpoints_and_bends source_lumen_or_unresolved_lumen outer_boundary_or_unresolved_boundary adjacent_structure_or_branch_interface source_unresolved_or_unacquired_extent'
 for side in ['right','left']:
  for segment in ['common_carotid_origin','proximal_common_carotid','mid_common_carotid','distal_common_carotid',
                  'bifurcation_and_bulb','proximal_cervical_ICA','mid_cervical_ICA','distal_cervical_ICA',
                  'covered_petrous_ICA','covered_cavernous_ICA','covered_clinoid_ICA','covered_supraclinoid_ICA',
                  'external_carotid_origin','covered_external_carotid_trunk']:
   add(side+'.vessel.'+segment,side.capitalize()+' '+segment.replace('_',' '),vessel,[0,1,2,3,4],side)
  for branch in ['superior_thyroid','ascending_pharyngeal','lingual','facial','occipital','posterior_auricular',
                 'maxillary','superficial_temporal','ophthalmic','posterior_communicating','anterior_choroidal',
                 'ACA_A1','covered_ACA_A2_or_other_ACA_branch','MCA_M1','covered_MCA_M2_or_other_MCA_branch',
                 'PCA_P1','covered_PCA_P2_or_other_PCA_branch','actual_other_carotid_or_collateral_branch']:
   add(side+'.branch.'+branch,side.capitalize()+' covered '+branch.replace('_',' '),vessel,[0,3,4],side,
       condition='Required only for actual obtained/reported branches and territories. Identify the actual origin, course and source endpoints; do not invent a complete vessel from a cropped parent or assume a variant branch is present/absent.')
  for layer in ['intima','media','adventitia','lumen_wall_interface','outer_wall_adjacent_tissue_interface']:
   add(side+'.wall.'+layer,side.capitalize()+' arterial '+layer.replace('_',' '),
       'actual_obtained_site_and_extent source_boundary_or_explicitly_unresolved_layer thickness_or_unresolved_thickness adjacent_lumen_layer_or_tissue_interface lesion_flap_or_haematoma_interface source_resolution_limit', [0,1,3],side)
  for site in ['every_actual_stenosis','every_actual_plaque','every_actual_occlusion','every_actual_thrombus',
               'every_actual_dissection','every_actual_pseudoaneurysm_or_aneurysm','every_actual_web_or_other_vasculopathy']:
   add(side+'.lesion.'+site,side.capitalize()+' '+site.replace('_',' '),
       'each_actual_identity_site_and_extent source_outer_and_internal_boundaries residual_lumen_interface host_wall_interface branch_or_adjacent_tissue_interface source_confidence_unresolved_or_unacquired_extent',[0,1,2,3,4],side,True)
  for component in ['source_calcific_plaque_component','source_noncalcific_plaque_component','source_haemorrhagic_wall_or_plaque_component',
                    'source_flap_or_membrane','source_true_channel','source_false_channel','source_haematoma',
                    'source_thrombus_or_mobile_appearing_component','source_aneurysm_neck_or_sac']:
   add(side+'.lesion_component.'+component,side.capitalize()+' '+component.replace('_',' '),
       'actual_component_identity_and_extent source_material_or_signal_observation source_internal_and_external_interfaces adjacent_lumen_wall_or_branch_relation source_unresolved_or_unacquired_extent',[0,1,2,3],side,True)
  for role in ['minimum_lumen_measurement_site','valid_distal_ICA_reference_site','distal_ICA_calibre_comparison',
               'ipsilateral_ECA_comparison','near_occlusion_with_full_collapse_extent','near_occlusion_without_full_collapse_extent',
               'occlusion_stump','distal_reconstitution_site','every_actual_tandem_intracranial_lesion']:
   add(side+'.assessment.'+role,side.capitalize()+' '+role.replace('_',' '),
       'actual_source_site_and_extent source_lumen_wall_or_unresolved_interface actual_plane_reference_and_quality comparator_identity_and_geometry source_acquisition_timing_or_flow_limit unassessed_or_unresolved_extent',[1,2,4],side,True)
  for interface in ['covered_jugular_or_other_venous_interface','covered_carotid_space_or_sheath_interface',
                    'covered_neural_or_sympathetic_interface','covered_bone_or_skull_base_interface',
                    'actual_other_adjacent_tissue_or_mass_interface']:
   add(side+'.adjacent.'+interface,side.capitalize()+' '+interface.replace('_',' '),
       'actual_acquired_extent separate_arterial_and_adjacent_tissue_boundary intervening_plane_or_unresolved_plane source_lesion_contact_displacement_or_supported_extension_interface source_unresolved_or_unacquired_extent',[0,3,4],side)
 for key in ['covered_aortic_arch_and_branch_variant','covered_brachiocephalic_trunk','covered_anterior_communicating_connection',
             'covered_basilar_or_vertebral_comparison','each_actual_collateral_pathway','each_actual_variant_or_congenital_calibre_pattern',
             'each_actual_prior_repair_or_device_site','each_actual_source_comparison_timepoint']:
  add(key,key.replace('_',' '),
      'actual_case_site_and_obtained_extent original_source_boundaries_or_unresolved_interfaces actual_branch_or_connection_identity source_supported_variant_repair_or_comparison_relation unacquired_or_unresolved_extent',[0,1,2,3,4])
 return {'investigation_id':INV,'module_id':ref['investigation']['module_id'],
  'title':'Complete acquired carotid lumen wall lesion branch comparison and collateral scope',
  'scope_status':'expanded_draft_requires_independent_anatomical_and_vascular_imaging_review',
  'clinical_validation_status':'draft_requires_neuroradiologist_vascular_imaging_and_relevant_clinical_review',
  'modality_scope':['CT','MRI','Ultrasound','Radiography'],'required_representations':['image','schematic','model'],
  'sources':[{'title':title,'url':url,'reviewed_at':'2026-10-10','review_status':'report_scope_and_primary_source_review_no_implicit_image_or_anatomy_approval'} for title,url in SOURCES],
  'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':groups,
  'source_contract_sha256':digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']}),
  'expansion_rules':['Instantiate every actual site, side, branch, lesion/component and reported field separately; this draft list is a floor, not a complete patient denominator.',
   'Parent arterial labels and gross atlas surfaces do not inherit lumen/wall, plaque component, dissection channel, distal reference or collateral completeness.',
   'Native CT annotations, curated source objects, publication cases and current examinations remain separate; no cross-case registration, normality or pathological diagnosis is fabricated.',
   'Cropped or unacquired vessel territories remain explicit, including limited ultrasound fields and source-CT endpoints. Reference caps are not anatomical endpoints.'],
  'source_scope_issues':['Bilateral full arterial/branch courses and fine lumen-wall/lesion interfaces remain unapproved; only supplied source extent is inspectable.',
   'Distal ICA reduction requires source interpretation with proximal disease, comparisons and variants; small calibre alone is not a near-occlusion diagnosis.',
   'Functional haemodynamics, microscopic tissue identity and clinical effects are not generated geometric anatomy components.'],
  'functional_evidence_requirements':['Actual contrast phases, complete acquired series and supplied timing/flow evidence are required to separate non-opacification, slow filling, true occlusion and pseudo-occlusion.',
   'Actual Doppler sample site, beam/flow angle, waveform and velocity scale, acquisition quality and named criteria are required for ultrasound grading; CTA/MRA shape or a still illustration does not substitute.',
   'NASCET assessment requires a suitable actual measured minimum lumen and disease-free distal reference; withhold a routine percentage for a reduced/collapsed or otherwise invalid reference.',
   'Patency, collateral flow, cerebral perfusion, mobility and neurological/voice function require appropriate supplied acquisitions and clinical evidence; static shape does not prove them.']}

def update():
 item=build();path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
 data['investigations']=[r for r in data['investigations'] if r['investigation_id']!=INV]+[item]
 data['scope']['catalog_investigation_ids']=[r['investigation_id'] for r in data['investigations']]
 path.write_text(json.dumps(data,indent=2)+'\n');n=len(requirements_for(item))
 print(len(item['structures']),'carotid groups;',n,'component requirements;',n*3,'representation obligations; no approval granted')

if __name__=='__main__':update()
