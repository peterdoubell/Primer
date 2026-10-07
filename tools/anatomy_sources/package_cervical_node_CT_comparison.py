#!/usr/bin/env python3
"""Preserve a credited co-author CT comparison without turning imaging suspicion into pathological ENE."""
import argparse,hashlib,json,sys,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PIL import Image
from pypdf import PdfReader
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/cervical-node-published-source-review';IDENT='ra.cervical-lymph-nodes';ID='open-cervical-nodes-pmc10548228-fig5';URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC10548228/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(source):
    m=json.loads((source/'PMC10548228.1.json').read_text());xml=(source/'PMC10548228.1.xml').read_bytes();pdf=(source/'PMC10548228.1.pdf').read_bytes()
    if m['pmcid']!='PMC10548228' or m['is_retracted'] is not False or hashlib.md5(xml).hexdigest()!=m['xml_url'].split('md5=')[1] or hashlib.md5(pdf).hexdigest()!=m['pdf_url'].split('md5=')[1]:raise ValueError('Original source identity/checksum differs')
    tree=E.fromstring(xml);grant,license_url=exact_license(tree.find('.//article-meta/permissions'));authors=[' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    fig=tree.find('.//fig[@id="f5"]');caption=' '.join(fig.find('caption').itertext());copyright=tree.findtext('.//article-meta/permissions/copyright-holder','')
    if grant!='CC BY 4.0' or 'James Bates' not in authors or 'Bates' not in copyright or 'Dr. James Bates' not in caption or fig.find('permissions') is not None:raise ValueError('Credited image copyright-holder grant requires review')
    obj=PdfReader(source/'PMC10548228.1.pdf').get_object(91);master=source/'fig5-original-PDF-ICC.png';raw=master.read_bytes();profile=obj['/ColorSpace'][1].get_object().get_data()
    with Image.open(master) as image:
        image.load();pixels=image.tobytes();width,height=image.size
        if pixels!=obj.get_data() or image.info.get('icc_profile')!=profile or (width,height)!=(obj['/Width'],obj['/Height']):raise ValueError('Original embedded master/profile samples differ')
    OUT.mkdir(exist_ok=True);archive=OUT/'packaged-source-images.json';removed=json.loads(archive.read_text())['replaced_investigation_images'] if archive.exists() else catalog.detail(Curriculum(),catalog.resolve(IDENT))['radiology_reference']['key_images']
    local='web/reference-media/radiology-open/cervical-nodes-pmc10548228-fig5.png';(ROOT/local).write_bytes(raw)
    limits='Two distinct source patients: A left levelII imaging suspicion with later source pathological ENE; B right levelII imaging suspicion without ENE on source pathology. These are publication outcomes, not independent pathology readout or a new patient diagnosis. Original selected contrasted axial CTs do not supply whole native node/capsule/neck/vascular geometry, microscopic extension, molecular status, flow or universal iENE grade. Full original pixels and ICC profile retained.'
    context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local','depicted_state':'source_distinct_nodal_CT_pathology_comparisons','selected_panels':['A','B'],'panel_types':{'A':'CT','B':'CT'},'panel_states':{'A':'source_nodal_imaging_suspicion','B':'source_nodal_imaging_suspicion'},'source_case_groups':{'left_level_II_pathology_positive':['A'],'different_right_level_II_pathology_negative':['B']},'source_pathology_outcomes_are_new_independent_confirmation':False,'native_orientation_or_full_anatomical_extent_verified':False}
    attribution=', '.join(authors)+'. '+m['title']+'. DOI '+m['doi']+'. Figure5 images kindly provided by co-author/copyright holder Dr. James Bates. CC BY4.0. Original PDF master decoded losslessly with original ICC; no resampling.'
    proof={'pmcid':m['pmcid'],'doi':m['doi'],'original_article_grant':grant,'license_url':license_url,'permissions_XML':E.tostring(tree.find('.//article-meta/permissions'),encoding='unicode'),'authors':authors,'credited_image_provider':'James Bates','credited_provider_is_listed_author_and_copyright_holder':True,'metadata_sha256':sha((source/'PMC10548228.1.json').read_bytes()),'XML_sha256':sha(xml),'PDF_sha256':sha(pdf),'publisher_XML_and_PDF_MD5_verified':True,'figure_number':5,'PDF_image_object':91,'source_caption_full':caption,'source_master_sha256':sha(raw),'decoded_pixel_sha256':sha(pixels),'original_ICC_sha256':sha(profile),'original_source_master_samples_and_ICC_verified':True,'source_pixels_changed':False,'other_figures_held':[{'figure_number':1,'reason':'BioRender-created graphic; underlying reuse scope unreviewed.'},{'figure_number':2,'reason':'Third-party Medrano credit; broader reuse scope unreviewed.'},{'figure_number':3,'reason':'Third-party Yu credit/older grade schema; scope unreviewed.'},{'figure_number':4,'reason':'Third-party Yu credit; broader reuse scope unreviewed.'}],'clinical_approval':False,'structure_coverage_granted':False}
    proof_path=OUT/'original-source-review.json';proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    row={'id':ID,'kind':'clinical-image','modality':'CT','figure_number':5,'src':'/app/'+local.removeprefix('web/'),'sha256':sha(raw),'width':width,'height':height,'source_url':URL,'figure_url':URL+'#f5','asset_source_url':m['pdf_url'].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/'),'clinical_panels':['A','B'],'source_context':context,'image_state':context['depicted_state'],'caption':'Original Figure5: distinct suspicious nodal CT cases with different source pathology outcomes. '+limits,'alt':'Original Figure5: two separate source nodal CT cases. '+limits,'limits':limits,'source_caption_full':caption,'structures_visible':['Source-local nodes and adjacent tissue/vessel relationships'],'license':grant,'license_url':license_url,'attribution':attribution,'rights_reviewed_on':'2026-10-07','rights_review':'Explicit article CC BY4 copyright includes credited co-author Bates; no separate figure restriction. Other third-party/BioRender figures held.'}
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[IDENT]=[r for r in data.get(IDENT,[]) if r['id']!=ID]+[row];path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    asset={'id':ID,'kind':'clinical_image','name':'Original two-case nodal CT/pathology comparison','local_path':local,'sha256':sha(raw),'modality':'CT','investigation_ids':[IDENT],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':URL,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':{'name':grant,'url':license_url,'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-07'}},'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':sha(pixels),'original_ICC_preserved':True,'highest_resolution_acquired_master_verified':True},'anatomical_review':{'status':'pending','reason':'Selected CTs/outcome text do not independently establish full capsule/node/neck/vascular geometry or current-patient pathology.'},'visual_review':{'status':'source_checked','sha256':sha(raw),'evidence_path':'docs/cervical-node-published-source-review.md','reviewed_at':'2026-10-07'}}
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',[asset],prefix=ID)
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());data[IDENT]['key_images']=[];path.write_text(json.dumps(data,indent=2)+'\n')
    path=ROOT/'data/radiology/investigation-source-images.json';raw_json=path.read_text()
    if '"'+IDENT+'"' in raw_json:
        start=raw_json.index('[',raw_json.index('"'+IDENT+'"'));old,end=json.JSONDecoder().raw_decode(raw_json,start);path.write_text(raw_json[:start]+'[]'+raw_json[end:])
    path=ROOT/'data/radiology/reporting-steps/head-neck.json';raw_json=path.read_text();start=raw_json.index('{',raw_json.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw_json,start);old_ids={i['id'] for i in removed};node.setdefault('start',{}).update(images=[],module_illustrations=False)
    for step in node['steps']:step['images']=[i for i in step.get('images',[]) if i not in old_ids]
    for i in [1,2,3]:node['steps'][i]['images']=list(dict.fromkeys(node['steps'][i]['images']+[ID]))
    path.write_text(raw_json[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw_json[end:]);archive.write_text(json.dumps({'replaced_investigation_images':removed,'original_master_path':local,'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')
    for v in vars(catalog).values():
        if callable(getattr(v,'cache_clear',None)):v.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(IDENT))['radiology_reference'];path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    for i in data['investigations']:
        if i['investigation_id']==IDENT:i['source_contract_sha256']=digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    path.write_text(json.dumps(data,indent=2)+'\n');print('Original co-author CT comparison preserved with larger master/profile and separate pathology outcomes')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);a=p.parse_args();package(a.source_root)
