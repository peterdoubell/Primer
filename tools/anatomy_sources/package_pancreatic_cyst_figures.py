#!/usr/bin/env python3
"""Package original large PDF figure JPEGs without cross-modality or pathological-grade inference."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[2]
CAPTIONS={('PMC8355307','Fig4'):'Source serous microcystic/honeycomb example: CT A and MRI B–D retain architecture and MRCP context.',
 ('PMC8355307','Fig9'):'Source multilocular mucinous-cyst example: CT A/B and MRI C/D show architecture and internal material described by the authors.',
 ('PMC8355307','Fig13'):'Source main-duct IPMN example: MRI/MRCP A/B and CT C retain duct and host-gland context; original images are not a complete calibrated duct volume.',
 ('PMC8355307','Fig18'):'Source multifocal branch-duct IPMN example on MRCP A/B. Projection/source correspondence and complete communication geometry remain unapproved.',
 ('PMC13315461','Fig3'):'Source non-enhancing nodular component/mucin-plug context. MRI A–F is selected; PET-CT G and EUS H remain distinct adjuncts.',
 ('PMC13315461','Fig4'):'Source enhancing mural-nodule case with low-grade IPMN described on histology I/J. MRI A–F, PET-CT G and EUS H stay separate; enhancement alone does not establish malignant grade.',
 ('PMC13315461','Fig5'):'Source enhancing mural-nodule case with high-grade IPMN described on histology I/J. MRI A–F cannot independently establish histological grade; PET-CT G and EUS H remain distinct adjuncts.'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder=ROOT/'docs/pancreatic-cyst-published-source-review';source_path=folder/'original-source-review.json';proof=json.loads(source_path.read_text())
    streams=json.loads((folder/'original-pdf-stream-selection.json').read_text());rows=[];assets=[];selection=[]
    for r in proof['figures']:
        key=(r['pmcid'],r['figure_id']);stream=next(s for s in streams['figures'] if (s['pmcid'],s['figure_id'])==key)
        file=root/stream['extracted_file']
        if sha(file)!=stream['sha256']:raise ValueError('Original encoded figure stream changed')
        identifier='open-pancreatic-cyst-'+r['pmcid'].lower()+'-'+r['figure_id'].lower();name='pancreatic-cyst-'+r['pmcid'].lower()+'-'+r['figure_id'].lower()+'.jpg'
        target=ROOT/'web/reference-media/radiology-open'/name;shutil.copyfile(file,target)
        panels=r['selected_mri_panels'];types=r['source_panel_types']
        if not panels or any(types[p]!='MRI' for p in panels):raise ValueError('Selected MRI panels borrow another modality')
        state='pancreatic_cyst_source_'+r['pmcid'].lower()+'_'+r['figure_id'].lower()
        context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'depicted_state':state,'extent':'local',
                 'selected_panels':panels,'panel_types':types,'panel_states':{p:state for p in types}}
        limits='Original complete published figure; no calibrated native DICOM volume, independently verified phase/sequence timing, full cyst/duct/wall/nodule extent or patient-specific 3D reconstruction. Source sequence/pathology labels remain author claims. CT, PET-CT, EUS and histology cannot lend features or histological grade to selected MRI panels. Original colours/annotations are preserved in encoded JPEG streams; independent colour calibration is unverified.'
        credit=r['source_copyright']+' '+', '.join(r['authors'])+'. '+r['article_title']+'. DOI '+r['doi']+'. CC BY 4.0. Original complete '+r['figure_id']+' JPEG preserved from the MD5-verified publication PDF without pixel alteration. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
        meta=json.loads((root/(r['pmcid']+'.1.json')).read_text());pdf_url=meta['pdf_url'].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
        row={'id':identifier,'kind':'clinical-image','src':'/app/reference-media/radiology-open/'+name,'width':stream['width'],'height':stream['height'],'sha256':stream['sha256'],
             'source_url':r['source_article_url'],'figure_url':r['source_article_url']+'#'+r['figure_id'],'asset_source_url':pdf_url,
             'figure_number':int(re.search(r'[0-9]+',r['figure_id']).group()),'modality':'MRI','clinical_panels':panels,'image_state':state,
             'caption':CAPTIONS[key],'alt':CAPTIONS[key],'limits':limits,'structures_visible':['Source-described local cyst/duct/nodule observation; complete anatomical extent and diagnostic grade not approved'],
             'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','attribution':credit,
             'rights_reviewed_on':'2026-10-04','rights_review':'Original XML CC BY 4.0 grant and selected figure credits reviewed; separately credited book figure excluded.',
             'source_context':context}
        ancillary=[]
        for kind in ['CT','PET-CT','Ultrasound','Histology']:
            other=[p for p,t in types.items() if t==kind]
            if other:ancillary.append({'kind':kind,'panels':other,'structures_visible':['Source '+('endoscopic ultrasound' if kind=='Ultrasound' else kind)+' context'],
                                      'limits':'Separate source modality/pathology context only; cannot supply selected MRI features or independently verified case/grade correspondence.'})
        if ancillary:row['ancillary_panels']=ancillary
        rows.append(row)
        assets.append({'id':identifier,'kind':'clinical_image','name':r['article_title']+' '+r['figure_id'],'local_path':'web/reference-media/radiology-open/'+name,
          'sha256':stream['sha256'],'regions':['abdomen'],'investigation_ids':['ra.pancreatic-cysts'],'structure_ids':[],'modality':'MRI','source_context':context,'requirement_coverage':{},
          'source':{'url':r['source_article_url'],'figure_url':row['figure_url'],'asset_url':pdf_url,'license':{'name':'CC BY 4.0','url':row['license_url'],
           'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(source_path.relative_to(ROOT)),'evidence_sha256':sha(source_path),'attribution':credit,'reviewed_at':'2026-10-04'}},
          'pixel_provenance':{'source_pdf_sha256':stream['source_pdf_sha256'],'source_pdf_object_id':stream['pdf_object_id'],'encoded_stream_sha256':stream['sha256'],
           'source_pixels_changed':False,'original_encoded_stream_readback_verified':True,'highest_resolution_acquired_master_verified':False,'colour_calibration_verified':False},
          'anatomical_review':{'status':'pending','reason':'Published sections, source sequence/pathology labels and overlays do not prove complete high-fidelity structures or MRI-derived histology.'},
          'visual_review':{'status':'source_checked','sha256':stream['sha256'],'reviewed_at':'2026-10-04','evidence_path':'docs/pancreatic-cyst-published-source-review.md'}})
        selection.append({'id':identifier,'local_path':assets[-1]['local_path'],'pmcid':r['pmcid'],'figure_id':r['figure_id'],'sha256':stream['sha256'],
                          'width':stream['width'],'height':stream['height'],'repository_dimensions':[r['width'],r['height']],
                          'source_panel_types':types,'selected_mri_panels':panels,'source_pixels_changed':False})
    ids={r['id'] for r in rows};image_path=ROOT/'data/radiology/radiology-open-images.json';images=json.loads(image_path.read_text())
    images['ra.pancreatic-cysts']=[r for r in images.get('ra.pancreatic-cysts',[]) if r['id'] not in ids]+rows
    image_path.write_text(json.dumps(images,indent=2,ensure_ascii=False)+'\n')
    asset_path=ROOT/'data/radiology/radiology-asset-evidence.json';raw=asset_path.read_text();start=raw.index('[',raw.index('"assets"'))+1;cursor=start;decoder=json.JSONDecoder();retained=[]
    while True:
        cursor+=len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==']':break
        r,end=decoder.raw_decode(raw,cursor)
        if r['id'] not in ids:retained.append(raw[cursor:end])
        cursor=end;cursor+=len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==',':cursor+=1
    retained += [json.dumps(r,indent=2,ensure_ascii=False).replace('\n','\n    ') for r in assets]
    asset_path.write_text(raw[:start]+'\n    '+',\n    '.join(retained)+'\n  '+raw[cursor:])
    (folder/'packaged-source-images.json').write_text(json.dumps({'figures':selection,'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
