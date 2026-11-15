#!/usr/bin/env python3
"""Add original vascular source figures without upgrading source phase or anatomical approval."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[2]
TEXT={
 'PMC12490646':('Source coronal CT appearance of a reported gastroduodenal pseudoaneurysm. The article body calls this CTA; the figure caption calls it angiographic imaging during an intervention. That source context discrepancy remains unresolved.',
               'The article describes bleeding, but this selected still does not independently verify active extravasation or acquisition timing. It is not imported as catheter angiography or used to infer a treatment decision.'),
 'PMC9870600':('Recurrent-pancreatitis source case: contrast CT shows an enhancing focus within a large lesion near the gastroduodenal artery region, described by the authors as a pseudoaneurysm.',
              'The source recurrent context is preserved; an acute-only episode, complete arterial neck, wall/lumen extent and specific contrast phase are not established by this figure.'),
 'PMC12358223':('Source CT example of a reported nonocclusive proximal portal-vein filling defect following pancreatitis, marked by the original white arrow.',
                'The selected section does not establish complete portal/SMV/splenic-vein extent, calibrated thrombus burden or a treatment recommendation.')}


def package(root):
    proof_path=ROOT/'docs/pancreatitis-vascular-source-review/original-source-review.json';proof=json.loads(proof_path.read_text())
    images_path=ROOT/'data/radiology/radiology-open-images.json';assets_path=ROOT/'data/radiology/radiology-asset-evidence.json'
    images=json.loads(images_path.read_text());rows=[];assets=[];records=[]
    for p in proof['figures']:
        path=root/p['source_filename'];raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=p['sha256']:raise ValueError('Original source figure changed')
        ident='open-pancreatitis-vascular-'+p['pmcid'].lower()+'-'+p['figure_id'].lower()
        filename='pancreatitis-vascular-'+p['pmcid'].lower()+'-'+p['figure_id'].lower()+'.jpg'
        target=ROOT/'web/reference-media/radiology-open'/filename;shutil.copyfile(path,target)
        caption,extra=TEXT[p['pmcid']]
        limits='Original published local section, not a calibrated DICOM series, whole vascular volume, dynamic bleeding study or patient-specific 3D model. Source labels/arrows remain author claims; independent anatomical review is pending. '+extra
        credit=p['source_copyright']+' '+', '.join(p['authors'])+'. '+p['article_title']+'. DOI '+p['doi']+'. '+p['license']+'. Original complete '+p['figure_id']+' preserved without image alteration. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
        context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'depicted_state':p['source_state'],'extent':'local'}
        image={'id':ident,'kind':'clinical-image','src':'/app/reference-media/radiology-open/'+filename,'width':p['width'],'height':p['height'],'sha256':p['sha256'],
               'source_url':p['source_article_url'],'figure_url':p['source_article_url']+'#'+p['figure_id'],'asset_source_url':p['source_url'],
               'figure_number':int(re.search(r'[0-9]+',p['figure_id']).group()),'modality':'CT','image_state':p['source_state'],
               'caption':caption,'alt':caption,'limits':limits,'structures_visible':['Source-described local vascular observation; full boundaries and anatomical accuracy not approved'],
               'license':p['license'],'license_url':p['license_url'],'attribution':credit,'rights_reviewed_on':'2026-10-04',
               'rights_review':'Original XML version-specific grant and complete selected caption checked; source pixels matched published MD5.',
               'source_context':context,'source_modality_caption_body_discrepancy':p['source_modality_caption_body_discrepancy']}
        rows.append(image)
        assets.append({'id':ident,'kind':'clinical_image','name':p['article_title']+' '+p['figure_id'],'local_path':'web/reference-media/radiology-open/'+filename,
                       'sha256':p['sha256'],'regions':['abdomen'],'investigation_ids':['ra.ct-pancreatitis'],'structure_ids':[],'modality':'CT','source_context':context,'requirement_coverage':{},
                       'source':{'url':p['source_article_url'],'figure_url':image['figure_url'],'asset_url':p['source_url'],
                                 'license':{'name':p['license'],'url':p['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified',
                                            'evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest(),'attribution':credit,'reviewed_at':'2026-10-04'}},
                       'pixel_provenance':{'source_media_publisher_md5':p['publisher_md5'],'source_media_md5_verified':True,'source_pixels_changed':False,'highest_resolution_acquired_master_verified':False},
                       'visual_review':{'status':'source_checked','sha256':p['sha256'],'reviewed_at':'2026-10-04','evidence_path':'docs/pancreatitis-vascular-source-review.md'},
                       'anatomical_review':{'status':'pending','reason':'No complete vascular boundary, phase, actual extravasation or treatment claim approved; source discrepancy/recurrent context remain explicit.'}})
        records.append({'id':ident,'local_path':assets[-1]['local_path'],'source_sha256':p['sha256'],'source_pixels_changed':False,'clinical_approval':False})
    owned={r['id'] for r in rows};images['ra.ct-pancreatitis']=[r for r in images['ra.ct-pancreatitis'] if r['id'] not in owned]+rows
    images_path.write_text(json.dumps(images,indent=2,ensure_ascii=False)+'\n')
    raw=assets_path.read_text();start=raw.index('[',raw.index('"assets"'))+1;cursor=start;decoder=json.JSONDecoder();retained=[]
    while True:
        cursor+=len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==']':break
        r,end=decoder.raw_decode(raw,cursor)
        if r['id'] not in owned:retained.append(raw[cursor:end])
        cursor=end;cursor+=len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==',':cursor+=1
    retained += [json.dumps(r,indent=2,ensure_ascii=False).replace('\n','\n    ') for r in assets]
    assets_path.write_text(raw[:start]+'\n    '+',\n    '.join(retained)+'\n  '+raw[cursor:])
    (proof_path.parent/'packaged-source-images.json').write_text(json.dumps({'figures':records,'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
