#!/usr/bin/env python3
"""Expand actual prostate reporting anatomy; never infer complete media coverage."""
import copy
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for

INV='ra.mri-prostate';DATE='2026-10-08'
ACR='https://edge.sitecorecloud.io/americancoldf5f-acrorgf92a-productioncb02-3650/media/ACR/Files/RADS/PI-RADS/PIRADS-2019.pdf'
TCIA='https://www.cancerimagingarchive.net/collection/prostate-mri-us-biopsy/'
PARTS=['complete_native_extent','outer_and_inner_tissue_interfaces','actual_internal_components','proximal_distal_and_adjacent_relationships','each_source_resolved_boundary','unresolved_or_uncovered_extent']
LOOKS=[
 'Review the complete acquired gland, base/mid/apex, separate PZ/TZ/CZ and anterior fibromuscular stroma, periurethral tissue, haemorrhage and BPH components. Record actual dimensions, volume method, dated PSA and source quality; unavailable tissue is unassessed.',
 'Map every actually reported finding across all involved native sectors and levels, with complete components, margins, maximum dimension, source series/plane and neighbours. PI-RADS v2.1 has41 regions:38 prostate, two seminal-vesicle and one external-sphincter regions; the diagram is an idealized map, not patient geometry.',
 'Assess actual T2, acquired or calculated high-b DWI, ADC and any DCE separately, with quality, ROI, calibration, timing and motion limits. Apply applicable v2.1 sequence/zone rules only after adequate observations; a source Likert score, ROI, size alone or uncalibrated ADC value does not supply a current assessment.',
 'Trace each source-resolved lesion/glandular-surface interface, TZ/PZ pseudocapsule, anterior/apical gaps, bilateral nerves/vessels, seminal vesicles and ducts, bladder neck, urethra, external sphincter, fascia and rectal interfaces. Record actual contact and direct extension separately; the prostate has no complete true capsule.',
 'Review every acquired pelvic node and basin, cortex/hilum and vascular relationship, imaged bones, bladder, rectum and other reported pelvic findings. Preserve actual field coverage, clinical/tissue and treatment evidence; no unacquired nodal/bone survey or whole-gland shape supplies a negative result or current stage.'
]

def build_draft(ref,node):
    guide=copy.deepcopy(ref['reporting']);node=copy.deepcopy(node)
    guide['reviewed_at']=DATE
    guide['protocol'] += ['Retain native sequence/plane, source spatial sampling, examination extent and quality. Distinguish acquired diffusion, producer-derived ADC/calculated DWI, source DCE and actual contrast timing; shared frame identifiers do not establish every registration or fine-tissue resolution.']
    guide['sources']=[s for s in guide['sources'] if s.get('url')!=TCIA]+[{'title':'TCIA original prostate MRI/US biopsy source and annotation limits','url':TCIA}]
    guide['pitfalls'] += ['Prostate outer fibromuscular boundary and TZ/PZ pseudocapsule are distinct and neither is a complete true histological capsule.','The official41-sector map is an idealized localization aid. Each source patient and every actual lesion, route, boundary and variant requires its own geometry.','Published suspicious target ROIs and source Likert-like scores are not proven tumour extent or automatic current PI-RADS v2.1 assessments. Unavailable ADC calibration, native high-b data or DCE remain explicit.']
    guide['measurements'].append({'name':'Each actual source component and interface','method':'Record the supplied native plane/sequence, acquisition axes, calibration, each component/total extent and actual adjacent structures. Separate source measurements and dated clinical/pathological information.','pitfall':'Voxel pitch, a source ROI, sector map or complete organ outline does not establish microscopic interfaces, complete tumour extent or current stage.'})
    removed=sum(bool(s.get('normal')) for s in node['steps'])
    for index,(step,look) in enumerate(zip(node['steps'],LOOKS)):
        guide['checklist'][index]['detail']=look
        guide['template_sections'][index]['body'] += '\n\nActual acquired source components/interfaces and uncovered extent [ ]; separate clinical/tissue correlation [ ].'
        step['look']=look;step['detail']=look;step['normal']={};step['parts']=[]
        step['measurements']=list(dict.fromkeys(step.get('measurements',[])+['Each actual source component and interface']))
    node['steps'][1]['findings'][0]='Lesion [ID/index status]: side [ ]; zone [ ]; level and all involved sectors [ ]; size and measurement plane/sequence [ ]; T2/DWI/DCE observations and quality [ ]; unresolved source/tissue correspondence [ ].'
    node['steps'][2]['tip']='Use the complete applicable v2.1 sequence-score definitions and zonal combination rules. Size of15mm alone does not assign category5; the required suspicious morphology or specified definite invasive behaviour must also be assessed. Missing/limited sequences remain identified.'
    node['model']={'family':'prostate','reporting_aim':'Partial schematic orientation only. It does not supply patient-specific zonal, fibromuscular/pseudocapsular, ductal, neurovascular, seminal-vesicle, sphincter, nodal, bone or lesion-extension geometry. Original source gland/ROI references are separately scoped; full reporting coverage remains unverified.'}
    structures=[]
    def add(key,name,side,steps,sector=False,pathology=False):
        ident='prostate.'+key
        structures.append({'id':ident,'name':name,'laterality':side,'tissue_class':'prostate_reporting_region_tissue_route_node_or_pathological_interface','modality_scope':['MRI'],'required_parts':[{'id':ident+'.'+part,'name':part.replace('_',' ')} for part in PARTS],'walkthrough_step_indices':steps,'report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in steps],'source_urls':[s['url'] for s in guide['sources']],'requires_site_instantiation':True,'requires_independent_source_layer_review':True,'requirement_basis':'all_effective_prostate_reporting_anatomy_and_actual_source_interfaces','condition':'Instantiate every actual reported side, level, branch, node, tissue layer, lesion, device or treated site and its resolved boundaries. Missing, microscopic or uncovered tissue remains unproven; modality permission is not resolution or clinical/pathological identity.','context_requirements':{'purpose':'pathology_example' if pathology else 'anatomical_reference'},'official_idealized_sector_region':sector})
    for side in ['right','left']:
        for level in ['base','midgland','apex']:
            for zone in ['PZ_anterior','PZ_posteromedial','PZ_posterolateral','TZ_anterior','TZ_posterior','AS']:
                add('sector.'+side+'_'+level+'_'+zone.lower(),f'{side} {level} {zone}',side,[0,1,2,3],True)
        add('sector.'+side+'_CZ',side+' central-zone sector',side,[0,1,2,3],True)
        add('sector.'+side+'_SV',side+' seminal-vesicle region',side,[3],True)
        for tissue in ['peripheral_zone_actual_full_extent','transition_zone_actual_full_extent','central_zone_and_ejaculatory_duct_surroundings','anterior_fibromuscular_stroma_actual_extent','outer_fibromuscular_boundary_and_anterior_apical_gaps','TZ_PZ_pseudocapsule_and_compressed_tissue','periurethral_glands_and_muscle','each_actual_BPH_nodule_and_internal_components','each_actual_neurovascular_bundle_and_cavernous_nerve_route','each_actual_pelvic_plexus_and_prostate_nerve_branch','each_actual_prostatic_arterial_branch_and_wall_lumen','each_actual_prostatic_venous_branch_and_plexus','seminal_vesicle_wall_lumen_and_each_component','ejaculatory_duct_wall_lumen_and_course','vas_deferens_ampulla_and_duct_interface','periprostatic_fascia_and_rectoprostatic_interface','puboprostatic_ligament_and_anterior_attachment']:
            add(side+'_'+tissue,side+' '+tissue.replace('_',' '),side,[0,1,3],False,'BPH' in tissue)
        for basin in ['obturator','internal_iliac','external_iliac','common_iliac','presacral','perirectal','inguinal_when_acquired_or_reported']:
            add(side+'_'+basin+'_each_actual_node',side+' '+basin+' each actual node',side,[4])
    add('sector.external_urethral_sphincter','External urethral sphincter region','midline',[3],True)
    for key in ['complete_gland_outline_and_each_dimension','bladder_neck_and_internal_urethral_sphincter','prostatic_urethra_proximal_and_distal_segments','verumontanum_and_each_duct_opening','membranous_urethra_and_external_sphincter_components','rectal_wall_lumen_and_anterior_interface','urinary_bladder_wall_lumen_and_trigone','each_actual_pelvic_bone_cortex_marrow_or_lesion','each_actual_other_reported_pelvic_organ_or_finding','each_actual_source_quality_motion_or_distortion_region','each_actual_T2_diffusion_ADC_or_contrast_ROI_and_frame']:
        add(key,key.replace('_',' '),'not_applicable',[0,1,2,3,4])
    for key in ['each_actual_reported_lesion_all_components_margins_and_sectors','each_actual_separate_focus_and_intervening_tissue','each_actual_glandular_surface_contact_and_direct_EPE_interface','each_actual_seminal_vesicle_nerve_vessel_urethral_or_adjacent_extension','each_actual_haemorrhage_inflammation_cyst_or_other_mimic','each_actual_treatment_resection_reconstruction_or_device_interface','each_actual_supplied_biopsy_pathology_and_temporal_correspondence']:
        add(key,key.replace('_',' '),'not_applicable',[0,1,2,3,4],False,True)
    assert sum(s['official_idealized_sector_region'] for s in structures)==41
    item={'investigation_id':INV,'module_id':catalog.resolve(INV)['module_id'],'title':'Complete effective prostate reporting anatomy and each actual source interface','modality':'MRI','scope_type':'bilateral_zonal_localization_and_conditional_lesion_extension_pelvic_and_treatment_scope','scope_status':'expanded_draft_requires_independent_prostate_anatomical_and_clinical_review','clinical_validation_status':'draft_requires_prostate_radiologist_anatomist_and_relevant_urological_pathology_review','required_representations':['image','schematic','model'],'modality_scope':['MRI'],'sources':[{**s,'reviewed_at':DATE,'review_status':'primary_reporting_and_source_annotation_context; manual graphics not redistributed'} for s in guide['sources']],'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':structures,'expansion_rules':['All41 idealized localization regions are explicit; no sphere, sector label or whole-gland outline substitutes for their patient-specific source anatomy.','Instantiate all actually reported tissues, branches, nodes, lesions, extension interfaces and supplied treated anatomy. This explicit floor is not a closed list or a claim that every examination requires microscopic or unacquired tissue.','Preserve actual source acquisition/derived processing, quality and calibration; current suspicion, stage, histology and treatment response are separate evidence.'],'source_scope_issues':['Current schematic and original operator gland/target surfaces do not supply all reported structures or independent fine anatomical approval.','Prostate outer fibromuscular boundary and TZ/PZ pseudocapsule are not true complete capsules; anterior/apical gaps remain required.','Original source targetROI/Likert scoring cannot assign current pathology or PI-RADS2.1; MRI and US source registration remain distinct.'],'functional_evidence_requirements':['Any quantitative ADC, DCE or diffusion claim requires the actual source calibration, acquisition/derivation, native ROIs and frames/timing.','Supplied tissue results, dated PSA, biopsy or treatment evidence must remain separately identified; appearance and source-only examples do not prove current stage, response or histology.']}
    return guide,node,item,removed

def build():
    ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference']
    p=ROOT/'data/radiology/reporting-steps/abdomen.json';text=p.read_text();start=text.index('{',text.index('"'+INV+'"'));old,end=json.JSONDecoder().raw_decode(text,start)
    guide,node,item,removed=build_draft(ref,old)
    p.write_text(text[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+text[end:])
    p=ROOT/'data/radiology/investigation-overrides-non-msk.json';d=json.loads(p.read_text());d.setdefault(INV,{})['reporting']=guide;p.write_text(json.dumps(d,indent=2)+'\n')
    p=ROOT/'data/radiology/flagship-templates.json';d=json.loads(p.read_text())
    # Keep the authored comprehensive template and headings intact; add source extent/correlation fields.
    def extend(value):
        if isinstance(value,dict):
            if value.get('id')=='prostate-mri-pi-rads-21':
                for section in value['sections']:
                    if section['heading'] in ['GLAND / PSA DENSITY','LESION WORKSHEET — REPEAT FOR EACH REPORTED LESION','LOCAL EXTENT','NODES / BONES / OTHER PELVIC FINDINGS']:
                        section['body']+='\nActual acquired components/interfaces, quality and uncovered extent [ ]; separate supplied clinical/tissue correspondence [ ].'
            else:
                for child in value.values():extend(child)
        elif isinstance(value,list):
            for child in value:extend(child)
    extend(d);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
    # A reporting override would otherwise regenerate a generic template and
    # discard the authored comprehensive headings used by these steps.
    p=ROOT/'data/radiology/investigation-overrides-non-msk.json';over=json.loads(p.read_text())
    over[INV]['report_templates']=copy.deepcopy(d[catalog.resolve(INV)['module_id']]['report_templates'])
    p.write_text(json.dumps(over,indent=2,ensure_ascii=False)+'\n')
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)):value.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];item['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    p=ROOT/'data/radiology/non-msk-structure-requirements.json';d=json.loads(p.read_text());d['investigations']=[r for r in d['investigations'] if r['investigation_id']!=INV]+[item];d['scope']['catalog_investigation_ids']=[r['investigation_id'] for r in d['investigations']];p.write_text(json.dumps(d,indent=2)+'\n')
    print(len(item['structures']),'groups;41 official localization regions;',len(requirements_for(item))*3,'image/schematic/model obligations;',removed,'unsupported presets removed')

if __name__=='__main__':build()
