#!/usr/bin/env python3
"""Expand every reported thyroid/nodal interface while preserving source and clinical uncertainty."""
import copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.check_msk_fidelity import requirements_for
ROOT=Path(__file__).resolve().parents[2];IDENT='ra.ultrasound-thyroid'
URLS=['https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/TI-RADS','https://radssupport.acr.org/support/solutions/articles/11000071474-acr-ti-rads-faq','https://radiologyassistant.nl/head-neck/ti-rads/ti-rads','https://gravitas.acr.org/PPTS/DownloadPreviewDocument?DocId=157&ReleaseId=2']
def update():
    ref=catalog.detail(Curriculum(),catalog.resolve(IDENT))['radiology_reference'];guide=copy.deepcopy(ref['reporting'])
    guide.update(reviewed_at='2026-10-07',protocol=['Record actual ultrasound planes, coverage, transducer/sampling, gain/focus, artifacts, Doppler settings if acquired, calibration and available comparisons. Unsurveyed retrosternal/deep neck extent remains unassessed.',
        'Inventory actual gland/background and nodules using stable source identities. Adult ACR TI-RADS category is distinct from a clinical action; retain supplied biopsy, treatment, risk context and applicable framework/version.'],
        checklist=[{'label':label,'detail':detail} for label,detail in [
            ('Background','Describe both actual lobes, isthmus, encountered variants/ectopic or treated tissue, acquired dimensions, parenchyma and coverage limits.'),
            ('Nodule identification','Inventory every actual relevant nodule/component; stable identity, side/site, source orthogonal dimensions and comparison. Selected index nodules do not represent all obtained anatomy.'),
            ('Five features','Use source-resolved composition, echogenicity against actual references, transverse shape, margin and echogenic foci. Name ACR framework; unavailable features remain unresolved, not zero-point findings.'),
            ('Extension','Trace each actual nodule-to-thyroid-boundary and adjacent tissue interface, with source confidence. Distinguish abutment/bulging from supported gross extension; microscopic invasion is not established by ultrasound.'),
            ('Nodes','Record actually surveyed central/lateral/other nodal regions, named map and each relevant node source morphology, dimensions and adjacent interfaces. Node evaluation is separate from nodule TI-RADS.'),
            ('Recommendation','State category and measurement separately from action. Use actual cytology/biopsy, prior treatment, clinical risk, suspicious nodes/extension and appropriate population-specific pathway.')]],
        pitfalls=['A generic thyroid/node model or published selected frame does not represent every actual nodule, tissue boundary, node or acquired neck extent.',
            'Do not call all comet-tail artefacts zero-point foci: use the actual ACR lexicon and source location, size and surrounding component; unresolved foci/shadowed tissue remain unresolved.',
            'Vascularity, motion, compressibility and vessel patency require actual corresponding acquisitions; static echotexture or colour labels are not functional measurements.',
            'Biopsy-proven status and management context are supplied clinical evidence. Growth does not make the routine unbiopsied-nodule pathway automatically applicable to a previously biopsied nodule.'])
    guide['sources']=list(dict(title=title,url=url) for title,url in zip(['ACR TI-RADS resources','ACR current TI-RADS FAQ','RA source TI-RADS descriptors','ACR thyroid/parathyroid ultrasound practice parameter'],URLS))
    guide['classification']['applicability']='Adult acquired thyroid-nodule ultrasound features using the named ACR framework/version. Management additionally requires applicable population, supplied biopsy and clinical risk; suspicious nodes/extension and PET-avid/pediatric contexts need the appropriate separate pathway.'
    guide['measurements'][0].update(method='For each actual relevant nodule record stable site/identity, source transverse and longitudinal planes, three orthogonal edge-to-edge dimensions, calibrated units and unresolved borders. Maximum acquired diameter is a size prompt, not all native geometry.',pitfall='Do not mix nodules, oblique planes, different acquisition/edge conventions or unresolved shadowed boundaries across comparisons.')
    guide['template_sections'][0]['body']='Actual right/left lobes/isthmus and encountered variant/ectopic/treated tissue [ ]; acquired dimensions/parenchyma [ ]; actual Doppler if obtained [ ]; technique, surveyed extent and unassessed deep/retrosternal anatomy [ ].'
    guide['template_sections'][1]['body']='Each actual relevant nodule/component identity, side/site [ ]; source dimensions/calibration/planes [ ]; comparison of the same nodule if available [ ]; unresolved components or margins [ ].'
    guide['template_sections'][2]['body']='Actual source composition/echogenicity/reference tissue/transverse shape/margin/echogenic foci [ ]; evaluability of every feature [ ]; explicitly applicable ACR scores, total and category if supported [ ]; unresolved features and differential [ ].'
    guide['template_sections'][3]['body']='Each source nodule-to-thyroid-boundary/adjacent muscle/tracheal/esophageal/vascular/other tissue interface [ ]; abutment/bulging versus supported extension and confidence [ ]; each actually surveyed node/side/descriptive site/named map/dimensions/morphology [ ]; unassessed interfaces and extent [ ].'
    guide['template_sections'][4]['body']='Supplied prior cytology/biopsy/treatment and dates [ ]; actual same-nodule interval comparison [ ]; category/size and applicable population/risk context [ ]; individualised action/interval and reason [ ]; unavailable evidence [ ].'
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());data.setdefault(IDENT,{})['reporting']=guide;path.write_text(json.dumps(data,indent=2)+'\n')
    path=ROOT/'data/radiology/reporting-steps/head-neck.json';text=path.read_text();start=text.index('{',text.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(text,start)
    node['model']={'family':'neck','reporting_aim':'Partial neck orientation only. This schematic does not supply every actual thyroid variant, nodule solid/fluid/calcific component, capsule/internal tissue boundary, node cortex/hilum or extrathyroidal vascular/airway/neural interface. Source ultrasound, calibration, acquired function and unassessed anatomy remain separate.'}
    looks=['Inspect actual lobe/isthmus planes and encountered variant/ectopic/treated tissue, gland boundaries and source parenchyma. Record actual Doppler acquisition and sampling/coverage limits.',
        'Identify every actual relevant nodule and each internal component; source transverse and longitudinal planes, axes/edge convention, measurement calibration and same-case comparison.',
        'Assess each source-resolved solid/fluid/spongiform component, reference gland/muscle echogenicity, transverse shape, margin and each foci type. Record shadowing and unavailable tissue/feature information.',
        'Trace actual thyroid-boundary and adjacent strap muscle, airway, esophageal, vascular and other source interfaces; survey actual named central/lateral/other nodal regions and each relevant node. Record confidence and unassessed deep extent.',
        'Use acquired feature scores and maximum diameter only in the applicable framework. Supplied prior biopsy/cytology, risk, treatment, PET findings, pediatric context and suspicious nodes/extension require their appropriate individualised pathway.']
    tips=['Do not preset a normal-sized homogeneous gland or normal flow without actual adequate acquisition.',
        'Stable identifiers and comparable calibrated source planes are required; a selected index image does not inventory every nodule.',
        'Comet-tail scoring depends on the actual source foci and ACR descriptors; not all reverberation is a zero-point benignity finding.',
        'Abutment or bulging alone is not proof of gross invasion; unresolved or microscopic extent and unsurveyed nodes are not absent disease.',
        'Previously biopsied nodules need management informed by biopsy results; do not apply an automatic ACR action simply because growth is reported.']
    for i,step in enumerate(node['steps']):step.update(normal={},look=looks[i],tip=tips[i],findings=['Actual acquired '+step['label'].lower()+' findings [ ]; source/identity/extent [ ]; uncertainty and unavailable evidence [ ].'])
    path.write_text(text[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+text[end:])
    for v in vars(catalog).values():
        if callable(getattr(v,'cache_clear',None)):v.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(IDENT))['radiology_reference'];structures=[]
    def add(key,parts,reports,steps,side='not_applicable',pathology=False):
        prefix='thyroid.'+side+'_'+key
        structures.append({'id':prefix,'name':side.replace('_',' ').capitalize()+' '+key.replace('_',' '),'tissue_class':'thyroid_nodal_component_or_actual_adjacent_interface','required_parts':[{'id':prefix+'.'+p,'name':p.replace('_',' ').capitalize()} for p in parts.split()],
            'laterality':side,'modality_scope':['Ultrasound'],'condition':'Instantiate every actual covered gland, variant, relevant nodule/node/component, tissue boundary and encountered lesion/treatment interface. A selected index example or generic model does not close other sites. Unacquired/unresolved deep, microscopic or internal tissue extent remains missing; no function or histology is invented as geometry.',
            'requirement_basis':'effective_thyroid_ultrasound_reporting_scope','report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in reports],'walkthrough_step_indices':steps,'source_urls':URLS,'requires_site_instantiation':True,'context_requirements':{'purpose':'pathology_example' if pathology else 'anatomical_reference'}})
    gland='full_actual_obtained_extent superior_mid_inferior_regions anterior_posterior_medial_lateral_boundaries actual_source_parenchymal_components true_capsular_and_perithyroidal_interface encountered_variant_or_treated_tissue source_unresolved_extent'
    nodule='every_actual_nodule_identity_and_extent each_solid_fluid_spongiform_or_other_component each_resolved_internal_boundary source_resolved_margin_and_capsular_interface every_punctate_macrocalcific_rim_or_other_foci_component source_local_transverse_longitudinal_geometry_and_axes adjacent_gland_tissue_interface shadowed_unresolved_or_uncovered_extent'
    adjacent='full_actual_obtained_component_extent each_resolved_surface_and_tissue_boundary nodule_or_node_contact_displacement_extension_interface every_encountered_variant_lesion_or_treatment_relation unresolved_wall_internal_or_uncovered_extent'
    for side in ['left','right']:
        add('thyroid_lobe',gland,[0,1,2,3],[0,1,2,3],side)
        for region in ['superior_pole_nodules','mid_lobe_nodules','inferior_pole_nodules','exophytic_or_unassigned_nodules']:add(region,nodule,[1,2,3,5],[1,2,3,4],side,True)
        for region in ['actual_central_VI_nodes','covered_superior_mediastinal_VII_nodes','covered_submandibular_Ib_nodes','covered_upper_jugular_II_nodes','covered_mid_jugular_III_nodes','covered_lower_jugular_IV_nodes','covered_posterior_triangle_V_nodes','other_named_or_unassigned_nodes']:
            add(region,'every_actual_node_identity_and_obtained_extent source_resolved_cortex source_resolved_hilum source_resolved_margin_and_capsular_interface every_solid_fluid_necrotic_appearing_calcific_or_other_component each_perinodal_and_adjacent_node_interface source_local_axes_and_named_map_boundaries unassessed_internal_or_uncovered_extent',[3,4,5],[3,4],side)
        for key in ['sternohyoid','sternothyroid','omohyoid_if_encountered','sternocleidomastoid','longus_colli','common_carotid_and_encountered_branches','internal_jugular_and_encountered_tributaries','encountered_thyroid_arteries_and_veins','encountered_parathyroid_or_mimic','encountered_recurrent_laryngeal_nerve_region','encountered_vagus_region']:
            add(key,adjacent,[0,2,3,4],[0,2,3],side)
        for key in ['nodule_to_capsule_and_perithyroidal_tissue','nodule_to_strap_muscles','nodule_to_trachea_larynx','nodule_to_esophagus','nodule_to_carotid_jugular_interface','nodule_to_encountered_neural_region','thyroid_bed_or_treated_tissue_if_present']:
            add(key,adjacent,[0,1,3,5],[0,1,3,4],side,True)
    for key in ['isthmus','pyramidal_lobe_if_present','thyroglossal_or_ectopic_tissue_if_encountered']:add(key,gland,[0,1,3],[0,1,3])
    add('isthmus_or_midline_nodules',nodule,[1,2,3,5],[1,2,3,4],pathology=True)
    for key in ['skin_subcutaneous_and_superficial_fascia','pretracheal_and_perithyroidal_fat','trachea_laryngeal_cartilage_and_air_interface','esophagus_and_tracheoesophageal_grooves','encountered_retrosternal_or_unassigned_extent','actual_midline_prelaryngeal_pretracheal_nodes']:
        add(key,adjacent,[0,3,4],[0,3])
    item={'investigation_id':IDENT,'module_id':ref['investigation']['module_id'],'title':'Every acquired thyroid component nodule node and adjacent interface','scope_status':'expanded_draft_requires_independent_thyroid_anatomical_review','modality_scope':['Ultrasound'],'sources':[{'title':s['title'],'url':s['url'],'reviewed_at':'2026-10-07','review_status':'reporting_source_reviewed_no_graphics_reused'} for s in guide['sources']],
        'source_contract_sha256':digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']}),'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':structures,
        'expansion_rules':['Every actual source site/component is independently instantiated; listed groups are a known floor, not the full native patient burden.','Nodal map/version and descriptive boundaries remain separate from thyroid TI-RADS; unacquired deep/retrosternal regions remain unassessed.','A thyroid outline or node-envelope mask does not supply actual tiny internal tissues, neural identity, tissue invasion or all source image features.'],
        'source_scope_issues':['Inherited selected references and partial neck orientation do not establish all thyroid/nodal/adjacent tissue components or commercial source clearance.','No independent leaf anatomical approval has been granted; all three representation types remain required.'],
        'functional_evidence_requirements':['Doppler flow, dynamic swallowing/motion, compression and vessel function require actual corresponding sources; they are not static geometry.','Histology/cytology, microscopic extension, thyroid function, assays and patient-specific management are supplied clinical evidence, not fabricated model tissues.','US echogenicity, reverberation and posterior artifacts require actual acquisition/reference tissue; a neutral surface texture cannot supply those observations.'],
        'clinical_validation_status':'draft_requires_thyroid_radiologist_and_relevant_clinical_review'}
    path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text());data['investigations']=[i for i in data['investigations'] if i['investigation_id']!=IDENT]+[item];data['scope']['catalog_investigation_ids']=[i['investigation_id'] for i in data['investigations']];path.write_text(json.dumps(data,indent=2)+'\n');n=len(requirements_for(item));print(len(structures),'groups;',n,'parts;',n*3,'representation obligations')
if __name__=='__main__':update()
