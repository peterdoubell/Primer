#!/usr/bin/env python3
"""Package the complete original VFSS FOV still; do not invent motion or normality."""
import argparse,hashlib,json,sys,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PIL import Image
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2];INV='ra.swallowing';IDENT='open-swallowing-pmc12081525-fig2';URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC12081525/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(source):
    proof_path=ROOT/'docs/swallowing-published-source-review/original-source-review.json';proof=json.loads(proof_path.read_text());row=proof['figures'][0]
    if proof['original_article_grant']!='CC BY 4.0' or row['source_PDF_object']!=71 or row['source_PDF_page']!=6 or not row['explicit_original_PDF_page_binding_visually_reviewed']:raise ValueError('Original reviewed master binding differs')
    original=source/'PMC12081525/original-PDF-masters'/row['source_master_filename'];raw=original.read_bytes()
    if sha(raw)!=row['source_master_sha256']:raise ValueError('Original source master changed')
    with Image.open(original) as im:
        im.load()
        if sha(im.tobytes())!=row['decoded_pixel_sha256'] or im.size!=(1350,1022) or im.mode!='L':raise ValueError('Original grayscale samples changed')
    tree=E.fromstring((source/'PMC12081525.1.xml').read_bytes());authors=[]
    for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name'):authors.append(' '.join(filter(None,[n.findtext('given-names'),n.findtext('surname')])))
    attribution=', '.join(authors)+'. ESSD–ESGAR best practice position statements on adult VFSS technical performance. DOI 10.1007/s00330-024-11241-1. Figure 2. CC BY4.0. Original PDF grayscale samples retained without enhancement/resampling; no endorsement implied.'
    local='web/reference-media/radiology-open/swallowing-pmc12081525-fig2.png';(ROOT/local).write_bytes(raw)
    context={'setting':'in_vivo','laterality':'not_applicable','population':{'sex':'female','life_stage':'unknown','age_not_supplied':True},'extent':'local','depicted_state':'source_post_maxillofacial_trauma_and_reconstruction','selected_panels':['a','b'],'panel_types':{'a':'Radiography','b':'Radiography'},'panel_states':{'a':'source_post_maxillofacial_trauma_and_reconstruction','b':'source_post_maxillofacial_trauma_and_reconstruction'},'source_case_groups':{'source_female_Fig2':['a','b']},'source_projection_roles':{'a':'Lateral oropharyngeal VFSS field-of-view example','b':'Anteroposterior oropharyngeal VFSS field-of-view example'},'full_original_cine_or_DICOM_available':False,'frame_order_timestamps_or_frame_pulse_rates_supplied':False,'source_views_independently_registered':False,'still_implies_aspiration_absence_or_swallow_function':False,'source_case_is_normal_reference':False,'source_adult_consensus_is_patient_age_evidence':False}
    limits='Selected static source views after maxillofacial trauma/reconstruction; age not supplied. Field-of-view example only: no full original cine, source frame timing/rates, validated motion, aspiration exclusion, functional muscle/nerve mechanism, unique diagnosis or matched patient 3D. Original PDF and HTML have different encoded contrast; neither is enhanced or harmonised here.'
    image={'id':IDENT,'kind':'clinical-image','modality':'Radiography','figure_number':2,'src':'/app/'+local.removeprefix('web/'),'sha256':sha(raw),'width':1350,'height':1022,'source_url':URL,'figure_url':URL+'#Fig2','asset_source_url':'https://pmc-oa-opendata.s3.amazonaws.com/PMC12081525.1/PMC12081525.1.pdf','clinical_panels':['a','b'],'source_context':context,'image_state':context['depicted_state'],'caption':'Source Figure 2: lateral and frontal VFSS field-of-view stills after trauma and reconstruction; age not supplied.','alt':'Complete original grayscale source figure with lateral panel a and frontal panel b.','limits':limits,'source_caption_full':row['source_caption_full'],'structures_visible':['Source projection-local oral pharyngeal laryngeal and cervical esophageal field; all fine boundaries unapproved'],'license':proof['original_article_grant'],'license_url':proof['license_url'],'attribution':attribution,'rights_reviewed_on':'2026-10-08','rights_review':'Original article CC BY4; no figure-specific exception in XML. PDF page/caption and original master visually matched; no dynamic source inferred.'};catalog._validate_source_panel_roles(image)
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[INV]=[r for r in data.get(INV,[]) if r['id']!=IDENT]+[image];path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    asset={'id':IDENT,'kind':'clinical_image','name':'Original VFSS field-of-view source stills','local_path':local,'sha256':sha(raw),'modality':'Radiography','investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':URL,'figure_url':image['figure_url'],'asset_url':image['asset_source_url'],'license':{'name':proof['original_article_grant'],'url':proof['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-08'}},'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':row['decoded_pixel_sha256'],'source_PDF_object':71,'source_PDF_page':6,'source_pixel_mode':'L','highest_resolution_acquired_master_verified':True,'HTML_PDF_encoded_contrast_difference_preserved':True},'anatomical_review':{'status':'pending','reason':'Two FOV stills do not establish all tissues or actual temporal swallowing events.'},'visual_review':{'status':'source_checked','sha256':sha(raw),'evidence_path':'docs/swallowing-published-source-review/source-review.md','reviewed_at':'2026-10-08'}};append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',[asset],prefix='open-swallowing-pmc12081525-')
    archive=proof_path.parent/'replaced-investigation-images.json'
    if not archive.exists():archive.write_text(json.dumps({'replaced_investigation_images':catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference']['key_images'],'reason':'Unreviewed remote stills and captions do not establish licensed original cine or every observed event.'},indent=2)+'\n')
    old={r['id'] for r in json.loads(archive.read_text())['replaced_investigation_images']}
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());data[INV]['key_images']=[];path.write_text(json.dumps(data,indent=2)+'\n')
    path=ROOT/'data/radiology/investigation-source-images.json';text=path.read_text()
    if '"'+INV+'"' in text:
        start=text.index('[',text.index('"'+INV+'"'));_,end=json.JSONDecoder().raw_decode(text,start);path.write_text(text[:start]+'[]'+text[end:])
    path=ROOT/'data/radiology/reporting-steps/head-neck.json';text=path.read_text();start=text.index('{',text.index('"'+INV+'"'));node,end=json.JSONDecoder().raw_decode(text,start);node.setdefault('start',{}).update(images=[],module_illustrations=False)
    for step in node['steps']:step['images']=[r for r in step.get('images',[]) if r not in old and r!=IDENT]
    path.write_text(text[:start]+json.dumps(node,indent=2).replace('\n','\n    ')+text[end:])
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)):value.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    next(r for r in data['investigations'] if r['investigation_id']==INV)['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']});path.write_text(json.dumps(data,indent=2)+'\n');print('Original source FOV figure integrated; temporal/clinical and anatomy coverage not granted')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
