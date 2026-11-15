#!/usr/bin/env python3
"""Package complete licensed published figures with explicit clinical/ancillary panel modalities."""
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
SUMMARIES={1:'Source-labelled interstitial oedematous pancreatitis: local CT tail enlargement and peripancreatic stranding.',
3:'Source-labelled acute peripancreatic fluid collection on CT, with preserved gland enhancement and unencapsulated fluid in adjacent spaces.',
4:'Source-labelled pseudocyst on MRI with MRCP duct findings; this figure supplies MRI context, not CT duct visibility.',
5:'Serial source case: A and D ultrasound; B, C and E CT; F MRI. Early CT collection morphology and later wall/debris appearances remain separate time points.',
6:'Source-labelled walled-off necrosis on CT, with a defined enhancing wall and heterogeneous internal content.',
7:'Source walled-off necrosis across ultrasound A, CT B and MRI C. Only panel B is the selected CT example; the other modalities remain explicit adjuncts.',
8:'Source walled-off necrosis with gas, a biliary stent and duodenal communication on CT. The gas is not labelled as microbiologically proved infection.'}
STATES={1:'pancreatitis_interstitial_source_case',3:'pancreatitis_apfc',4:'pancreatitis_pseudocyst_mri',5:'pancreatitis_serial_collection_context',6:'pancreatitis_walled_off_necrosis',7:'pancreatitis_multimodality_won',8:'pancreatitis_won_stent_fistula_context'}
SELECTED={1:['whole'],3:['a','b'],4:['a','b'],5:['b','c','e'],6:['whole'],7:['b'],8:['a','b']}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    review=ROOT/'docs/pancreatitis-published-source-review';path=review/'original-figure-acquisition.json';source=json.loads(path.read_text())
    pdf=root/'PMC4760067.1.pdf';metadata=json.loads((root/'PMC4760067.1.json').read_text())
    import urllib.parse
    expected=urllib.parse.parse_qs(urllib.parse.urlparse(metadata['pdf_url']).query)['md5'][0]
    if hashlib.md5(pdf.read_bytes()).hexdigest()!=expected:raise ValueError('Original PDF MD5 differs')
    target=ROOT/'web/reference-media/radiology-open';images_path=ROOT/'data/radiology/radiology-open-images.json';assets_path=ROOT/'data/radiology/radiology-asset-evidence.json'
    images=json.loads(images_path.read_text());assets=json.loads(assets_path.read_text());rows=[];evidence=[];selected_files=[]
    ids={'open-pancreatitis-sureka-2015-fig'+str(r['figure_number']) for r in source['figures']}
    for r in source['figures']:
        number=r['figure_number'];original=root/r['source_filename'];method='Original repository figure JPEG, preserved byte-for-byte';source_pdf_image=None
        if number in (5,7):
            index={5:5,7:7}[number];original=root/'pdf-images'/('original-'+str(index).zfill(3)+'.jpg')
            method='Original complete figure JPEG stream extracted losslessly from MD5-verified publication PDF by pdfimages -j'
            source_pdf_image={'page':5 if number==5 else 6,'image_number_zero_based':index,'pdf_object_id':47 if number==5 else 54,'source_pdf_sha256':sha(pdf),'source_pdf_publisher_md5':expected}
        elif sha(original)!=r['sha256']:raise ValueError('Original repository image changed')
        identifier='open-pancreatitis-sureka-2015-fig'+str(number);filename='pancreatitis-sureka-2015-fig'+str(number)+'.jpg'
        shutil.copyfile(original,target/filename)
        with Image.open(original) as pixels:width,height=pixels.size
        modality='MRI' if number==4 else 'CT';types=r['source_panel_types'];panels=SELECTED[number]
        if any(types[p]!=modality for p in panels):raise ValueError('Clinical panels borrow another modality')
        context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'adult'},'depicted_state':STATES[number],'extent':'local',
                 'selected_panels':panels,'panel_types':types,'panel_states':{p:STATES[number] for p in types}}
        limits='Published selected sections only: no original DICOM volume, calibrated full anatomy, validated source phase timing, histology, complete wall/debris extent or patient-specific 3D reconstruction. Original panel labels and source arrows are preserved; their presence does not grant independent anatomical approval.'
        if number in (5,7):limits+=' Mixed source modalities/time points cannot be borrowed for selected CT panels; source MRI sequence descriptions are not independently verified.'
        if number==4:limits+=' Source MRI/MRCP sequence and duct-communication descriptions are author claims; no CT, DWI/ADC or complete duct-wall coverage is supplied.'
        if number==8:limits+=' Biliary instrumentation and enteric communication remain explicit alternatives/context for collection gas; infection is not proved by this image alone.'
        attribution=source['source_copyright']+' '+', '.join(source['authors'])+'. Imaging lexicon for acute pancreatitis: 2012 Atlanta Classification revisited. DOI '+source['doi']+'. CC BY 4.0. Complete Figure '+str(number)+' preserved without image alteration. Source: NLM/PMC Article Datasets, original article/media snapshot; this snapshot may not reflect latest NLM data. No endorsement implied.'
        figure_url=source['source_article_url']+'#'+r['source_figure_id']
        row={'id':identifier,'kind':'clinical-image','src':'/app/reference-media/radiology-open/'+filename,'width':width,'height':height,'sha256':sha(original),
             'source_url':source['source_article_url'],'figure_url':figure_url,'figure_number':number,'asset_source_url':metadata['pdf_url'].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/') if source_pdf_image else r['source_url'],
             'caption':SUMMARIES[number],'alt':SUMMARIES[number],'modality':modality,'clinical_panels':panels,'image_state':STATES[number],
             'structures_visible':['Source-described local observation; complete reporting anatomy and specific boundaries not approved'],
             'limits':limits,'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','attribution':attribution,
             'rights_reviewed_on':'2026-10-04','rights_review':'Original CC BY 4.0 article XML and complete source captions checked; no figure-specific excluded credit found.',
             'acquisition':method,'source_context':context}
        ancillary=[]
        for kind in ['Ultrasound','MRI']:
            other=[p for p,t in types.items() if t==kind and p not in panels]
            if other:ancillary.append({'kind':kind,'panels':other,'structures_visible':['Source '+kind+' collection context'],
                                       'limits':'Ancillary source modality only; cannot supply CT visibility, temporal matching or independently verified sequence features.'})
        if ancillary:row['ancillary_panels']=ancillary
        rows.append(row)
        evidence.append({'id':identifier,'kind':'clinical_image','name':'Pancreatitis source Figure '+str(number),'local_path':'web/reference-media/radiology-open/'+filename,
                         'sha256':row['sha256'],'regions':['abdomen'],'investigation_ids':['ra.ct-pancreatitis'],'structure_ids':[],
                         'modality':modality,'source_context':context,'requirement_coverage':{},
                         'source':{'url':source['source_article_url'],'figure_url':figure_url,'asset_url':row['asset_source_url'],'license':{'name':'CC BY 4.0','url':row['license_url'],'commercial_use':True,'redistribution':True,
                                  'review_status':'verified','evidence_path':'docs/pancreatitis-published-source-review/original-figure-acquisition.json','evidence_sha256':sha(path),'attribution':attribution,'reviewed_at':'2026-10-04'}},
                         'pixel_provenance':{'acquisition':method,'repository_comparison_media_sha256':r['sha256'],'source_pdf_image':source_pdf_image,'source_pixels_changed':False,'highest_resolution_acquired_master_verified':False},
                         'anatomical_review':{'status':'pending','reason':'Published local sections and source labels do not establish complete high-fidelity reporting structures.'},
                         'visual_review':{'status':'source_checked','sha256':row['sha256'],'reviewed_at':'2026-10-04','evidence_path':'docs/pancreatitis-published-source-review/packaged-figure-selection.json'}})
        selected_files.append({'figure_number':number,'local_path':evidence[-1]['local_path'],'sha256':row['sha256'],'width':width,'height':height,
                               'repository_dimensions':[r['width'],r['height']],'source_pdf_image':source_pdf_image,'acquisition':method,'clinical_panels':panels,'source_panel_types':types,'source_pixels_changed':False})
    images['ra.ct-pancreatitis']=[r for r in images.get('ra.ct-pancreatitis',[]) if r['id'] not in ids]+rows
    # Preserve unrelated asset records byte-for-byte while appending owned entries.
    import re
    raw=assets_path.read_text();start=raw.index('[',raw.index('"assets"'))+1;cursor=start;decoder=json.JSONDecoder();retained=[]
    while True:
        cursor+=len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==']':break
        item,end=decoder.raw_decode(raw,cursor)
        if item['id'] not in ids:retained.append(raw[cursor:end])
        cursor=end;cursor+=len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==',':cursor+=1
    retained += [json.dumps(r,indent=2,ensure_ascii=False).replace('\n','\n    ') for r in evidence]
    assets_path.write_text(raw[:start]+'\n    '+',\n    '.join(retained)+'\n  '+raw[cursor:])
    images_path.write_text(json.dumps(images,indent=2,ensure_ascii=False)+'\n')
    (review/'packaged-figure-selection.json').write_text(json.dumps({'source_figure_acquisition_sha256':sha(path),'figures':selected_files,
         'source_pixels_cropped_resampled_recompressed_or_edited':False,'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
