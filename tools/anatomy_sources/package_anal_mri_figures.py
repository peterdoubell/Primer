#!/usr/bin/env python3
"""Attach preserved T2 tumour snapshots without inferring complete volumes or response."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[2]
IDENT='open-anal-mri-pmc10784345-fig2'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
    folder=ROOT/'docs/anal-mri-published-source-review';proof_path=folder/'original-source-review.json'
    proof=json.loads(proof_path.read_text());source=proof['figures'][0];article=proof['articles'][0]
    if len(proof['figures'])!=1 or source['pmcid']!='PMC10784345' or source['figure_number']!=2:raise ValueError('Unreviewed selection')
    src=root/source['extracted_file']
    if sha(src)!=source['sha256'] or not source['original_encoded_stream_or_decoded_pixel_readback_verified']:raise ValueError('Original figure differs')
    local='web/reference-media/radiology-open/anal-mri-pmc10784345-fig2.png';shutil.copyfile(src,ROOT/local)
    caption='Four original axial T2 snapshots from two different anal-cancer patient examples, each at baseline and week 2. Original contours and arrows are preserved. These local views do not independently validate volumetric response or predict recurrence.'
    limits='Two separate source patients, with baseline/week-2 views in each pair; no geometry is transferred between pairs. Complete clinical series, volumetric masks, independent timepoint registration, calibrated greatest tumour dimension and pathological confirmation are not supplied by these snapshots. No DWI/ADC, definitive viability, complete sphincter/organ invasion map, nodal staging, systemic staging or spatial 3D tumour reconstruction is inferred. Published PDF samples/ICC are preserved; highest-resolution acquired masters and independent anatomical validation remain unverified.'
    context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},
             'depicted_state':'anal_cancer_mri_source_pmc10784345_fig2','extent':'local',
             'selected_panels':list('abcd'),'panel_types':dict.fromkeys('abcd','MRI'),
             'panel_states':dict.fromkeys('abcd','anal_cancer_mri_source_pmc10784345_fig2'),
             'panel_sequences':dict.fromkeys('abcd','axial T2'),
             'separate_patient_pairs':[['a','b'],['c','d']],
             'panel_timepoints':{'a':'baseline','b':'week_2','c':'baseline','d':'week_2'},
             'panel_identifiers_from_caption':True,'independent_timepoint_registration_verified':False,
             'full_volumetric_series_or_masks_included':False,'response_or_recurrence_prediction_verified':False,
             'full_sphincter_or_organ_invasion_map_verified':False,'spatial_3d_tumour_derived':False}
    credit=article['copyright']+' '+', '.join(article['authors'])+'. '+article['title']+'. DOI '+article['doi']+'. CC BY 4.0. Complete original Figure 2 preserved from the verified publication PDF without sample changes. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
    row={'id':IDENT,'kind':'clinical-image','src':'/app/'+local.removeprefix('web/'),
         'width':source['width'],'height':source['height'],'sha256':source['sha256'],
         'source_url':article['source_article_url'],'figure_url':article['source_article_url']+'#Fig2','figure_number':2,
         'asset_source_url':article['pdf_url'],'modality':'MRI','clinical_panels':list('abcd'),
         'image_state':context['depicted_state'],'source_context':context,'caption':caption,'alt':caption,
         'limits':limits,'structures_visible':['Source-local tumour contours and surrounding anal/pelvic context in axial T2 snapshots'],
         'license':'CC BY 4.0','license_url':article['license_url'],'attribution':credit,'source_background':'white',
         'rights_reviewed_on':'2026-10-05','rights_review':'Original XML grant and complete caption checked for separate credits; repository checksums and PDF sample/profile readback verified.'}
    image_path=ROOT/'data/radiology/radiology-open-images.json';images=json.loads(image_path.read_text())
    images['ra.mri-anal-cancer']=[r for r in images.get('ra.mri-anal-cancer',[]) if r['id']!=IDENT]+[row]
    image_path.write_text(json.dumps(images,indent=2,ensure_ascii=False)+'\n')
    asset={'id':IDENT,'kind':'clinical_image','name':article['title']+' Figure 2','local_path':local,'sha256':source['sha256'],
           'regions':['pelvis'],'investigation_ids':['ra.mri-anal-cancer'],'structure_ids':[],'requirement_coverage':{},
           'modality':'MRI','source_context':context,
           'source':{'url':article['source_article_url'],'figure_url':row['figure_url'],'asset_url':article['pdf_url'],
                     'license':{'name':'CC BY 4.0','url':article['license_url'],'commercial_use':True,'redistribution':True,
                                'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),
                                'evidence_sha256':sha(proof_path),'attribution':credit,'reviewed_at':'2026-10-05'}},
           'pixel_provenance':{'source_pdf_sha256':article['pdf_sha256'],'pdf_object_id':source['pdf_object_id'],
                               'decoded_pixel_sha256':source['decoded_pixel_sha256'],'source_pixels_changed':False,
                               'highest_resolution_acquired_master_verified':False},
           'anatomical_review':{'status':'pending','reason':'Local published tumour snapshots are not independent complete boundary, organ, node or model validation.'},
           'visual_review':{'status':'source_checked','sha256':source['sha256'],'reviewed_at':'2026-10-05',
                            'evidence_path':'docs/anal-mri-published-source-review.md'}}
    path=ROOT/'data/radiology/radiology-asset-evidence.json';raw=path.read_text();start=raw.index('[',raw.index('"assets"'))+1;cursor=start;retained=[];decoder=json.JSONDecoder()
    while True:
        cursor+=len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==']':break
        entry,end=decoder.raw_decode(raw,cursor)
        if entry['id']!=IDENT:retained.append(raw[cursor:end])
        cursor=end+len(re.match(r'\s*',raw[end:]).group())
        if raw[cursor]==',':cursor+=1
    retained.append(json.dumps(asset,indent=2,ensure_ascii=False).replace('\n','\n    '))
    path.write_text(raw[:start]+'\n    '+',\n    '.join(retained)+'\n  '+raw[cursor:])
    path=ROOT/'data/radiology/reporting-steps/abdomen.json';raw=path.read_text()
    # Only the current tumour step's image array changes; preserve other authored text.
    key='"ra.mri-anal-cancer"';start=raw.index(key);start=raw.index('"images"',start);begin=raw.index('[',start);end=raw.index(']',begin)
    ids=json.loads(raw[begin:end+1])
    if IDENT not in ids:ids.append(IDENT)
    path.write_text(raw[:begin]+json.dumps(ids,indent=2).replace('\n','\n          ')+raw[end+1:])
    (folder/'packaged-source-images.json').write_text(json.dumps({'figures':[{'local_path':local,'sha256':source['sha256'],'figure_number':2,
        'pmcid':source['pmcid'],'width':source['width'],'height':source['height'],'source_pixels_changed':False}],
        'clinical_approval':False,'structure_coverage_granted':False,'model_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    package(p.parse_args().source_root)
