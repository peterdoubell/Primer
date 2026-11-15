#!/usr/bin/env python3
"""Integrate all complete licensed thyroid figure displays without granting anatomy coverage."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PIL import Image
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2];INV='ra.ultrasound-thyroid';PREFIX='open-thyroid-pmc8864691-fig';URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC8864691/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(source):
    proof_dir=ROOT/'docs/thyroid-pictorial-source-review';original=json.loads((proof_dir/'original-source-review.json').read_text());display=json.loads((proof_dir/'PDF-display-review.json').read_text());visual=json.loads((proof_dir/'PDF-display-visual-review.json').read_text());meta=json.loads((proof_dir/'PMC8864691.1.json').read_text())
    if original['original_article_grant']!='CC BY 4.0' or display['original_PDF_sha256']!=original['original_PDF_sha256'] or sha((source/'PMC8864691.1.pdf').read_bytes())!=original['original_PDF_sha256']:raise ValueError('Original source/grant differs')
    rendered=source/'PDF-aware-display-review';profile=(rendered/'display-sRGB.icc').read_bytes()
    if sha(profile)!=display['display_sRGB_profile_sha256']:raise ValueError('Reviewed display profile differs')
    archive=proof_dir/'packaged-source-images.json'
    if archive.exists():replaced=json.loads(archive.read_text())['replaced_investigation_images']
    else:replaced=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference']['key_images']
    rows=[];assets=[]
    for source_figure,figure in zip(original['figures'],display['figures']):
        n=figure['figure_number'];ident=PREFIX+str(n);raw=(rendered/figure['display_file']).read_bytes()
        if sha(raw)!=figure['display_sha256'] or sha(raw)!=visual['figure_display_sha256s'][str(n)] or n!=source_figure['figure_number']:raise ValueError('Reviewed figure/display binding differs')
        with Image.open(rendered/figure['display_file']) as image:
            image.load();pixels=image.tobytes()
            if list(image.size)!=figure['dimensions'] or sha(pixels)!=figure['decoded_display_RGB_sha256'] or image.info.get('icc_profile')!=profile:raise ValueError('Display samples/profile differ')
        local=f'web/reference-media/radiology-open/thyroid-pmc8864691-fig{n}.png';(ROOT/local).write_bytes(raw)
        specific={3:'A visible halo does not independently identify a histological capsule.',12:'Source-described extension does not prove microscopic invasion or every adjacent organ interface.',17:'Shadowed contents remain unseen; source scoring assumptions do not establish the hidden physical material.',20:'Source-described extension does not independently prove microscopic or adjacent-organ invasion.',11:'The two source panels are not independently registered planes or a native volume.'}.get(n,'')
        limits='Selected source B-mode ultrasound example; source scores are educational descriptions, not a new diagnosis or management decision. No complete gland/node/adjacent-interface extent, cine/Doppler, acquisition calibration, matched serial case or 3D interiors is established. '+specific
        panels=['r1c1','r1c2'] if n==11 else ['full_figure'];context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local','depicted_state':'source_thyroid_nodule_example','selected_panels':panels,'panel_types':{p:'Ultrasound' for p in panels},'panel_states':{p:'source_thyroid_nodule_example' for p in panels},'source_case_groups':{'unlinked_source_figure_'+str(n):panels},'different_figures_assumed_same_patient':False,'native_orientation_or_full_anatomical_extent_verified':False}
        if n==11:context.update(panel_identifier_scheme='grid_unlettered',panel_grid_rows=1,panel_grid_columns=2,source_panels_independently_registered=False)
        caption=' '.join(source_figure['source_caption_full'].split());attribution='Pires AT et al. '+meta['title']+'. DOI '+meta['doi']+'. Figure '+str(n)+'. CC BY4.0. Derived display of the complete original PDF figure, with no anatomical edits. No endorsement implied.'
        asset_url=meta['pdf_url'].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
        row={'id':ident,'kind':'clinical-image','modality':'Ultrasound','figure_number':n,'src':'/app/'+local.removeprefix('web/'),'sha256':sha(raw),'width':figure['dimensions'][0],'height':figure['dimensions'][1],'source_url':URL,'figure_url':URL+'#f'+str(n),'asset_source_url':asset_url,'clinical_panels':panels,'source_context':context,'image_state':context['depicted_state'],'caption':'Source Figure '+str(n)+': '+caption.split('.')[0]+'.','alt':'Source thyroid ultrasound Figure '+str(n)+': '+caption.split('.')[0]+'.','limits':limits,'source_caption_full':caption,'structures_visible':['Source-local thyroid nodule appearance and displayed surrounding tissues; independent tissue-boundary review pending'],'license':original['original_article_grant'],'license_url':original['license_url'],'attribution':attribution,'rights_reviewed_on':'2026-10-07','rights_review':'Original XML CC BY4 and every caption reviewed; complete licensed derived PDF displays. No native patient-volume or clinical approval inferred.'}
        if n==11:row['panel_identifier_scheme']='grid_unlettered'
        catalog._validate_source_panel_roles(row);rows.append(row)
        assets.append({'id':ident,'kind':'clinical_image','name':'Source thyroid ultrasound Figure '+str(n),'local_path':local,'sha256':sha(raw),'modality':'Ultrasound','investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':URL,'figure_url':row['figure_url'],'asset_url':asset_url,'license':{'name':original['original_article_grant'],'url':original['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str((proof_dir/'original-source-review.json').relative_to(ROOT)),'evidence_sha256':sha((proof_dir/'original-source-review.json').read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-07'}},'pixel_provenance':{'source_pixels_changed':True,'change_reason':'PDF-aware colour/display rendering; no anatomical editing or post-render spatial resampling. RGB output is not unchanged native channel samples.','decoded_pixel_sha256':sha(pixels),'highest_resolution_acquired_master_verified':True,'source_original_PDF_object':figure['original_PDF_object'],'render_proof_path':str((proof_dir/'PDF-display-review.json').relative_to(ROOT)),'render_proof_sha256':sha((proof_dir/'PDF-display-review.json').read_bytes()),'display_ICC_sha256':sha(profile)},'anatomical_review':{'status':'pending','reason':'Selected stills and source scores do not establish each actual gland/nodule/node/internal tissue or adjacent interface.'},'visual_review':{'status':'source_checked','sha256':sha(raw),'evidence_path':'docs/thyroid-pictorial-source-review.md','reviewed_at':'2026-10-07'}})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[INV]=[r for r in data.get(INV,[]) if not r['id'].startswith(PREFIX)]+rows;path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());data[INV]['key_images']=[];path.write_text(json.dumps(data,indent=2)+'\n')
    path=ROOT/'data/radiology/investigation-source-images.json';text=path.read_text()
    if '"'+INV+'"' in text:
        start=text.index('[',text.index('"'+INV+'"'));_,end=json.JSONDecoder().raw_decode(text,start);path.write_text(text[:start]+'[]'+text[end:])
    path=ROOT/'data/radiology/reporting-steps/head-neck.json';text=path.read_text();start=text.index('{',text.index('"'+INV+'"'));node,end=json.JSONDecoder().raw_decode(text,start);old={r['id'] for r in replaced};node['start']={'images':[],'module_illustrations':False}
    for step in node['steps']:step['images']=[i for i in step.get('images',[]) if i not in old and not i.startswith(PREFIX)]
    for index,numbers in {0:[5],1:[1,2,3,9,21],2:list(range(1,22)),3:[12,20]}.items():node['steps'][index]['images']=list(dict.fromkeys(node['steps'][index]['images']+[PREFIX+str(n) for n in numbers]))
    path.write_text(text[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+text[end:]);archive.write_text(json.dumps({'replaced_investigation_images':replaced,'published_figure_ids':[r['id'] for r in rows],'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)):value.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    for item in data['investigations']:
        if item['investigation_id']==INV:item['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    path.write_text(json.dumps(data,indent=2)+'\n');print('21 complete licensed thyroid displays integrated with separate source contexts and pending anatomy review')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);a=p.parse_args();package(a.source_root)
