#!/usr/bin/env python3
"""Integrate complete licensed figures with explicit normal/schematic/mixed modality roles."""
import argparse,hashlib,json,sys,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PIL import Image
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2];INV='ra.mri-trigeminal';PREFIX='open-trigeminal-pmc6420596-fig';URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC6420596/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(source):
    proof_path=ROOT/'docs/trigeminal-published-source-review/original-source-review.json';proof=json.loads(proof_path.read_text());archive=proof_path.parent/'packaged-source-images.json'
    if proof['original_article_grant']!='CC BY 4.0' or not proof['selected_complete_masters_visually_inspected']:raise ValueError('Reviewed original source grant/layout differs')
    xml=(source/'PMC6420596.1.xml').read_bytes()
    if sha(xml)!=proof['original_XML_sha256']:raise ValueError('Original author metadata differs')
    authors=', '.join(' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in E.fromstring(xml).findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name'))
    replaced=json.loads(archive.read_text())['replaced_investigation_images'] if archive.exists() else catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference']['key_images'];rows=[];assets=[]
    for figure in proof['figures']:
        n=figure['figure_number'];ident=PREFIX+str(n);path=source/'PMC6420596/original-PDF-masters'/figure['source_master_filename'];raw=path.read_bytes()
        if sha(raw)!=figure['source_master_sha256']:raise ValueError('Reviewed source master changed')
        with Image.open(path) as image:
            image.load();pixels=image.tobytes();profile=image.info.get('icc_profile')
            if sha(pixels)!=figure['decoded_pixel_sha256'] or image.size!=(figure['width'],figure['height']) or (sha(profile) if profile else None)!=figure['source_ICC_sha256']:raise ValueError('Original source samples/profile differ')
        modality='Schematic' if n==6 else 'CT' if n==19 else 'MRI';kind='schematic' if n==6 else 'clinical-image';state='normal_anatomical_reference' if n==1 else 'conceptual_trigeminal_schematic' if n==6 else 'source_trigeminal_pathology_example'
        panels={1:['E'],6:['full_figure'],12:['A','B'],13:['C'],19:['A','B','C'],20:['full_figure'],21:['A','B'],22:['A'],28:['A']}[n]
        types={p:modality for p in panels}
        if n==1:types={p:'MRI' for p in 'ABCDEFGHIJ'}
        if n==13:types.update(A='CT',B='CT')
        if n in [22,28]:types['B']='MRI'
        context={'setting':'conceptual' if n==6 else 'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'conceptual' if n==6 else 'local','depicted_state':state,'selected_panels':panels,'panel_types':types,'panel_states':{p:state for p in types},'different_figures_assumed_same_patient':False,'native_orientation_or_full_anatomical_extent_verified':False,'source_panels_independently_registered':False}
        if n==1:context['source_case_groups']={p:[p] for p in types};context['normal_panels_assumed_same_patient']=False
        else:context['source_case_groups']={'source_figure_'+str(n):list(types)}
        if n==19:context['source_followup_months']={'A':0,'B':6,'C':12}
        if n==21:context['source_branch_caption_discrepancy']={'division_name':'mandibular','source_division_number':'V2','resolved':False}
        if n in [22,28]:context['nonselected_panels']={'B':'Source facial/vestibulocochlear context; not trigeminal coverage'}
        specific=proof['source_semantic_limits'].get('Fig'+str(n),'Source-local selected views; diagnosis is publication context, not independent tissue confirmation.')
        limits=specific+' Complete original figure only; no full native nerve/fascicle/vessel/CSF/dural boundaries, calibrated acquired volume, physiological function, matched 3D patient or current-patient diagnosis is established.'
        attribution=authors+'. Imaging of cranial nerves: a pictorial overview. DOI '+proof['doi']+'. Figure '+str(n)+'. CC BY4.0. Complete original PDF samples and embedded RGB ICC profile retained without enhancement/resampling. No endorsement implied.'
        local=f'web/reference-media/radiology-open/trigeminal-pmc6420596-fig{n}.png';(ROOT/local).write_bytes(raw)
        row={'id':ident,'kind':kind,'modality':modality,'figure_number':n,'src':'/app/'+local.removeprefix('web/'),'sha256':sha(raw),'width':figure['width'],'height':figure['height'],'source_url':URL,'figure_url':URL+'#Fig'+str(n),'asset_source_url':'https://pmc-oa-opendata.s3.amazonaws.com/PMC6420596.1/PMC6420596.1.pdf','clinical_panels':[] if n==6 else panels,'source_context':context,'image_state':state,'caption':'Source Figure '+str(n)+': '+figure['source_caption_full'].split('.')[0]+'.','alt':'Source complete Figure '+str(n)+'; '+specific,'limits':limits,'source_caption_full':figure['source_caption_full'],'structures_visible':['Source-described selected trigeminal/adjacent anatomy; complete tissue boundaries unapproved'],'license':proof['original_article_grant'],'license_url':proof['license_url'],'attribution':attribution,'rights_reviewed_on':'2026-10-07','rights_review':'Explicit original XML CC BY4 grant and complete selected captions reviewed; no separate figure restriction found.'}
        if n==6:row['schematic_panels']=panels
        if n==13:row['ancillary_panels']=[{'kind':'CT','panels':['A','B'],'structures_visible':['Source soft-tissue and bone-window context'],'limits':'Separate CT views; not MRI signal, registered volume or every nerve/vessel interface.'}]
        catalog._validate_source_panel_roles(row);rows.append(row)
        assets.append({'id':ident,'kind':'schematic' if n==6 else 'clinical_image','name':'Source trigeminal Figure '+str(n),'local_path':local,'sha256':sha(raw),'modality':modality,'investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':URL,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':{'name':proof['original_article_grant'],'url':proof['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-07'}},'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':sha(pixels),'original_source_ICC_preserved':bool(profile),'source_PDF_object':figure['source_PDF_object'],'highest_resolution_acquired_master_verified':True},'anatomical_review':{'status':'pending','reason':'Selected reference/pathology/conceptual material does not prove all tiny central/peripheral anatomy, native registration, tissue identity or current patient disease.'},'visual_review':{'status':'source_checked','sha256':sha(raw),'evidence_path':'docs/trigeminal-published-source-review.md','reviewed_at':'2026-10-07'}})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[INV]=[r for r in data.get(INV,[]) if not r['id'].startswith(PREFIX)]+rows;path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());data[INV]['key_images']=[];path.write_text(json.dumps(data,indent=2)+'\n')
    path=ROOT/'data/radiology/investigation-source-images.json';text=path.read_text()
    if '"'+INV+'"' in text:
        start=text.index('[',text.index('"'+INV+'"'));_,end=json.JSONDecoder().raw_decode(text,start);path.write_text(text[:start]+'[]'+text[end:])
    path=ROOT/'data/radiology/reporting-steps/head-neck.json';text=path.read_text();start=text.index('{',text.index('"'+INV+'"'));node,end=json.JSONDecoder().raw_decode(text,start);old={r['id'] for r in replaced};node['start']={'images':[PREFIX+'6'],'module_illustrations':False}
    for step in node['steps']:step['images']=[i for i in step.get('images',[]) if i not in old and not i.startswith(PREFIX)]
    for index,figures in {0:[22,28],1:[1],2:[12,13],3:[6,13,20],4:[6,19,20,21]}.items():node['steps'][index]['images']=list(dict.fromkeys(node['steps'][index]['images']+[PREFIX+str(n) for n in figures]))
    path.write_text(text[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+text[end:]);archive.write_text(json.dumps({'replaced_investigation_images':replaced,'published_figure_ids':[r['id'] for r in rows],'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)):value.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    for item in data['investigations']:
        if item['investigation_id']==INV:item['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    path.write_text(json.dumps(data,indent=2)+'\n');print('Nine original figures integrated with explicit normal/schematic/MRI/CT/timepoint roles')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);a=p.parse_args();package(a.source_root)
