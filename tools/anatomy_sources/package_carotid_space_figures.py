#!/usr/bin/env python3
"""Integrate all licensed carotid-space masters with distinct schematic and source acquisition roles."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PIL import Image
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2];INV='ra.mri-neck-spaces';PREFIX='open-neck-spaces-pmc6377693-fig';URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC6377693/'
MRI_PANELS={2:['b'],3:['a','b'],4:['full_figure'],5:['a','b'],7:['a','b'],8:['a','b','c'],9:['b','c'],10:['a','b'],16:['full_figure'],17:['a','b','c'],20:['full_figure'],22:['full_figure']}
CT_PANELS={12:['a'],14:['a','b'],15:['b'],18:['b'],19:['a','b','c'],21:['a','b'],23:['a']}
EXTRA={2:{'CT':['a'],'Radiography':['c'],'Ultrasound':['d']},9:{'CT':['a']},10:{'CT':['c']},12:{'Ultrasound':['b']},15:{'Radiography':['a']},18:{'Ultrasound':['a']},23:{'Ultrasound':['b']}}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(source):
    proof_path=ROOT/'docs/carotid-space-published-source-review/original-source-review.json';proof=json.loads(proof_path.read_text());archive=proof_path.parent/'packaged-source-images.json'
    if proof['original_article_grant']!='CC BY 4.0' or not proof['all_23_complete_master_layouts_visually_inspected']:raise ValueError('Reviewed source rights/layout differs')
    replaced=json.loads(archive.read_text())['replaced_investigation_images'] if archive.exists() else catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference']['key_images'];rows=[];assets=[]
    for figure in proof['figures']:
        n=figure['figure_number'];ident=PREFIX+str(n);schematic=n in [1,6,11,13];modality='Schematic' if schematic else 'MRI' if n in MRI_PANELS else 'CT';panels=([ 'r1c1','r1c2'] if n in [11,13] else ['a','b'] if n==6 else ['full_figure']) if schematic else MRI_PANELS.get(n,CT_PANELS.get(n));types={p:modality for p in panels}
        for kind,extra in EXTRA.get(n,{}).items():types.update({p:kind for p in extra})
        raw=(source/'PMC6377693/original-PDF-masters'/figure['source_master_filename']).read_bytes()
        if sha(raw)!=figure['source_master_sha256']:raise ValueError('Reviewed original master changed')
        with Image.open(source/'PMC6377693/original-PDF-masters'/figure['source_master_filename']) as image:
            image.load();pixels=image.tobytes();profile=image.info.get('icc_profile')
            if sha(pixels)!=figure['decoded_pixel_sha256'] or image.size!=(figure['width'],figure['height']) or (sha(profile) if profile else None)!=figure['source_ICC_sha256']:raise ValueError('Original samples/profile differ')
        state='conceptual_source_diagram' if schematic else 'source_carotid_space_pathology_example';context={'setting':'conceptual' if schematic else 'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'conceptual' if schematic else 'local','depicted_state':state,'selected_panels':panels,'panel_types':types,'panel_states':{p:state for p in types},'source_case_groups':{'source_figure_'+str(n):list(types)},'different_figures_assumed_same_patient':False,'native_orientation_or_full_anatomical_extent_verified':False,'source_panels_independently_registered':False}
        if n in [11,13]:context.update(panel_identifier_scheme='grid_unlettered',panel_grid_rows=1,panel_grid_columns=2)
        if n==17:context['source_followup_months']={'c':4};context['followup_interval_approximate']=True
        if n==19:context['source_followup_days']={'a':0,'b':3};context['panel_c_chronology_not_independently_supplied']=True
        if n==21:context['source_supplied_biopsy_site']='Tongue-base lesion in panel b; not a new independent biopsy or HPV assay from pixels'
        if n==2:context['source_panel_d_contains_spectral_Doppler_tracing']=True
        specific={1:'Conceptual left carotid-space contents, not independently resolved native nerve/sheath anatomy.',6:'Conceptual nerve-tumour configurations, not tissue diagnosis or patient-specific 3D.',11:'Conceptual wall-layer/dissection interfaces; do not supply native patient wall thickness or dissection geometry.',13:'Conceptual pseudoaneurysm and wall-layer illustration, not native acquired adventitial boundaries.',14:'Source CTA injury case; static vocal-fold medialisation does not independently prove functional paralysis or a unique nerve injury.',17:'Source follow-up panel c approximately four months later; chronology is not registration or a guaranteed individual clinical response.',18:'Source Doppler/CT observations are separate acquisitions; static appearance alone is not a complete calibrated dynamic flow evaluation.',19:'Source CT panel b is three days after a; no independently supplied timing is invented for c. Source suppuration does not establish organism or drainability.',21:'Source reports biopsy of the tongue-base lesion; morphology does not independently establish source node histology, HPV status or a new patient primary.',23:'Source-labelled branchial cleft cyst; a cystic neck mass alone does not prove congenital benignity.'}.get(n,'Source-described selected lesion/compartment example; tissue identity is publication context, not new independent confirmation.')
        limits=specific+' Complete original selected views only; no every native fascia, nerve, vessel wall/lumen, node internal tissue, lesion interface, full neck extent or matched 3D patient is established. Source clinical labels and functions are not borrowed into another case.'
        attribution=', '.join(proof['original_author_names'])+'. Pathology of the carotid space. DOI '+proof['doi']+'. Figure '+str(n)+'. CC BY4.0. Original samples and embedded ICC retained; no enhancement/resampling. '+('Illustration credits: Nadezdha Kiriyak and Gwen Mack; original signatures retained. ' if schematic else '')+'No endorsement implied.'
        local=f'web/reference-media/radiology-open/neck-spaces-pmc6377693-fig{n}.png';(ROOT/local).write_bytes(raw)
        row={'id':ident,'kind':'schematic' if schematic else 'clinical-image','modality':modality,'figure_number':n,'src':'/app/'+local.removeprefix('web/'),'sha256':sha(raw),'width':figure['width'],'height':figure['height'],'source_url':URL,'figure_url':URL+'#Fig'+str(n),'asset_source_url':'https://pmc-oa-opendata.s3.amazonaws.com/PMC6377693.1/PMC6377693.1.pdf','clinical_panels':[] if schematic else panels,'source_context':context,'image_state':state,'caption':'Source Figure '+str(n)+': '+figure['source_caption_full'].split('.')[0]+'.','alt':'Complete source Figure '+str(n)+'. '+specific,'limits':limits,'source_caption_full':figure['source_caption_full'],'structures_visible':['Selected source carotid-space/adjacent structures; full native tissue boundaries unapproved'],'license':proof['original_article_grant'],'license_url':proof['license_url'],'attribution':attribution,'rights_reviewed_on':'2026-10-07','rights_review':'Original explicit article CC BY4; no figure-specific restrictive grant found. Acknowledged artwork credits/signatures retained.'}
        if schematic:row['schematic_panels']=panels
        if n in [11,13]:row['panel_identifier_scheme']='grid_unlettered'
        if EXTRA.get(n):row['ancillary_panels']=[{'kind':kind,'panels':extra,'structures_visible':['Separate source '+('projection angiography' if kind=='Radiography' else kind)+' context'],'limits':'Source acquisition differs from primary modality; no borrowed signal, calibrated geometry or current-patient physiological evaluation.'} for kind,extra in EXTRA[n].items()]
        catalog._validate_source_panel_roles(row);rows.append(row)
        assets.append({'id':ident,'kind':'schematic' if schematic else 'clinical_image','name':'Source carotid-space Figure '+str(n),'local_path':local,'sha256':sha(raw),'modality':modality,'investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':URL,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':{'name':proof['original_article_grant'],'url':proof['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-07'}},'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':sha(pixels),'original_source_ICC_preserved':bool(profile),'source_PDF_object':figure['source_PDF_object'],'highest_resolution_acquired_master_verified':True},'anatomical_review':{'status':'pending','reason':'Selected source examples/conceptual artwork do not establish full actual neck/tiny tissue interfaces, native registration, physiological or diagnostic certainty.'},'visual_review':{'status':'source_checked','sha256':sha(raw),'evidence_path':'docs/carotid-space-published-source-review.md','reviewed_at':'2026-10-07'}})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[INV]=[r for r in data.get(INV,[]) if not r['id'].startswith(PREFIX)]+rows;path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());data[INV]['key_images']=[];path.write_text(json.dumps(data,indent=2)+'\n')
    path=ROOT/'data/radiology/investigation-source-images.json';text=path.read_text()
    if '"'+INV+'"' in text:
        start=text.index('[',text.index('"'+INV+'"'));_,end=json.JSONDecoder().raw_decode(text,start);path.write_text(text[:start]+'[]'+text[end:])
    path=ROOT/'data/radiology/reporting-steps/head-neck.json';text=path.read_text();start=text.index('{',text.index('"'+INV+'"'));node,end=json.JSONDecoder().raw_decode(text,start);old={r['id'] for r in replaced};node['start']={'images':[PREFIX+'1'],'module_illustrations':False}
    for step in node['steps']:step['images']=[i for i in step.get('images',[]) if i not in old and not i.startswith(PREFIX)]
    selections={0:[1,2,5,9],1:[3,4,6,7,8,20,21,23],2:[2,5,9],3:[10,11,12,13,14,15,16,17,22],4:[18,19,20,21,23]}
    for index,numbers in selections.items():node['steps'][index]['images']=list(dict.fromkeys(node['steps'][index]['images']+[PREFIX+str(n) for n in numbers]))
    path.write_text(text[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+text[end:]);archive.write_text(json.dumps({'replaced_investigation_images':replaced,'published_figure_ids':[r['id'] for r in rows],'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)):value.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    for item in data['investigations']:
        if item['investigation_id']==INV:item['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    path.write_text(json.dumps(data,indent=2)+'\n');print('All 23 original figures integrated: four conceptual diagrams, separate primary/ancillary acquisitions and source timelines')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);a=p.parse_args();package(a.source_root)
