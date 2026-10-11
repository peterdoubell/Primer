"""Bounded stroke source/reporting integration, preserving unrelated JSON tokens.

The CTP publication's source GO is independent from native ISLES'22 redistribution
NO-GO. No source example, array, mask or generic brain mesh gains anatomy credit.
Only the five fixed data files below may be changed by this tool.
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
from tools.anatomy_sources.integrate_myelopathy_sources import object_members,member,array_values,replace_member,add_member,upsert_array,clear_catalog_caches as clear_core_catalog_caches
from tools.check_msk_fidelity import audit,requirements_for,validate_reporting_snapshots,inspect_binding
from tools.check_radiology_fidelity import digest

INV='ra.acute-stroke';MODULE='rad.4.stroke';DATE='2026-10-11'
FOLDER=Path('docs/acute-stroke-source-review-20261011')
PREFIX='open-acute-stroke-ctp2023-fig'
FIG=lambda n:PREFIX+str(n)
DATA_PATHS=[Path('data/radiology/'+n) for n in ('radiology-open-images.json','radiology-asset-evidence.json','non-msk-structure-requirements.json','reporting-steps/neuroradiology.json','investigation-overrides-non-msk.json')]
ORIGINAL_RECEIPT=FOLDER/'runtime-data-integration-20261011.json'
ORIGINAL_RECEIPT_SHA='af4b98a3e40d2158c425abce296ff18569c45414518dec31f7cfe2063ca7ced3'
RECEIPT=FOLDER/'runtime-data-integration-caption-complete-20261011.json'
PINNED={'ctp-final-integration-proposal.json': 'df1debaec552d12bbb9af778cdd2ac7a2c9e7597fea2b70071986504afabe368', 'structure-requirements-proposal.json': '919ab2b64c2854edcf74dc2e7274bc1611edae03ddc0f8db76b88900705eba16', 'isles22-rights-conflict-amendment-20261011.json': '7c1900c929104220cc7df7c7bcddf0065ef03b9ebfb0ed15b04a4ce1c083f62a'}
PRIMARY=[
 {'id':'stroke-ctp2023','title':'Cerebral CTP acute stroke and mimic source pictorial review (2023)','url':'https://doi.org/10.3390/diagnostics13030447','headings':['CT and CTP source cases','Posterior fossa and inflow disease','Mimics and acquisition artefacts','Published source processing limits']},
 {'id':'stroke-AHA-ASA2026','title':'AHA/ASA guideline for early management of acute ischaemic stroke (2026)','url':'https://www.ahajournals.org/doi/10.1161/STR.0000000000000513','headings':['Brain and vascular imaging','Actual time and clinical eligibility','Predicted core and reperfusion selection']},
 {'id':'stroke-AHA-CVT2024','title':'AHA cerebral venous thrombosis scientific statement (2024)','url':'https://www.ahajournals.org/doi/10.1161/STR.0000000000000456','headings':['Venous imaging and diagnostic limits','Venous infarction and haemorrhage','Confirmed diagnosis and clinical management']},
]
STEP_IMAGES={0:[FIG(n) for n in [1,2,4,5,6,7]],1:[FIG(5),FIG(8),FIG(11)],2:[FIG(n) for n in [1,3,4,7,9,10,11]],3:[FIG(n) for n in [1,2,3,4,6,7,9,10,11,12,13]],4:[FIG(5),FIG(8),FIG(12),FIG(13)]}
NORMAL_PROMPTS=[
 'Actual parenchymal findings [ ]; side/territory and each involved structure [ ]; applicable ASPECTS modality, side, affected regions and score [ ]; unassessed extent [ ].',
 'Actual blood by compartment, side/site and extent [ ]; haemorrhagic transformation [ ]; susceptibility/CT limits and unassessed compartments [ ].',
 'Actual arterial occlusion by artery/segment, proximal/distal extent and reconstitution [ ]; tandem cervical lesion, stenosis/dissection and acquisition limits [ ]; venous question/venography if acquired [ ].',
 'Actual CTA phases and collateral filling extent/delay [ ]; perfusion acquisition/quality/coverage [ ]; software/thresholds and estimates in mL [ ]; unassessed tissue and processing limits [ ].',
 'Actual oedema, midline shift in mm with method/level/direction [ ]; cisterns, ventricles and herniation route [ ]; comparison and alternative findings [ ]; unresolved limits [ ].',
]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def clear_catalog_caches():
    clear_core_catalog_caches()
    from primer.module_media import radiology_source_bindings
    radiology_source_bindings.cache_clear()


def checked(path,expected):
    raw=(ROOT/path).read_bytes()
    if sha(raw)!=expected:raise ValueError('Frozen source evidence changed: '+str(path))
    return json.loads(raw)


INDEPENDENT=FOLDER/'independent-review.json'
INDEPENDENT_SHA='4af86b0db18667fd1b5af5e3c8244e7654828d4b2c0cfa5584de1b2f9deecde4'

def source_inputs():
    if not INDEPENDENT or not INDEPENDENT_SHA:raise ValueError('Final independent CTP review is pending')
    if not PINNED:raise ValueError('Final independent CTP pins are not installed')
    review=checked(INDEPENDENT,INDEPENDENT_SHA)
    result={n:checked(FOLDER/n,expected) for n,expected in PINNED.items()}
    proposal=result['ctp-final-integration-proposal.json'];scope=result['structure-requirements-proposal.json']
    rights=result['isles22-rights-conflict-amendment-20261011.json']
    if rights.get('native_candidate_public_or_runtime_binding_permitted') is not False:raise ValueError('Native redistribution NO-GO changed without new source authority')
    if len(proposal['images'])!=13 or {r['id'] for r in proposal['images']}!={FIG(n) for n in range(1,14)}:raise ValueError('Complete CTP source object scope required')
    if (review.get('investigation_id')!=INV or review.get('module_id')!=MODULE
            or review.get('verdict')!='GO_CTP_SOURCE_INTEGRATION_ONLY_NATIVE_PUBLICATION_NO_GO'
            or review.get('CTP',{}).get('source_integration_approved') is not True
            or set(review['CTP'].get('approved_display_ids',[]))!={FIG(n) for n in range(1,14)}
            or review['CTP'].get('final_integration_proposal_SHA256')!=PINNED['ctp-final-integration-proposal.json']
            or review.get('ISLES22_native_candidate',{}).get('publication_approved') is not False):raise ValueError('Independent decision or permitted source scope changed')
    for k in ('clinical_approval','fine_anatomical_approval','structure_coverage_granted','full_module_clinical_commercial_grade','whole_goal_complete'):
        if review.get(k) is not False:raise ValueError('Source review borrowed anatomical or clinical approval')
    if proposal['clinical_approval'] is not False or proposal['fine_anatomical_approval'] is not False:raise ValueError('Source packet borrowed clinical approval')
    folder=ROOT/'web/reference-media/radiology-open/acute-stroke';files=list(folder.iterdir())
    if len(files)!=27 or sum(p.stat().st_size for p in files)!=37429274:raise ValueError('Complete CTP packet altered')
    for path in files:
        pin=review['pins'].get(str(path.relative_to(ROOT)))
        if not pin or pin['sha256']!=sha(path.read_bytes()) or pin['bytes']!=path.stat().st_size:raise ValueError('Independently reviewed CTP source bytes changed')
    if scope['named_requirement_groups']!=369 or scope['named_required_parts_floor']!=3692 or scope['verified_representation_obligations']!=0:raise ValueError('Whole conditional stroke scope changed')
    for row in proposal['images']:
        path=ROOT/'web'/row['src'].removeprefix('/app/')
        if not row['src'].startswith('/app/reference-media/radiology-open/acute-stroke/') or sha(path.read_bytes())!=row['sha256']:raise ValueError('CTP source raster or path changed')
    return proposal,scope,review


def normalize_rows(proposal,review_path=None,review_sha=None):
    images=[];assets=[]
    laterality={1:'right',2:'right',3:'unknown',4:'left',5:'right',6:'bilateral',7:'right',8:'bilateral',9:'bilateral',10:'left',11:'left',12:'right',13:'unknown'}
    states={n:('source_ctp_motion_reprocessing_case' if n==13 else 'source_seizure_mimic_case' if n==12 else 'source_traumatic_circulatory_arrest_case' if n==8 else 'source_vascular_or_ischaemic_case') for n in range(1,14)}
    for n,original in enumerate(proposal['images'],1):
        row=copy.deepcopy(original);old=copy.deepcopy(row['source_context']);types={p:('MRI' if n==6 and p=='F' else 'CT') for p in old['panels']}
        if n==8:types['timeAttenuationCurve']='Haemodynamic tracing'
        selected=[p for p,t in types.items() if t=='CT'];row.update(kind='clinical-image',figure_number=n,figure_url=row['source_url']+'#fig'+str(n),
            structures_visible=[original['alt']],limits='Selected native publication sections/maps only; calibrated source CT Hounsfield values, full DICOM stacks, numerical perfusion time series/maps, source segmentation and patient meshes are absent. Printed thresholds do not establish current patient tissue viability. Figure6 next-day DWI is not registered to CT. Different numbered figures remain different source cases.',
            rights_review='CTP publication unrestricted CC BY4 grant and exact source byte/pixel packet checked; source permission does not establish clinical or fine anatomy approval.',rights_reviewed_on=DATE,
            clinical_panels=selected,panel_identifier_scheme='descriptive_source_positions',clinical_approval=False,fine_anatomical_approval=False,patient_specific_3D_approved=False)
        context={**old,'setting':'in_vivo','laterality':laterality[n],'population':{'life_stage':'unknown','case_context':'Individual age/development is not supplied by the original numbered caption; no cohort demographics substituted.'},'depicted_state':'mixed','extent':'local',
                 'panel_identifier_scheme':'descriptive_source_positions','selected_panels':selected,'panel_types':types,'panel_states':{p:states[n] for p in types},'original_panel_source_roles':copy.deepcopy(old['panels']),
                 'clinical_approval':False,'fine_anatomical_approval':False,'current_patient_findings':False,'native_patient_registration_verified':False,'fine_structure_coverage_granted':False,'patient_specific_3D_approved':False}
        row['source_context']=context;row['image_state']='mixed';row['ancillary_panels']=[]
        if n==6:row['ancillary_panels'].append({'kind':'MRI','panels':['F'],'structures_visible':['Next-day DWI source bilateral cerebellar lesion examples'],'limits':'Same caption source case on a later day, not registered to the CT/CTP panels; no ADC or full MRI stack is supplied in this publication figure.'})
        if n==8:row['ancillary_panels'].append({'kind':'Haemodynamic tracing','panels':['timeAttenuationCurve'],'structures_visible':['Source arterial, venous and bilateral parenchymal time-attenuation curves'],'limits':'A static source plot, not native recoverable time-series data or a current patient measurement.'})
        row['original_publication_pdf']=copy.deepcopy(proposal['source']['original_PDF']);row['original_publication_pdf']['src']='/app/reference-media/radiology-open/acute-stroke/ctp-2023-original-publication.pdf';row['original_publication_pdf']['unchanged_original']=True
        source_figure=proposal['source_figures'][n-1];row['native_source_objects']=[{k:o[k] for k in ('xref','width','height','encoded_stream_sha256','native_RGB_channels_sha256')} for o in source_figure['objects']]
        row['source_context_original_proof_relation']={'evidence_path':str(FOLDER/'ctp-final-integration-proposal.json'),'evidence_sha256':PINNED.get('ctp-final-integration-proposal.json','pending'),'original_source_context_sha256':digest(old),'schema_normalization_only':True}
        license_info={'name':'CC BY 4.0','url':row['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(FOLDER/'ctp-final-integration-proposal.json'),'evidence_sha256':PINNED.get('ctp-final-integration-proposal.json','pending'),'attribution':row['attribution'],'reviewed_at':DATE}
        visual={'status':'source_checked','sha256':row['sha256'],'reviewed_at':DATE,'anatomical_or_clinical_approval':False}
        if review_path:license_info.update(independent_review_path=review_path,independent_review_sha256=review_sha);visual.update(evidence_path=review_path,evidence_sha256=review_sha)
        asset={'id':row['id'],'kind':'clinical_image','name':row['title'],'local_path':'web/'+row['src'].removeprefix('/app/'),'sha256':row['sha256'],'regions':['brain'],'investigation_ids':[INV],'structure_ids':[],'modality':'CT','source_context':copy.deepcopy(context),'representation_selection':{'panels':selected},'requirement_coverage':{},
               'source':{'url':row['source_url'],'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':license_info},
               'pixel_provenance':{'acquisition':'Complete native PDF raster object or exact original top/bottom strip assembly; original streams and full PDF retained','original_PDF_sha256':proposal['source']['original_PDF']['sha256'],'native_RGB_pixels_changed':False,'source_geometry_changed':False,'cropped_resampled_or_repainted':False,'JPEG_decoder_rounding_disclosed':True,'highest_resolution_acquired_master_verified':False},
               'anatomical_review':{'status':'pending','reason':'Native artwork source checking does not establish complete fine anatomy, acquisition calibration, patient registration or complete source-native geometry.'},'visual_review':visual,'clinical_approval':False,'fine_anatomical_approval':False,'patient_specific_3D_approved':False,'runtime_registered':True}
        catalog._validate_source_panel_roles(row)
        if inspect_binding(asset,{'modality_scope':['CT','MRI'],'context_requirements':[]}):raise ValueError('Typed source context contradiction')
        # The authenticated reader exposes the exact complete original caption
        # under this field; keep original_caption and every source byte intact.
        row['source_caption_full']=row['original_caption']
        images.append(row);assets.append(asset)
    return images,assets


def report_override(reference):
    guide=copy.deepcopy(reference['reporting']);guide['reviewed_at']=DATE
    guide['protocol']=[
      'Record actual onset/last-known-well, deficit, examination times, prior treatment and comparison; identify every NCCT, CTA/MRA, perfusion, MRI or venographic component actually acquired with coverage and quality.',
      'Review NCCT for haemorrhage and parenchymal change; review actual arch-to-vertex vascular coverage/phase and each target segment. MRI requires DWI with ADC, FLAIR and susceptibility as acquired. Venous suspicion requires appropriate actual venographic assessment rather than dense blood alone.',
      'Check source perfusion motion, bolus, temporal sampling, truncation, coverage and processing before using estimates. Protocol/order and selection imaging follow the current clinical pathway and should avoid unnecessary reperfusion delay.'
    ]
    guide['checklist']=[
      {'label':'Haemorrhage','detail':'Assess each actually acquired parenchymal, subarachnoid, ventricular and extra-axial bleeding compartment, side/site and extent; distinguish haemorrhagic transformation and unassessed limits.'},
      {'label':'Parenchyma','detail':'Localise each acute or uncertain change by side, actual structure and vascular or venous distribution; describe applicable modality-specific MCA ASPECTS regions and separate prior injury or artefact.'},
      {'label':'Occlusion','detail':'Assess each actually acquired arterial segment, occlusion extent, reconstitution, tandem cervical disease, stenosis/dissection and variants; assess venous findings on appropriate venography when acquired.'},
      {'label':'Collaterals','detail':'Describe actual acquisition phases, collateral spatial extent and relative delay; retain coverage/flow/processing limitations before describing software-defined perfusion estimates.'},
      {'label':'Tissue and complications','detail':'Assess each actual injury/estimated tissue region, oedema, shift, cisterns, ventricular obstruction, herniation, comparison and alternative diagnosis without inferring viability or current-patient findings from source examples.'},
    ]
    guide['measurements']=[
      {'name':'ASPECTS','method':'On an applicable MCA-territory source examination record CT or DWI modality, side, each of the ten assessed regions and acute change; score 10 minus affected regions. Retain old lesions, artefacts and unassessed regions.','pitfall':'MCA ASPECTS is not a posterior circulation score, exact core volume, tissue viability assay or independent treatment rule.'},
      {'name':'Perfusion volumes','method':'Only when acquisition/processing is adequate, record software/version, thresholds/units, estimated core and delayed region volumes in mL, mismatch volume and ratio with actual scope and uncertainty.','pitfall':'Static colour maps are not numerical source maps. Motion, bolus, delay, truncation, coverage and platform effects can invalidate estimates; predicted core does not mean wholly irreversible tissue.'},
      {'name':'Vascular calibre and extent','method':'Name the actual vessel/segment, proximal/distal lesion extent, native calibrated measurement plane, stenosis convention/reference vessel and luminal/wall findings actually resolved.','pitfall':'Do not infer vessel patency from missing acquisition, a generic mesh, a dense vessel or apparent absence on a single phase. Flow, bolus and variant anatomy can mimic occlusion.'},
      {'name':'Midline shift and ventricular effect','method':'Measure current-study shift in mm with direction, stated anatomical level and ideal-midline method; assess each acquired ventricular/cisternal compartment and obstruction/effacement.','pitfall':'Selected publication slices do not establish complete extent, patient calibration, a current shift measurement or hydrocephalus.'},
    ]
    guide['classification']={'name':'ASPECTS','version':'Ten-region MCA assessment; specify NCCT or DWI application','applicability':'An applicable MCA-territory examination, with actual side, regions and acquisition stated.','summary':'Name each affected and unassessed region with the score; keep posterior circulation and perfusion separate. Treatment selection uses the actual clinical pathway.'}
    guide['pitfalls']=[
      'Normal early CT or an initially negative DWI does not exclude clinically consistent stroke; small/posterior lesions and acquisition limits require context.',
      'DWI/ADC/FLAIR evolution varies. DWI–FLAIR mismatch is selection context, not an exact onset clock or an automatic treatment decision.',
      'Predicted core and delayed tissue are imaging/processing estimates; low CBF, diffusion restriction and hypoattenuation do not prove wholly irreversible tissue.',
      'Single-phase CTA can miss delayed filling. Collateral status does not justify avoidable delay or independently exclude reperfusion assessment.',
      'Arterial and venous infarction can both be haemorrhagic. Dense sinus or nonterritorial injury raises a venous question; actual CTV/MRV and the clinical pathway establish the assessment.',
      'Source cases, next-day DWI, motion/reprocessing plots and separate source patients are teaching context. They neither register to one another nor autofill the current patient report.',
    ]
    guide['impression_prompts']=['State each actual haemorrhage or ischaemic/uncertain lesion with side/site, extent and acquisition limitations.','State each actual target arterial or venous finding, tissue/collateral estimates and urgent complication; distinguish acquired findings from unassessed questions.','Communicate the actual time-sensitive imaging question to the stroke team using current clinical/time/imaging eligibility; source scores or estimates alone do not determine treatment.']
    guide['escalation']=['Promptly communicate acute haemorrhage, target-vessel occlusion, suspected significant venous thrombosis or threatening oedema/herniation with actual finding, limits, recipient and time.']
    guide['template_sections']=[
      {'heading':'BRAIN PARENCHYMA','body':'Each actual lesion/change: [side, structure, distribution, extent and uncertainty]. Prior injury/artefact: [ ]. Applicable ASPECTS: [modality, side, regions assessed/affected/unassessed, __/10]. MRI sequences/timepoint and limits: [ ].'},
      {'heading':'HAEMORRHAGE','body':'Each actual collection: [compartment, side/site, extent]. Haemorrhagic transformation: [ ]. Acquired susceptibility/CT coverage and unresolved limits: [ ].'},
      {'heading':'ARTERIAL FINDINGS','body':'Each arterial lesion: [vessel/segment, proximal/distal extent, reconstitution and acquisition phase/quality]. Tandem cervical disease, stenosis convention/calibre and resolved dissection findings: [ ]. Variants/access coverage: [ ]. Venous question and actual CTV/MRV/venous findings if acquired: [ ]; unassessed venous extent: [ ].'},
      {'heading':'COLLATERALS AND PERFUSION','body':'Actual CTA phases/coverage: [ ]. Collateral filling extent and relative delay: [ ]. Perfusion acquisition and quality: [ ]. Software/version, thresholds/units: [ ]. Estimated core __ mL; delayed region __ mL; mismatch volume/ratio [ ]; validity and unassessed extent: [ ].'},
      {'heading':'MASS EFFECT AND OTHER FINDINGS','body':'Oedema/swelling by site: [ ]. Shift __ mm toward [ ], at [level], using [method]. Each cisternal/ventricular effect or obstruction: [ ]. Herniation route: [ ]. Actual comparable prior/timepoint: [ ]. Alternative diagnosis and remaining uncertainty: [ ].'},
    ]
    sources=[{k:r[k] for k in ('title','url')} for r in PRIMARY]
    guide['sources']=[*guide['sources'],*[r for r in sources if r['url'] not in {s['url'] for s in guide['sources']}]]
    override={'reporting':guide,'reading':[*copy.deepcopy(reference['reading']),*[copy.deepcopy(r) for r in PRIMARY if r['url'] not in {v['url'] for v in reference['reading']}]],'additional_sources':sources,'key_images':[],'suppress_visual_fallback':True,
      'overview':'Assess the actually acquired stroke examination by haemorrhage, source-resolved tissue, arterial/venous findings, collateral/perfusion technique and complications. Keep source examples, estimated tissue and unassessed questions separate from the current patient.',
      'learning_points':['Record actual acquisition coverage, timing and limitations before interpreting tissue or vessels.','Read each actual lesion and applicable ASPECTS region; a generic brain label does not supply complete territory anatomy.','Name each actual vessel/segment and distinguish acquired lumen/wall findings from unassessed arterial or venous questions.','Interpret perfusion/collateral estimates with technique, processing and clinical context; avoid deterministic viability or clock claims.','Use complete licensed source artwork as context; different patients and next-day MRI remain unregistered examples.']}
    if reference.get('spatial_model'):
        override['spatial_model']=copy.deepcopy(reference['spatial_model']);override['spatial_model']['population_note']='Gross source anatomy for orientation only. The generic model does not supply complete patient-specific vascular, venous, ASPECTS, lesion or fine-structure geometry; named reporting coverage remains unverified.'
    return override


def walkthrough(existing,guide):
    result=copy.deepcopy(existing);result.update(walkthrough_reviewed_at=DATE,preset_mode='assessment-prompts',clinical_approval=False,fine_anatomical_approval=False,start={'images':[FIG(1),FIG(3),FIG(13)],'module_illustrations':False})
    looks=['All actual NCCT brain regions in appropriate windows; MRI DWI/ADC/FLAIR and susceptibility if acquired; record exact lesion, old injury, territory and the applicable ten MCA regions.','Every acquired parenchymal, sulcal/cisternal, ventricular and extra-axial compartment; state each side/site and extent or unresolved question.','Actual arch-to-vertex coverage, cervical and intracranial segments, lesion/reconstitution and variant/access anatomy; appropriate venographic source when the venous question is assessed.','Actual single/multiphase CTA filling and delay; inspect motion, bolus, truncation, coverage and processing before interpreting actual perfusion maps.','Actual midline/level and calibrated shift method, each basal cistern/ventricle and posterior-fossa pathway, swelling/herniation, prior comparison and alternatives.']
    findings=[['Actual lesion/change at [side/site], distribution/extent [ ]; sequences/acquisition and uncertainty [ ].','Applicable ASPECTS [modality/side]: affected/unassessed regions [ ]; score __/10.'],['Actual blood in [compartment/side/site], extent [ ]; transformation [ ]; unresolved limits [ ].'],['Actual [vessel/segment] lesion [ ], proximal/distal extent [ ], reconstitution [ ]; tandem disease/stenosis/dissection [ ].','Actual venographic findings or unassessed venous question [ ].'],['Actual collateral phases/filling extent/delay [ ]; acquisition limits [ ].','Valid software-defined estimates [software/version/thresholds]: core __ mL, delayed region __ mL, mismatch [ ]; limitations [ ].'],['Actual shift __ mm toward [ ] at [level/method]; ventricular/cisternal effect, obstruction or herniation [ ].','Comparable prior/timepoint and alternative findings [ ]; uncertainty [ ].']]
    measurements=[['ASPECTS'],[],['Vascular calibre and extent'],['Perfusion volumes'],['Midline shift and ventricular effect']]
    order=[1,0,2,3,4]
    for i,s in enumerate(result['steps']):
        s.setdefault('original_normal_report_statement',copy.deepcopy(s.get('normal')))
        s.update(detail=guide['checklist'][order[i]]['detail'],normal={s['sections'][0]:NORMAL_PROMPTS[i]},findings=findings[i],images=STEP_IMAGES[i],parts=[],look=looks[i],measurements=measurements[i],tip=guide['pitfalls'][[0,4,4,3,5][i]],clinical_approval=False)
    return result


def updated_scope(original,guide,node):
    value=copy.deepcopy(original);value.update(reporting_checklist=copy.deepcopy(guide['checklist']),reporting_template_sections=copy.deepcopy(guide['template_sections']),runtime_integrated=True,modality_scope=['CT','MRI'],shared_curriculum_quiz_sha256=digest(node['quiz']))
    value['original_source_scope_proposal_sha256']=PINNED['structure-requirements-proposal.json'];value['original_shared_curriculum_quiz_sha256']=original['shared_curriculum_quiz_sha256']
    quizzes=[g for g in value['structures'] if g['tissue_class']=='curriculum_quiz_dependency']
    if len(quizzes)!=len(node['quiz']):raise ValueError('Every current assessed quiz dependency required')
    for g,q in zip(quizzes,node['quiz']):
        g['original_literal_curriculum_quiz']=copy.deepcopy(g['literal_curriculum_quiz']);g['literal_curriculum_quiz']=copy.deepcopy(q)
    for g in value['structures']:
        g['original_modality_scope']=copy.deepcopy(g['modality_scope']);g['modality_scope']=['CT','MRI']
        g['source_sequence_phase_conditions']=g['original_modality_scope']
        for ref in g['report_refs']:
            ref.update(copy.deepcopy(guide['checklist'][ref['checklist_index']]))
        if any(g.get(k) is not False for k in ('clinical_approval','fine_anatomical_approval','structure_coverage_granted')):raise ValueError('Source anatomy credit forbidden')
    return value


def unrelated_tokens(raw,path,ids):
    result={}
    if path in (DATA_PATHS[0],DATA_PATHS[4]):
        for k,v,a,b in object_members(raw):
            if k!=INV:result[k]=sha(raw[a:b].encode())
    elif path in (DATA_PATHS[1],DATA_PATHS[2]):
        field='assets' if path==DATA_PATHS[1] else 'investigations';_,a,b=member(raw,[field])
        for value,token in array_values(raw,a,b):
            key=value['id'] if field=='assets' else value['investigation_id']
            if (key not in ids if field=='assets' else key!=INV):result[field+':'+key]=sha(token.encode())
        for k,v,a,b in object_members(raw):
            if k not in {field,'scope'}:result['top:'+k]=sha(raw[a:b].encode())
        if field=='investigations':
            _,a,_=member(raw,['scope'])
            for k,v,c,d in object_members(raw,a):
                if k!='catalog_investigation_ids':result['scope:'+k]=sha(raw[c:d].encode())
            _,a,b=member(raw,['scope','catalog_investigation_ids'])
            for value,token in array_values(raw,a,b):
                if value!=INV:result['catalog:'+value]=sha(token.encode())
    else:
        for k,v,a,b in object_members(raw):
            if k!='investigations':result['top:'+k]=sha(raw[a:b].encode())
        _,a,_=member(raw,['investigations'])
        for k,v,c,d in object_members(raw,a):
            if k!=INV:result[k]=sha(raw[c:d].encode())
    return result


def nonstroke_contracts(curriculum):
    result={}
    for item in catalog.catalogue()['investigations']:
        if item['id']==INV:continue
        ref=catalog.detail(curriculum,item)['radiology_reference'];result[item['id']]=digest({k:ref[k] for k in ('reporting','report_templates','walkthrough','reading')})
    return result


def integrate():
    proposal,original_scope,review=source_inputs();images,assets=normalize_rows(proposal,str(INDEPENDENT),INDEPENDENT_SHA);ids={r['id'] for r in images};before={p:(ROOT/p).read_text() for p in DATA_PATHS}
    clear_catalog_caches();curriculum=Curriculum();reference=catalog.detail(curriculum,catalog.resolve(INV))['radiology_reference'];nonstroke_before=nonstroke_contracts(curriculum)
    override=report_override(reference);guide=override['reporting'];steps=walkthrough(json.loads(before[DATA_PATHS[3]])['investigations'][INV],guide);scope=updated_scope(original_scope,guide,curriculum.node(MODULE));outputs={}
    raw=before[DATA_PATHS[0]];outputs[DATA_PATHS[0]]=replace_member(raw,[INV],images) if INV in json.loads(raw) else add_member(raw,[],INV,images)
    outputs[DATA_PATHS[1]]=upsert_array(before[DATA_PATHS[1]],['assets'],assets,'id',lambda a:a['id'] in ids)
    step_raw=replace_member(before[DATA_PATHS[3]],['investigations',INV],steps)
    # Repository step files are canonical. Existing unrelated entries already
    # have that format; the subsequent exact token guard rejects any drift.
    outputs[DATA_PATHS[3]]=json.dumps(json.loads(step_raw),indent=2,ensure_ascii=False)+'\n'
    raw=before[DATA_PATHS[4]];outputs[DATA_PATHS[4]]=replace_member(raw,[INV],override) if INV in json.loads(raw) else add_member(raw,[],INV,override)
    # Preview four files reversibly to obtain the actual authoritative contract.
    try:
        for p in (DATA_PATHS[0],DATA_PATHS[1],DATA_PATHS[3],DATA_PATHS[4]):(ROOT/p).write_text(outputs[p])
        clear_catalog_caches();current=Curriculum();ref=catalog.detail(current,catalog.resolve(INV))['radiology_reference']
        contract={k:ref[k] for k in scope['source_contract_definition']};scope['source_contract_sha256']=digest(contract)
        validate_reporting_snapshots({'investigations':[scope]},{INV:ref['reporting']})
        raw=upsert_array(before[DATA_PATHS[2]],['investigations'],[scope],'investigation_id',lambda x:x['investigation_id']==INV);scope_ids=json.loads(raw)['scope']['catalog_investigation_ids']
        if INV not in scope_ids:raw=replace_member(raw,['scope','catalog_investigation_ids'],scope_ids+[INV])
        outputs[DATA_PATHS[2]]=raw
        for p in DATA_PATHS:
            if unrelated_tokens(before[p],p,ids)!=unrelated_tokens(outputs[p],p,ids):raise ValueError('Unrelated JSON value token changed: '+str(p))
        nonstroke_after=nonstroke_contracts(current)
        if nonstroke_before!=nonstroke_after:raise ValueError('An unrelated effective report contract changed')
        result=audit({'investigations':[scope],'scope':{'catalog_investigation_ids':[INV]},'clinical_validation_status':'draft_requires_neuroradiologist_review'},{'assets':assets},ROOT,expected_catalog_ids={INV})
        parts=len(requirements_for(scope))
        if result['counts']!={'verified':0,'unverified':0,'missing':parts*3}:raise ValueError('Source packet borrowed anatomy coverage')
        for p in DATA_PATHS:(ROOT/p).write_text(outputs[p])
    except BaseException:
        for p in DATA_PATHS:(ROOT/p).write_text(before[p])
        clear_catalog_caches();raise
    receipt={'reviewed_at':DATE,'investigation_id':INV,'module_id':MODULE,'source_metadata_sha256':PINNED,'independent_review_path':str(INDEPENDENT),'independent_review_sha256':INDEPENDENT_SHA,'registered_image_ids':sorted(ids),'source_CTP_figure_count':13,'native_source_bound':False,'native_rights_conflict_NO_GO_retained':True,'CTP_source_pixels_or_originals_modified':False,
       'effective_report_contract':contract,'effective_report_contract_sha256':scope['source_contract_sha256'],'shared_curriculum_quiz_sha256':scope['shared_curriculum_quiz_sha256'],'original_source_quiz_snapshot_sha256':original_scope['shared_curriculum_quiz_sha256'],
       'named_requirement_groups':len(scope['structures']),'named_required_parts_floor':parts,'representation_obligations_floor':parts*3,'scoped_fidelity_counts':result['counts'],'full_patient_denominator_known':False,'clinical_approval':False,'fine_anatomical_approval':False,'structure_coverage_granted':False,'patient_specific_3D_approved':False,
       'all_five_report_actions_unfilled':True,'source_examples_do_not_autofill_patient_findings':True,'all_unrelated_JSON_value_tokens_unchanged':True,'unrelated_token_fingerprints':{str(p):unrelated_tokens(before[p],p,ids) for p in DATA_PATHS},'nonstroke_effective_contract_digests':nonstroke_after,'nonstroke_effective_contracts_unchanged':len(nonstroke_after),'data_file_SHA256':{str(p):sha((ROOT/p).read_bytes()) for p in DATA_PATHS},'root_owned_pending':['CTP source Blob routing/headers','Current source rights inventory','Shared curriculum repair and integrated reader verification','Release and production checks']}
    if sha((ROOT/ORIGINAL_RECEIPT).read_bytes())!=ORIGINAL_RECEIPT_SHA:raise ValueError('Frozen pre-caption data receipt changed')
    receipt.update(source_caption_full_exact_original_caption=True,complete_source_captions=13,
                   previous_runtime_data_receipt=str(ORIGINAL_RECEIPT),previous_runtime_data_receipt_sha256=ORIGINAL_RECEIPT_SHA)
    (ROOT/RECEIPT).write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n');clear_catalog_caches()
    print(json.dumps({'images':len(images),'groups':len(scope['structures']),'parts_floor':parts,'missing_obligations':parts*3,'nonstroke_contracts_unchanged':len(nonstroke_after),'native_source_bound':False}))
    return receipt
if __name__=='__main__':integrate()
