#!/usr/bin/env python3
"""Integrate the frozen traumatic-CT source packet and a conditional reporting draft.

Fixed trusted paths only. All review hashes and 34 public files are checked before
mutation. Unrelated JSON value tokens are preserved. Source examples, source
documents and cohort plots do not acquire patient findings or anatomy approval.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.anatomy_sources.integrate_myelopathy_sources import (
    object_members,member,array_values,replace_member,add_member,upsert_array,clear_catalog_caches as clear_core_catalog_caches)
from tools.check_msk_fidelity import requirements_for,validate_reporting_snapshots,inspect_binding,audit
from tools.check_radiology_fidelity import digest

INV='ra.ct-traumatic-haemorrhage'
MODULE='rad.5.intracranial-haemorrhage'
DATE='2026-10-11'
FOLDER=Path('docs/traumatic-haemorrhage-source-review')
INDEPENDENT=Path('docs/traumatic-haemorrhage-independent-review-20261011.json')
INDEPENDENT_SHA='73a9979a40c7407728cdf223c3cbd6b7a3326ffae75d4292abddc6606f33f6d8'
PINNED={
    'original-source-review.json':'a6d3f72f2fd082f2c4d0a43f6cbf28d7f9ffc503c37bcc60c3a1ef1f3ddc7e7f',
    'integration-proposal.json':'cb0e018b4411866a0ddaa3600ced9f4bed6c7d31cc30db53e736700733cfca4b',
    'ninds-2025-source-context-proposal.json':'df800577dcea762c244cfbedc4636d51e0ea50956ddd1af639545bca861dfa51',
    'visual-source-review.json':'2c13f82ea3675d3c37a9ae500ccc723e3679ea169d0467c6e451811be04988cb',
}
DATA_PATHS=[Path('data/radiology/'+name) for name in (
    'radiology-open-images.json','radiology-asset-evidence.json','non-msk-structure-requirements.json',
    'reporting-steps/neuroradiology.json','investigation-overrides-non-msk.json')]
RECEIPT=Path('docs/traumatic-haemorrhage-runtime-integration-20261011.json')
PREFIX='open-traumatic-centertbi-2024-fig'
SOURCE_PREFIX='web/reference-media/radiology-open/traumatic-haemorrhage/'
PRIMARY=[
    {'id':'trauma-centertbi-2024','title':'CENTER-TBI pictorial review of acute traumatic brain injury (2024)',
     'url':'https://doi.org/10.1089/neu.2023.0553','headings':['Skull and extra-axial injury','Parenchymal and ventricular injury','Mass effect and source measurement methods','Study and source limitations']},
    {'id':'trauma-ninds-2025','title':'NINDS imaging working-group recommendations and illustrated CDE appendix (2025)',
     'url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC12409119/','headings':['Updated imaging definitions','Traumatic axonal and/or microvascular injury','Source imaging limitations','Proposed reporting template']},
]
FIG=lambda name:PREFIX+str(name)
STEP_IMAGES={0:[FIG('2-panel-1')],1:[FIG('2-panel-2'),FIG(7)],
             2:[FIG('2-panel-1'),FIG('2-panel-2')],3:[FIG('2-panel-1'),FIG('2-panel-2'),FIG(9)],
             4:[FIG('2-panel-1'),FIG(3),FIG('2-panel-2')]}
NORMAL_PROMPTS=[
    'Extra-axial compartments [__]; each side/site and collection thickness in mm [__]; distribution, sutures/dural reflections and unassessed extent [__].',
    'Each contusion/haematoma and location [__]; oedema/swelling [__]; possible traumatic axonal and/or microvascular injury [__]; CT limits and MRI if acquired [__].',
    'Intraventricular blood by each horn/ventricle [__]; ventricular calibre and obstruction [__]; unassessed CSF pathways [__].',
    'Midline shift in mm, direction, stated level and method [__]; cisterns [__]; each suspected herniation route/secondary brainstem injury [__]; uncertainty [__].',
    'Each skull/skull-base fracture and suture/canal involvement [__]; pneumocephalus/scalp injury [__]; comparable prior study/timepoint and interval change [__].',
]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def clear_catalog_caches():
    clear_core_catalog_caches()
    from primer.module_media import radiology_source_bindings
    radiology_source_bindings.cache_clear()


def checked(path,expected):
    raw=(ROOT/path).read_bytes()
    if sha(raw)!=expected:raise ValueError('Reviewed source fingerprint changed: '+str(path))
    return json.loads(raw)


def validate_approval_contract(proof,review,proposal,context):
    if (review.get('decision')!='SOURCE_INTEGRATION_GO_WITH_EXPLICIT_LIMITS'
            or review.get('source_integration_approved') is not True
            or review.get('investigation_id')!=INV or review.get('module_id')!=MODULE):
        raise ValueError('Independent source decision or scope changed')
    for key in ('clinical_approval','commercial_clinical_grade_complete','fine_structure_coverage_granted',
                'native_patient_registration_verified','patient_specific_3D_approved'):
        if review.get(key) is not False:raise ValueError('Unsupported independent clinical approval: '+key)
    for record in (proof,proposal,context):
        if record.get('clinical_approval') is not False or record.get('fine_structure_coverage_granted') is not False:
            raise ValueError('Source packet cannot grant clinical/fine coverage')
    ids={r['id'] for r in proposal['images']}
    expected={FIG(i) for i in ['1','2-panel-1','2-panel-2',*[str(n) for n in range(3,15)]]}
    if (proposal.get('investigation_id')!=INV or proposal.get('module_id')!=MODULE
            or len(proposal['images'])!=15 or ids!=expected or ids!=set(review['approved_display_ids'])
            or {a['id'] for a in proposal['assets']}!=ids):
        raise ValueError('Exact scoped source selection changed')
    if {d['id'] for d in context['documents']}!=set(review['approved_source_context_document_ids']):
        raise ValueError('Approved source-context document set changed')
    if any(a.get('structure_ids')!=[] or a.get('requirement_coverage')!={}
           or a['anatomical_review']['status']!='pending' for a in proposal['assets']):
        raise ValueError('Source asset borrowed anatomical approval')


def validate_sources():
    review=checked(INDEPENDENT,INDEPENDENT_SHA)
    records={name:checked(FOLDER/name,expected) for name,expected in PINNED.items()}
    proof=records['original-source-review.json'];proposal=records['integration-proposal.json'];context=records['ninds-2025-source-context-proposal.json']
    if review['reviewed_metadata_sha256']!={str(FOLDER/k):v for k,v in PINNED.items()}:
        raise ValueError('Independent metadata set changed')
    validate_approval_contract(proof,review,proposal,context)
    files=review['public_files']
    if len(files)!=34 or sum(f['bytes'] for f in files)!=38875353:raise ValueError('Complete packet bound changed')
    seen=set()
    for entry in files:
        path=entry['path']
        if (not isinstance(path,str) or not path.startswith(SOURCE_PREFIX)
                or Path(path).name in {'.','..'} or '..' in Path(path).parts or path in seen):
            raise ValueError('Source file scope changed')
        seen.add(path);raw=(ROOT/path).read_bytes()
        if len(raw)!=entry['bytes'] or sha(raw)!=entry['sha256']:
            raise ValueError('Frozen public source changed: '+path)
    return proof,review,proposal,context,files


def normalized_rows(proposal):
    images=[];assets=[];changes=[];by_asset={a['id']:a for a in proposal['assets']}
    for original in proposal['images']:
        row=copy.deepcopy(original);asset=copy.deepcopy(by_asset[row['id']]);context=row['source_context']
        identifier=row['figure_identifier'];normalizations=[]
        row['figure_number']='2.'+identifier[-1] if identifier.startswith('2-') else int(identifier)
        row['source_figure_label']='Figure 2 Panel '+identifier[-1] if identifier.startswith('2-') else 'Figure '+identifier
        if context['extent']=='not_applicable':
            context['original_extent']=context['extent'];context['extent']='local'
            normalizations.append('extent normalized to local artwork; original not_applicable retained')
        if row['kind']=='clinical-image':
            context['original_depicted_state']=context['depicted_state'];context['depicted_state']='mixed'
            context['original_panel_states']=copy.deepcopy(context['panel_states'])
            context['panel_states']={p:'source_published_traumatic_injury_example' for p in context['panel_types']}
            context['panel_identifier_scheme']='descriptive_source_positions';row['panel_identifier_scheme']='descriptive_source_positions'
            asset['representation_selection']={'panels':list(context['selected_panels'])}
            normalizations.append('typed mixed state/source positions; original state and original per-panel codes retained')
        row['original_image_state']=row['image_state'];row['image_state']=context['depicted_state']
        row['clinical_approval']=row['fine_anatomical_approval']=row['patient_specific_3D_approved']=False
        context['clinical_approval']=context['fine_anatomical_approval']=False
        row['source_context_original_proof_relation']={'evidence_path':str(FOLDER/'original-source-review.json'),
            'evidence_sha256':PINNED['original-source-review.json'],'original_source_context_sha256':digest(original['source_context']),
            'schema_normalization_only':True}
        row['rights_review']='Pinned independent source review '+INDEPENDENT_SHA+' approves the full source object and disclosed RGB interpretation under CC BY4; no clinical/fine-anatomy approval.'
        asset.update(source_context=copy.deepcopy(context),structure_ids=[],requirement_coverage={},
                     clinical_approval=False,fine_anatomical_approval=False,patient_specific_3D_approved=False,runtime_registered=True)
        asset['source_context_original_proof_relation']=copy.deepcopy(row['source_context_original_proof_relation'])
        asset['source']['license'].update(independent_review_path=str(INDEPENDENT),independent_review_sha256=INDEPENDENT_SHA)
        asset['visual_review'].update(evidence_path=str(INDEPENDENT),evidence_sha256=INDEPENDENT_SHA,anatomical_or_clinical_approval=False)
        catalog._validate_source_panel_roles(row)
        problems=inspect_binding(asset,{'modality_scope':['CT','MRI'],'context_requirements':[]})
        if problems:raise ValueError('Typed source context contradiction: '+str(problems))
        images.append(row);assets.append(asset);changes.append({'id':row['id'],'changes':normalizations,
            'original_context_sha256':digest(original['source_context']),'registered_context_sha256':digest(context)})
    return images,assets,changes


def reporting_override(existing,reading,context_documents):
    override=copy.deepcopy(existing);guide=copy.deepcopy(existing['reporting']);guide['reviewed_at']=DATE
    guide['protocol']=['Review the actually acquired noncontrast head CT from skull base/foramen magnum through vertex in brain, wider subdural and bone windows, with multiplanar reconstructions if available.',
        'Record acquisition coverage, reconstruction thickness/kernel, motion/beam hardening and diagnostic limitations; compare the actual prior examination and timepoint. MRI or vascular imaging, if acquired, has a separate role.']
    guide['checklist']=[
        {'label':'Extra-Axial Blood','detail':'Assess each epidural, subdural and subarachnoid collection by actual side, site, extent, density pattern and relation to sutures/dural reflections.'},
        {'label':'Parenchymal Injury','detail':'Assess every contusion, intraparenchymal haemorrhage, oedema/swelling and CT-visible traumatic axonal and/or microvascular injury; state CT sensitivity limits.'},
        {'label':'Ventricles','detail':'Assess blood in each ventricular horn/ventricle, ventricular calibre, effacement/displacement and actual CSF-pathway obstruction or hydrocephalus.'},
        {'label':'Mass Effect','detail':'Assess the midline at a stated level/method, basal cisterns, each suspected herniation route and secondary brainstem injury.'},
        {'label':'Bone And Comparison','detail':'Assess skull/skull-base fractures, suture/canal involvement, pneumocephalus/scalp injury and comparable interval change.'},
    ]
    guide['measurements']=[
        {'name':'Haematoma and shift','method':'On the calibrated current study, measure each extra-axial collection thickness perpendicular to the adjacent skull and midline shift in mm with side/direction, a stated level (for example septum pellucidum at foramen of Monro) and a stated method.',
         'pitfall':'Perpendicular ideal-midline and A/2−B methods can differ. Uncalibrated publication PNGs or source centimetre calipers do not supply patient measurements; use comparable levels/planes for follow-up.'},
        {'name':'Lesion extent and interval change','method':'Record each actual lesion and its extent in calibrated planes with native units, examination dates/times and comparable reconstruction; use volume only with a stated validated acquisition/method.',
         'pitfall':'Source serial panels are the source patient, not the reader patient. Density, slice plane and reconstruction differences can mimic growth; CT may miss nonhaemorrhagic injury.'},
        {'name':'Ventricular calibre and obstruction','method':'Assess each actually imaged ventricular compartment, CSF outlet/pathway and calibre on the current study; state compression versus enlargement and the location of a suspected obstruction.',
         'pitfall':'A selected source slice is not a complete ventricular/CSF examination. Do not infer hydrocephalus or an occlusion from an unassessed pathway.'},
    ]
    guide['pitfalls']=[
        'EDH is usually limited by sutural attachment but can cross dural folds or the midline, and suture diastasis/fracture can alter its boundaries. SDH commonly crosses sutures and follows dural reflections; assess morphology and the actual full distribution.',
        'Acute blood can be relatively isodense with severe anaemia or admixture; mixed density alone does not prove active arterial extravasation or establish haemorrhage age.',
        'A normal CT does not exclude nonhaemorrhagic traumatic injury. CT-visible microbleeds do not establish axonal histology; MRI, if acquired, is interpreted separately for traumatic axonal and/or microvascular injury (TAMVI).',
        'Published CT/MRI examples are different or unregistered source cases unless the original caption explicitly establishes a relation. Cohort outcome/statistical plots do not predict the current patient.',
        'Secondary brainstem haemorrhage in descending herniation is a serious source-described Duret context; imaging alone does not establish mechanism or inevitable outcome.',
    ]
    guide['impression_prompts']=['State each actually observed bleeding compartment/lesion, side, site and extent, then mass effect, ventricular obstruction and associated bone injury.',
        'State relevant interval change, examination limitations and any unassessed CT/MRI/vascular question; source examples never become patient findings.']
    guide['template_sections']=[
        {'heading':'EXTRA-AXIAL BLOOD','body':'Each collection: [compartment, side/site, distribution and thickness __ mm]. Density pattern: [ ]. Suture/dural-reflection relation: [ ]. Unassessed extent: [ ].'},
        {'heading':'PARENCHYMAL INJURY','body':'Each contusion/haematoma: [side/site, extent and density]. Oedema/swelling: [ ]. Possible TAMVI/CT limitations: [ ]. MRI if actually acquired: [ ].'},
        {'heading':'VENTRICLES','body':'Blood by horn/ventricle: [ ]. Calibre/effacement/displacement: [ ]. CSF-pathway obstruction/hydrocephalus: [ ]. Unassessed pathways: [ ].'},
        {'heading':'MASS EFFECT','body':'Midline shift: [ ] mm toward [ ], at [level], using [method]. Basal cisterns: [ ]. Herniation route/secondary brainstem injury: [ ]. Uncertainty: [ ].'},
        {'heading':'BONE AND COMPARISON','body':'Each skull/skull-base fracture: [site, pattern, suture/canal involvement]. Pneumocephalus/scalp injury: [ ]. Prior examination/date/time and comparable interval change: [ ].'},
    ]
    guide['sources']=[*guide['sources'],*[{k:r[k] for k in ('title','url')} for r in PRIMARY if r['url'] not in {s['url'] for s in guide['sources']}]]
    override.update(reporting=guide,reading=[*reading,*[copy.deepcopy(r) for r in PRIMARY if r['url'] not in {s['url'] for s in reading}]],
                    additional_sources=[{k:r[k] for k in ('title','url')} for r in PRIMARY],key_images=[],suppress_visual_fallback=True,
                    source_context_documents=copy.deepcopy(context_documents),
                    overview='Assess the current acquired trauma CT by bleeding compartment, parenchymal injury, ventricles, mass effect and skull/skull-base injury. Preserve actual side/site, measurement method, comparison and examination limits.',
                    learning_points=[
                        'Localise each traumatic collection before interpreting its cause; sutures and dural reflections are useful relationships with relevant exceptions.',
                        'Review all actual cerebral, cerebellar and brainstem regions for injury and oedema; CT does not exclude nonhaemorrhagic injury.',
                        'Assess each ventricular compartment, basal cistern and herniation route; use calibrated current-study measurements with stated units, level and method.',
                        'Review bone windows, skull-base canals and associated air/scalp injury, then compare like-for-like prior acquisitions.',
                        'Complete original source figures and NINDS documents are teaching references. Different patients, MRI adjuncts and cohort statistics retain separate roles.',
                    ])
    return override


def walkthrough(existing,guide):
    value=copy.deepcopy(existing);value['walkthrough_reviewed_at']=DATE
    value['start']={'images':[FIG('2-panel-1'),FIG('2-panel-2')],'module_illustrations':False}
    value['preset_mode']='assessment-prompts';value['clinical_approval']=value['fine_anatomical_approval']=False
    tips=[guide['pitfalls'][0],guide['pitfalls'][2],guide['measurements'][2]['pitfall'],guide['pitfalls'][4],guide['measurements'][1]['pitfall']]
    looks=[
        'Brain, wider subdural and bone windows; each convexity, interhemispheric/tentorial and posterior-fossa compartment; preserve actual suture and meningeal relationships.',
        'All acquired cerebral surfaces/white matter, deep structures, corpus callosum, cerebellum and brainstem. MRI FLAIR/SWI source panels are separate adjuncts, never CT-visible evidence.',
        'Each lateral ventricular horn, third and fourth ventricle; actually imaged connections/outlets and compression versus enlargement.',
        'Septum pellucidum at a stated level, falx reference, ambient/quadrigeminal and other basal cisterns, tentorial hiatus, uncus/parahippocampal structures and posterior fossa/foramen magnum as acquired.',
        'Calvarium, skull-base bone windows/MPR, sutures, middle meningeal grooves/carotid canals and associated scalp/air; comparable current/prior reconstructions.',
    ]
    findings=[
        ['[Compartment] collection at [side/site], __ mm thick on [plane/level]; distribution and suture/dural-fold relation [ ].','SAH distribution in actual [sulci/fissures/cisterns] [ ]; unassessed extent [ ].'],
        ['Contusion/haematoma at [side/site] with extent [ ] and oedema/swelling [ ].','CT-visible punctate injury at [site] [ ]; possible TAMVI and unassessed nonhaemorrhagic injury [ ].'],
        ['Blood in [each actual horn/ventricle] [ ]; calibre and CSF-pathway obstruction/hydrocephalus [ ].'],
        ['Midline shift __ mm toward [ ], at [level] using [method].','Cisternal compression/effacement [ ]; suspected herniation route/secondary brainstem finding [ ]; uncertainty [ ].'],
        ['Fracture at [site] with [pattern] and suture/canal relation [ ]; pneumocephalus/scalp injury [ ].','Since [actual examination/date/time], comparable lesion/ventricular/mass-effect change [ ]; plane/reconstruction limits [ ].'],
    ]
    measure_names=[['Haematoma and shift'],['Lesion extent and interval change'],['Ventricular calibre and obstruction'],['Haematoma and shift'],['Lesion extent and interval change']]
    for i,step in enumerate(value['steps']):
        step.setdefault('original_normal_report_statement',copy.deepcopy(step.get('normal')))
        step.update(detail=guide['checklist'][i]['detail'],look=looks[i],normal={step['sections'][0]:NORMAL_PROMPTS[i]},
                    images=STEP_IMAGES[i],parts=[],tip=tips[i],findings=findings[i],measurements=measure_names[i],clinical_approval=False)
    return value


COMMON=['full_actual_acquired_extent_and_unassessed_limits','each_resolved_surface_boundary_and_neighboring_tissue_interface',
        'authentic_topology_continuity_and_source_coordinates','each_actual_side_site_lesion_variant_age_and_timepoint',
        'native_registered_planes_and_reconstruction_roles','fine_resolution_partial_volume_and_unresolved_microstructure_limits']


def requirements_draft(guide,shared_node):
    groups=[]
    def add(category,site,name,parts,steps,side='midline',modes=None,candidates=None,condition='every_actual_acquired_normal_variant_or_injury_state',basis='reporting_walkthrough_and_primary_reading'):
        identifier='trauma.'+category+'.'+site+'.'+side
        groups.append({'id':identifier,'name':(side+' ' if side in ('left','right') else '')+name,
            'tissue_class':category,'required_parts':[{'id':identifier+'.'+p,'name':p.replace('_',' ')} for p in dict.fromkeys(COMMON+parts)],
            'anatomical_site_scope':[site],'laterality':side,'modality_scope':modes or ['CT'],
            'condition':condition,'requirement_basis':basis,'report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in steps],
            'walkthrough_step_indices':steps,'context_requirements':{},
            'context_instantiation_rules':{'purpose':'separate anatomy reference, pathology example and current-patient assessment',
                'site':'instantiate every actual involved/resolved site and each lesion, beyond these named minimum groups',
                'population':'instantiate actual age/development, variant and treatment context; cohort age cannot identify a panel patient',
                'acquisition':'instantiate CT window/kernel/plane/timepoint, MRI sequence or vascular phase only when acquired; no cross-case registration assumed',
                'resolution':'report each unresolvable membrane/tract/vessel wall separately; CT-negative/subvoxel anatomy is not absent anatomy'},
            'requires_site_instantiation':True,'site_instantiation_status':'pending','population_and_state_instantiation_status':'pending',
            'candidate_figure_ids':[FIG(x) for x in candidates or []],
            'candidate_sources_are_partial_examples_not_coverage':True,
            'representation_status':{'image':'pending_full_extent_and_fine_boundary_review','schematic':'pending_independent_anatomical_review','model':'missing_source_native_complete_geometry'},
            'clinical_approval':False,'fine_anatomical_approval':False,'structure_coverage_granted':False})
    # Meningeal layers and their interfaces are required separately; names do not
    # make these microscopic boundaries visible on noncontrast CT.
    for site in ['frontal_convexity','temporal_convexity','parietal_convexity','occipital_convexity','posterior_fossa']:
        for side in ['left','right']:
            for membrane in ['periosteal_dura','meningeal_dura','arachnoid_mater','pia_mater']:
                add('meninges',site+'_'+membrane,membrane.replace('_',' ')+' at '+site.replace('_',' '),
                    ['outer_and_inner_surfaces','actual_thickness_if_resolved','skull_or_CSF_or_cortical_attachment','resolved_layer_separation_and_adjacent_collection'],[0],side)
            for compartment in ['epidural_potential_space','subdural_potential_space','subarachnoid_space']:
                add('compartment',site+'_'+compartment,compartment.replace('_',' ')+' at '+site.replace('_',' '),
                    ['bounding_membranes_and_tissue_planes','every_actual_collection_and_internal_component','relation_to_sutures_falx_tentorium_and_adjacent_brain','full_collection_distribution_and_transition_between_planes'],[0],side,candidates=['2-panel-1'])
    for name in ['falx_cerebri','tentorium_cerebelli','tentorial_hiatus','dural_sinus_wall','arachnoid_trabeculae','arachnoid_granulations','pial_vessel_entry_interface']:
        add('meningeal_interface',name,name.replace('_',' '),['attachment_and_openings','each_resolved_layer_lumen_and_neighbor','collection_relationship_and_resolution_limit'],[0,3])
    # Named CT landmarks, source-described deep injury locations and entire
    # actually scanned parenchyma. Finer tracts require separate source evidence.
    sites=['orbital_frontal_cortex','inferior_frontal_surface','anterior_temporal_pole','temporal_cortex','parietal_cortex','occipital_cortex',
           'frontal_gray_white_junction','temporal_gray_white_junction','parietal_gray_white_junction','occipital_gray_white_junction',
           'frontal_subcortical_white_matter','temporal_subcortical_white_matter','parietal_subcortical_white_matter','occipital_subcortical_white_matter',
           'cingulate_gyrus','uncus','parahippocampal_gyrus','hippocampal_head','thalamus','putamen','caudate','internal_capsule_anterior_limb',
           'internal_capsule_genu','internal_capsule_posterior_limb','cerebellar_hemisphere','cerebellar_tonsil','cerebral_peduncle','superior_cerebellar_peduncle','middle_cerebellar_peduncle','inferior_cerebellar_peduncle']
    for side in ['left','right']:
        for site in sites:
            add('parenchyma',site,site.replace('_',' '),['cortical_gray_white_or_nuclear_boundary_as_applicable','each_resolved_internal_component_tract_or_horn',
                'each_actual_contusion_hematoma_microbleed_edema_or_ischemic_component','adjacent_CSF_bone_vessel_and_other_neural_relations','unacquired_or_CT_invisible_injury'],[1,3],side,candidates=['2-panel-2'])
    for site in ['corpus_callosum_rostrum','corpus_callosum_genu','corpus_callosum_body','corpus_callosum_isthmus','corpus_callosum_splenium',
                 'fornix_body','septum_pellucidum','cerebellar_vermis','midbrain_tectum','midbrain_tegmentum','pons_upper','pons_lower','medulla','cervicomedullary_junction']:
        add('deep_neural_landmark',site,site.replace('_',' '),['each_resolved_subdivision_and_surface','each_actual_injury_and_neighbor_relation','brainstem_paramedian_versus_primary_trauma_distribution','hemorrhagic_vs_nonhemorrhagic_role_if_acquired'],[1,2,3],modes=['CT','MRI'],candidates=['2-panel-2',7,9])
    for side in ['left','right']:
        for horn in ['frontal_horn','body','atrium','occipital_horn','temporal_horn','foramen_of_monro']:
            add('ventricle','lateral_'+horn,'lateral ventricular '+horn.replace('_',' '),['ependymal_wall_and_native_lumen','each_actual_blood_component_and_sedimentation_level',
                'local_calibre_effacement_displacement_or_entrapment','CSF_connection_obstruction_and_periventricular_tissue'],[2,3],side,candidates=['2-panel-1','2-panel-2'])
    for site in ['third_ventricle','cerebral_aqueduct','fourth_ventricle','foramen_of_magendie','septal_midline_reference']:
        add('ventricular_pathway',site,site.replace('_',' '),['wall_lumen_and_each_connection','actual_blood_level_or_obstruction','calibre_and_direction_of_displacement','full_acquired_pathway_or_missing_extent'],[2,3],candidates=['2-panel-1','2-panel-2'])
    for side in ['left','right']:
        add('ventricular_outlet','foramen_of_luschka','foramen of Luschka',['fourth_ventricular_connection','outlet_lumen_and_adjacent_cistern','actual_obstruction_or_unresolved_outlet'],[2,3],side)
        for site in ['ambient_cistern','sylvian_fissure','cortical_sulci','cerebellopontine_cistern']:
            add('CSF_space',site,site.replace('_',' '),['arachnoid_pial_boundaries_and_neighbors','blood_or_patency_as_actually_observed','compression_asymmetry_or_obliteration','full_continuous_source_extent'],[0,2,3],side,candidates=['2-panel-1','2-panel-2'])
    for site in ['suprasellar_cistern','interpeduncular_cistern','prepontine_cistern','quadrigeminal_cistern','superior_cerebellar_cistern','cisterna_magna','anterior_interhemispheric_fissure','posterior_interhemispheric_fissure']:
        add('basal_or_midline_CSF_space',site,site.replace('_',' '),['each_boundary_neural_vascular_and_meningeal_neighbor','native_connection_to_adjacent_CSF_space','actual_blood_compression_patency_or_obliteration','unassessed_fine_membrane_or_outlet'],[0,2,3],candidates=['2-panel-1','2-panel-2'])
    # Every actual vessel/branch remains to be instantiated. Noncontrast groove
    # proximity is separate from a proven laceration, dissection or flow finding.
    for side in ['left','right']:
        for site in ['middle_meningeal_artery','middle_meningeal_groove','cortical_bridging_veins','sphenoparietal_sinus','transverse_sinus','sigmoid_sinus','internal_carotid_canal','posterior_cerebral_artery','anterior_choroidal_artery','oculomotor_nerve']:
            add('vascular_or_neural_relation',site,site.replace('_',' '),['each_actual_branch_origin_route_and_endpoint','wall_lumen_or_nerve_boundaries_when_resolved','relation_to_fracture_collection_dural_fold_or_herniation','actual_injury_vs_inferred_risk_and_unacquired_angiographic_role'],[0,3,4],side,modes=['CT','MRI'],candidates=['2-panel-1',3])
    for site in ['superior_sagittal_sinus','straight_sinus','confluence_of_sinuses','brainstem_paramedian_perforators']:
        add('midline_vascular_relation',site,site.replace('_',' '),['every_actual_branch_or_sinus_junction','source_resolved_wall_lumen_and_position','collection_displacement_or_herniation_relation','flow_or_injury_not_inferred_from_static_CT'],[0,3,4],modes=['CT','MRI'])
    for side in ['left','right']:
        for site in ['frontal_bone','parietal_bone','occipital_bone','temporal_squamous_bone','temporal_petrous_bone','sphenoid_greater_wing','sphenoid_lesser_wing',
                     'anterior_skull_base','middle_skull_base','posterior_skull_base','orbital_roof','orbital_floor','inferior_orbital_rim','optic_canal',
                     'superior_orbital_fissure','jugular_foramen','hypoglossal_canal','nasal_bone','maxilla','pterygoid_plates','zygomatic_bone',
                     'craniofacial_buttresses','scalp_subgaleal_space']:
            add('bone_or_scalp',site,site.replace('_',' '),['inner_outer_table_or_tissue_surfaces','each_actual_fracture_line_fragment_displacement_or_collection','cortex_diploe_suture_and_foramen_interfaces','adjacent_brain_meninges_vessel_and_air_relations','whole_bone_window_MPR_extent_and_source_reconstruction_limit'],[0,4],side,candidates=['2-panel-1',3])
    for site in ['sagittal_suture','coronal_sutures','lambdoid_sutures','squamosal_sutures','metopic_suture_if_present','clivus','cribriform_plate','foramen_magnum','tentorial_bony_attachments']:
        add('suture_or_skull_base',site,site.replace('_',' '),['each_actual_suture_segment_or_bone_surface','normal_variant_developmental_state_vs_diastasis_fracture','each_actual_canal_foramen_or_fine_bony_interface','dural_attachment_and_adjacent_collection_or_air'],[0,3,4],candidates=['2-panel-1',3])
    for side in ['left','right']:
        for injury in ['epidural_hematoma','acute_subdural_hematoma','isodense_subacute_subdural','chronic_or_mixed_subdural','subarachnoid_hemorrhage','contusion','intracerebral_hematoma','TAMVI_pattern','intraventricular_blood','edema_or_swelling','secondary_brainstem_hemorrhage','fracture','pneumocephalus','scalp_hematoma']:
            step=4 if injury in ['fracture','pneumocephalus','scalp_hematoma'] else 2 if injury=='intraventricular_blood' else 0 if 'subdural' in injury or injury in ['epidural_hematoma','subarachnoid_hemorrhage'] else 1
            add('actual_lesion',injury,injury.replace('_',' '),['instantiate_each_actual_lesion_separately','full_source_extent_and_every_distinct_component','each_resolved_margin_and_neighboring_tissue_interface','native_density_signal_or_susceptibility_role_if_acquired','calibrated_size_units_and_reproducible_plane','serial_source_case_and_timepoint_registration','clinical_inference_separate_from_pixels'],[step,3],side,modes=['CT','MRI'] if injury=='TAMVI_pattern' else ['CT'],candidates=['2-panel-1','2-panel-2'],condition='instantiate every actually present lesion; this group does not imply the lesion exists')
        for condition,parts,modes in [
            ('subdural_hygroma',['arachnoid_tear_vs_inferred_CSF_source','blood_vs_CSF_like_collection_and_underlying_atrophy','each_actual_membrane_collection_and_communication'],['CT','MRI']),
            ('cerebral_or_cerebellar_atrophy',['each_actual_region_and_volume_loss','sulcal_and_ventricular_enlargement_with_normal_variant_context','baseline_vs_posttraumatic_serial_change_not_inferred_from_one_panel'],['CT','MRI']),
            ('hypoxic_or_ischemic_injury',['each_actual_territory_and_gray_white_component','native_diffusion_ADC_and_CT_roles_if_acquired','secondary_vascular_compression_vs_other_cause_not_histologically_assumed'],['CT','MRI']),
            ('penetrating_injury',['full_actual_entry_track_exit_and_foreign_body','each_bone_dural_parenchymal_vascular_and_CSF_interface','native_material_and_artifact_limits'],['CT','MRI']),
            ('traumatic_arterial_dissection',['each_actual_artery_and_segment','wall_lumen_flap_thrombus_and_stenosis_if_resolved','full_covered_course_and_separate_CTA_MRA_or_angiographic_phase'],['CT','MRI','Radiography']),
            ('traumatic_pseudoaneurysm',['each_actual_sac_neck_and_parent_artery_connection','wall_and_lumen_or_extravascular_boundaries_if_resolved','serial_development_and_native_angiographic_evidence'],['CT','MRI','Radiography']),
            ('venous_sinus_injury_or_thrombosis',['each_actual_sinus_segment_branch_and_junction','native_wall_lumen_thrombus_or_compression','separate_CT_venography_MR_venography_or_angiography_if_acquired'],['CT','MRI','Radiography']),
            ('skull_base_CSF_communication',['each_actual_bony_dural_and_arachnoid_defect','CSF_pathway_and_extracranial_exit_if_demonstrated','noncontrast_fracture_risk_separate_from_proven_leak'],['CT','MRI']),
            ('postoperative_trauma_state',['each_actual_craniotomy_craniectomy_or_burr_hole_boundary','surgical_dural_collection_and_residual_brain_interfaces','actual_drain_catheter_or_other_device_course_if_present','pre_post_treatment_acquisition_and_timepoint_not_borrowed_from_source_cases'],['CT','MRI']),
        ]:
            add('conditional_reading_lesion',condition,condition.replace('_',' '),parts,[0,1,2,3,4],side,modes=modes,
                condition='conditional primary-reading or acquired follow-up role; instantiate only if actually imaged or assessed, with unknown acquisition retained',
                basis='actual_primary_reading_or_post_treatment_dependency')
    route_parts={
        'subfalcine':['cingulate_gyrus_falx_relation','anterior_cerebral_artery_relation_if_resolved','foramen_of_Monro_and_ipsilateral_ventricular_entrapment'],
        'uncal_downward_transtentorial':['uncus_parahippocampal_gyrus_tentorial_edge_relation','oculomotor_nerve_and_posterior_cerebral_artery_relation_if_resolved','midbrain_and_perimesencephalic_cisternal_displacement'],
        'central_downward_transtentorial':['diencephalic_and_midbrain_descent','tentorial_hiatus_and_basal_cisternal_relations','brainstem_vascular_relations_if_resolved'],
        'upward_transtentorial':['cerebellar_vermis_and_superior_surface_tentorial_relation','quadrigeminal_and_superior_cerebellar_cistern_relation','fourth_ventricular_compression'],
        'tonsillar':['each_cerebellar_tonsil_foramen_magnum_relation','medulla_and_cervicomedullary_junction_compression','cisterna_magna_and_upper_cervical_CSF_relations'],
    }
    for route in route_parts:
        add('herniation_route',route,route.replace('_',' ')+' herniation route',['actual_displaced_structure_and_full_trajectory','fixed_falx_tentorial_edge_or_foramen_reference','each_compressed_cistern_ventricle_vessel_nerve_or_brainstem_interface','actual_side_degree_and_timepoint','secondary_injury_vs_uncertain_mechanism','calibrated_source_geometry_no_affine_fake_lesion',*route_parts[route]],[2,3],candidates=['2-panel-1','2-panel-2',9],condition='only each actually suspected/observed route, with alternative and unassessed extent retained')
    for task in ['extraaxial_thickness','midline_shift_A2_minus_B','midline_shift_perpendicular_falx','lesion_extent_or_volume','ventricular_calibre','serial_interval_change']:
        add('measurement',task,task.replace('_',' '),['actual_source_calibration_and_native_units','named_landmark_level_and_method','correct_orthogonal_plane_and_sign_direction','repeatable_current_prior_source_correspondence','partial_volume_and_method_uncertainty','source_published_calipers_not_patient_measurements'],[0,1,2,3,4],candidates=['2-panel-1','2-panel-2'])
    # Literal shared-lesson dependencies stay explicit and conditional; traumatic
    # examples do not fulfil spontaneous haemorrhage, CTA/MRI or angiographic tasks.
    quiz_parts={
        1:['right_temporal_epidural_collection','squamous_temporal_fracture','clotted_and_lower_attenuation_swirl_components','middle_meningeal_artery_relation_not_CT_proved_extravasation'],
        2:['right_frontal_parietal_subdural_collection','coronal_suture_crossing','periosteal_dural_attachment','meningeal_dura_arachnoid_and_falx_boundary'],
        3:['right_basal_ganglia_spontaneous_hematoma','orthogonal_A_B_diameters','contiguous_slice_extent_C','calibrated_centimetre_to_millilitre_ABC2_geometry'],
        4:['right_putaminal_hematoma','arterial_CTA_extravasation_focus','clot_vessel_separation','native_HU_calibration','delayed_phase_growth_same_case'],
        5:['hyperacute_oxyhemoglobin_blood_state','acute_deoxyhemoglobin_blood_state','early_subacute_intracellular_methemoglobin','late_subacute_extracellular_methemoglobin','chronic_hemosiderin_ferritin_rim','source_matched_T1_T2_and_susceptibility_stages'],
        6:['interpeduncular_prepontine_ambient_cisternal_blood','anterior_interhemispheric_and_lateral_sylvian_distribution','ventricular_blood_assessment','thin_section_CTA_full_arterial_coverage_and_limits'],
        7:['anterior_interhemispheric_blood','left_gyrus_rectus_hematoma','anterior_communicating_artery_complex_and_aneurysm','both_lateral_ventricles','native_CSF_obstruction_and_drainage_route_if_actual'],
        8:['right_occipital_lobar_hematoma','cortical_subcortical_microbleeds','basal_ganglia_thalami_pons_comparison','two_convexity_sulci_superficial_siderosis','native_SWI_distribution_and_mimics'],
        9:['AVM_nidus_maximum_diameter','left_precentral_gyrus_eloquent_cortex','subependymal_vein','internal_cerebral_vein','each_actual_feeder_nidus_connection_and_draining_route'],
        10:['cerebellar_hematoma','cavernous_malformation_mixed_signal_core','complete_susceptibility_rim','adjacent_small_veins','enlarged_transcortical_DVA_draining_vein','cavernoma_DVA_interface'],
        11:['left_convexity_isodense_subdural_collection','compressed_left_hemisphere','inward_displaced_gray_white_junction','effaced_sulci','native_brain_vs_subdural_window_matched_slices'],
        12:['right_convexity_subdural_collection','native_38_HU_and_density_relative_to_cortex','absence_or_presence_of_internal_septa','actual_hemoglobin_and_timing_not_inferred_from_pixels'],
        13:['lobar_hematoma','lobar_microbleeds','cortical_superficial_siderosis','calcification_cavernoma_and_small_vessel_mimics','native_SWI_phase_and_second_sequence','blooming_not_native_lesion_size'],
    }
    for i,question in enumerate(shared_node['quiz']):
        mode=['CT','MRI'] if i+1 in [5,8,10,13] else ['CT','MRI','Radiography'] if i+1 in [6,7,9] else ['CT']
        add('shared_quiz_dependency','q'+str(i+1),'shared intracranial-haemorrhage quiz '+str(i+1),
            ['every_literal_named_structure_compartment_and_neighbor','each_case_specific_lesion_internal_component_and_extent','each_named_source_sequence_phase_or_method','native_units_coordinates_or_lesion_stage_if_reported','actual_differential_and_unresolved_structure_or_source_role',*quiz_parts[i+1]],[0,1,2,3,4],modes=mode,
            condition='only when this shared quiz dependency is being represented; nontraumatic cases remain distinct',basis='literal_shared_curriculum_quiz')
        groups[-1]['literal_shared_quiz']=copy.deepcopy(question)
        groups[-1]['source_case_context']='traumatic' if i+1 in [1,2,11,12] else 'nontraumatic_or_separate_shared_dependency'
        groups[-1]['candidate_figure_ids']=[]
    return {'schema_version':1,'investigation_id':INV,'module_id':MODULE,
        'title':'Traumatic head CT: conditional full reporting anatomy and source-resolution requirement draft',
        'scope_status':'expanded_conditional_draft_requires_neuroradiologist_review_and_actual_site_instantiation',
        'clinical_validation_status':'draft_requires_neuroradiologist_review','required_representations':['image','schematic','model'],
        'modality_scope':['CT','MRI_if_actually_acquired_for_separate_TAMVI_or_anatomy_role','CTA_CTV_MRA_or_angiography_only_if_separately_acquired'],
        'reporting_checklist':copy.deepcopy(guide['checklist']),'reporting_template_sections':copy.deepcopy(guide['template_sections']),
        'structures':groups,'source_contract_sha256':'PENDING_EFFECTIVE_CONTRACT',
        'source_contract_definition':['reporting','report_templates','walkthrough','reading'],
        'shared_curriculum_quiz_sha256':digest(shared_node['quiz']),
        'non_anatomical_report_dependencies':['Actual indication/history and anticoagulation/anaemia context, never inferred from source examples',
            'Current acquisition quality/coverage/kernel/planes and separate MRI/vascular roles','Actual comparison examination/date/time and comparable reconstruction',
            'Key-image series/image identifiers from the current patient','Clinical impression tied to actual observations and uncertainties',
            'Recommendation/communication recipient/time/method based on the current clinical situation'],
        'scope_review_flags':{'named_parts_are_a_floor_not_full_patient_denominator':True,'requires_each_actual_site_lesion_and_fine_part_instantiation':True,
            'unbounded_actual_patient_structure_denominator_known':False,'thin_meningeal_vessel_wall_tract_and_microvascular_visibility_not_assumed_on_CT':True,
            'native_source_meshes_or_patient_registered_volumes_available_for_complete_trauma':False,
            'source_figure_selection_does_not_bound_required_anatomy':True,'all_source_bindings_are_candidates_with_zero_coverage':True,
            'shared_nontraumatic_quiz_dependencies_not_fulfilled_by_traumatic_sources':True,
            'administrative_fields_remain_separate_from_anatomical_geometry_obligations':True},
        'runtime_integrated':True,'clinical_approval':False,'fine_anatomical_approval':False,'structure_coverage_granted':False}


def unrelated_tokens(raw,path,ids):
    result={}
    if path==DATA_PATHS[0] or path==DATA_PATHS[4]:
        for key,_,a,b in object_members(raw):
            if key!=INV:result[key]=sha(raw[a:b].encode())
    elif path in [DATA_PATHS[1],DATA_PATHS[2]]:
        field='assets' if path==DATA_PATHS[1] else 'investigations';_,a,b=member(raw,[field])
        for value,token in array_values(raw,a,b):
            identifier=value['id'] if field=='assets' else value['investigation_id']
            if (identifier not in ids if field=='assets' else identifier!=INV):result[field+':'+identifier]=sha(token.encode())
        for key,_,a,b in object_members(raw):
            if key not in {field,'scope'}:result['top:'+key]=sha(raw[a:b].encode())
        if field=='investigations':
            _,a,_=member(raw,['scope'])
            for key,_,c,d in object_members(raw,a):
                if key!='catalog_investigation_ids':result['scope:'+key]=sha(raw[c:d].encode())
            _,a,b=member(raw,['scope','catalog_investigation_ids'])
            for value,token in array_values(raw,a,b):
                if value!=INV:result['catalog:'+value]=sha(token.encode())
    else:
        for key,_,a,b in object_members(raw):
            if key!='investigations':result['top:'+key]=sha(raw[a:b].encode())
        _,a,_=member(raw,['investigations'])
        for key,_,c,d in object_members(raw,a):
            if key!=INV:result[key]=sha(raw[c:d].encode())
    return result


def integrate():
    proof,review,proposal,context,media=validate_sources()
    images,assets,normalizations=normalized_rows(proposal);ids={r['id'] for r in images}
    before={p:(ROOT/p).read_text() for p in DATA_PATHS}
    clear_catalog_caches();curriculum=Curriculum();old_reference=catalog.detail(curriculum,catalog.resolve(INV))['radiology_reference']
    nontrauma_before=catalog.detail(curriculum,catalog.resolve('ra.intracranial-haemorrhage'))['radiology_reference']
    old_override=json.loads(before[DATA_PATHS[4]])[INV]
    override=reporting_override(old_override,old_reference['reading'],context['documents']);guide=override['reporting']
    step=walkthrough(json.loads(before[DATA_PATHS[3]])['investigations'][INV],guide)
    item=requirements_draft(guide,curriculum.node(MODULE));outputs={}
    raw=before[DATA_PATHS[0]];current=json.loads(raw);rows=[r for r in current.get(INV,[]) if r['id'] not in ids]+images
    outputs[DATA_PATHS[0]]=replace_member(raw,[INV],rows) if INV in current else add_member(raw,[],INV,rows)
    outputs[DATA_PATHS[1]]=upsert_array(before[DATA_PATHS[1]],['assets'],assets,'id',lambda a:a['id'] in ids)
    outputs[DATA_PATHS[3]]=replace_member(before[DATA_PATHS[3]],['investigations',INV],step)
    outputs[DATA_PATHS[4]]=replace_member(before[DATA_PATHS[4]],[INV],override)
    for path in [DATA_PATHS[0],DATA_PATHS[1],DATA_PATHS[3],DATA_PATHS[4]]:(ROOT/path).write_text(outputs[path])
    clear_catalog_caches();curriculum=Curriculum();reference=catalog.detail(curriculum,catalog.resolve(INV))['radiology_reference']
    galleries=[m for m in curriculum.node(MODULE)['lesson_media'] if m['kind']=='source-gallery' and INV in m['investigation_ids']]
    if not galleries or any(m['investigation_ids']!=[INV] for m in galleries):raise ValueError('Traumatic source lesson gallery scope changed')
    contract={k:reference.get(k) for k in item['source_contract_definition']};item['source_contract_sha256']=digest(contract)
    item['source_context_documents_sha256']=digest(reference['source_context_documents'])
    validate_reporting_snapshots({'investigations':[item]},{INV:reference['reporting']})
    raw=upsert_array(before[DATA_PATHS[2]],['investigations'],[item],'investigation_id',lambda a:a['investigation_id']==INV)
    scoped_ids=json.loads(raw)['scope']['catalog_investigation_ids']
    if INV not in scoped_ids:raw=replace_member(raw,['scope','catalog_investigation_ids'],scoped_ids+[INV])
    outputs[DATA_PATHS[2]]=raw
    for path in DATA_PATHS:
        if unrelated_tokens(before[path],path,ids)!=unrelated_tokens(outputs[path],path,ids):
            raise ValueError('Unrelated JSON value token changed: '+str(path))
    (ROOT/DATA_PATHS[2]).write_text(outputs[DATA_PATHS[2]])
    nontrauma=catalog.detail(curriculum,catalog.resolve('ra.intracranial-haemorrhage'))['radiology_reference']
    if nontrauma!=nontrauma_before:raise ValueError('Nontraumatic investigation contract changed')
    scoped={'investigations':[item],'scope':{'catalog_investigation_ids':[INV]},'clinical_validation_status':'draft_requires_neuroradiologist_review'}
    result=audit(scoped,{'assets':assets},ROOT,expected_catalog_ids={INV});parts=len(requirements_for(item));obligations=3*parts
    if result['counts']!={'verified':0,'unverified':0,'missing':obligations}:raise ValueError('Unexpected source anatomy coverage')
    receipt={'reviewed_at':DATE,'investigation_id':INV,'module_id':MODULE,'source_metadata_sha256':PINNED,
        'independent_review_sha256':INDEPENDENT_SHA,'registered_image_ids':sorted(ids),'registered_source_context_document_ids':[d['id'] for d in context['documents']],
        'public_source_files':media,'public_source_bytes':38875353,'source_pixels_or_native_original_files_modified':False,
        'source_context_schema_normalizations':normalizations,'nontraumatic_effective_reference_unchanged':True,
        'nontraumatic_effective_reference_sha256':digest(nontrauma),'nontraumatic_contract_excludes_shared_lesson_gallery_addition':True,
        'shared_lesson_gallery_scope':[INV],'effective_report_contract':contract,'effective_report_contract_sha256':item['source_contract_sha256'],
        'source_context_documents':copy.deepcopy(reference['source_context_documents']),
        'source_context_documents_sha256':item['source_context_documents_sha256'],
        'named_requirement_groups':len(item['structures']),'named_required_parts_floor':parts,'representation_obligations_floor':obligations,
        'scoped_fidelity_counts':result['counts'],'full_patient_denominator_known':False,
        'clinical_approval':False,'fine_anatomical_approval':False,'structure_coverage_granted':False,'patient_specific_3D_approved':False,
        'source_examples_do_not_autofill_patient_findings':True,'all_five_walkthrough_presets_are_unfilled_assessment_prompts':True,
        'all_unrelated_JSON_value_tokens_unchanged':True,
        'unrelated_token_fingerprints':{str(p):unrelated_tokens(before[p],p,ids) for p in DATA_PATHS},
        'root_owned_pending':['Source Blob/CSP/authenticated reader verification','Shared source-fidelity inventory refresh','Release/production verification']}
    (ROOT/RECEIPT).write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'images':len(images),'documents':len(context['documents']),'groups':len(item['structures']),
                      'required_parts_floor':parts,'missing_representation_obligations':obligations,'clinical_approval':False}))
    return receipt


if __name__=='__main__':integrate()
