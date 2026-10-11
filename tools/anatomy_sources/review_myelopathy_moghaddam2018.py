#!/usr/bin/env python3
"""Preserve full myelopathy publication images; write a source-bound integration draft only.

No runtime registry, curriculum, shared evidence or clinical approval is mutated.
The source PDF keeps its complete vectors/text/ICC. JPEG ICC insertion is metadata
only: the original stream is retained, and removal of the inserted segment must
reproduce it byte-for-byte. Lossless Flate samples retain their source channels.
"""
import argparse
import hashlib
import io
import json
import math
import re
from pathlib import Path
import shutil
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageStat
from pypdf import PdfReader
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / 'docs/myelopathy-published-source-review-20261011'
MEDIA = ROOT / 'web/reference-media/radiology-open'
DATE = '2026-10-11'
XLINK = '{http://www.w3.org/1999/xlink}href'
ARTICLES = [
    {'pmcid':'PMC6108975','folder':'source','prefix':'myelopathy-moghaddam2018',
     'objects':[12,13,23,22,30,29,34,35,43,44,52,70,78,79,91,102,101,107,108,112,113,124,125,132],
     'pages':[2,2,3,3,4,4,5,5,6,6,7,8,9,9,10,11,11,12,12,13,13,14,14,15]},
    {'pmcid':'PMC12394311','folder':'source-mogad','prefix':'myelopathy-mogad2025','objects':[14],'pages':[2]},
]
# Source captions control modality/patient/time relationships. No missing plane,
# side, sequence, molecular diagnosis or timing is inferred from image pixels.
FACTS = {
 1: ('intramedullary anatomy','not a patient','diagram',['spinal cord cross-section'],'not_applicable',{}),
 2: ('axial involvement patterns','not a patient','diagram',['spinal cord cross-section'],'not_applicable',{}),
 3: ('short versus long involvement','not a patient','diagram',['spinal cord and adjacent vertebrae'],'not_applicable',{}),
 4: ('multiple sclerosis','50-year-old male','MRI',['spinal cord; regional level not reported in caption'],'right',{'a':'axial MERGE','b':'sagittal T2 fat-saturated'}),
 5: ('multiple sclerosis, source-described active demyelination','50-year-old female','MRI',['spinal cord; regional level not reported in caption'],'right',{'a':'sagittal STIR','b':'axial T2','c':'axial T1 post-contrast'}),
 6: ('neuromyelitis optica spectrum disease','20-year-old female','MRI',['spinal cord','right optic nerve'],'right optic nerve; cord side not reported',{'a':'sagittal T2 fat-saturated','b':'axial orbital T1 post-contrast','c':'axial cord T2','d':'axial cord T1 post-contrast'}),
 7: ('acute disseminated encephalomyelitis','2-year-old boy','MRI',['cervical cord','thoracic cord','thalami'],'not_reported',{'a':'sagittal cervical T2','b':'sagittal thoracic T2','c':'axial brain T2 FLAIR','d':'follow-up sagittal thoracic T2'}),
 8: ('Guillain-Barré syndrome; peripheral root process','2-year-old patient; sex not reported','MRI',['conus medullaris','lumbar nerve roots'],'not_reported',{'a':'sagittal thoracolumbar T2','b':'axial lumbar T1 post-contrast'}),
 9: ('transverse myelitis','38-year-old female','MRI',['cervical cord'],'bilateral cross-sectional involvement',{'a':'sagittal T2','b':'axial T2','c':'T1 post-contrast; plane not explicitly named'}),
 10: ('HIV myelitis, source label','54-year-old female','MRI',['dorsal spinal cord; regional level not reported in caption'],'dorsal pattern; side not reported',{'a':'sagittal T2','b':'axial T2','c':'sagittal T1 post-contrast'}),
 11: ('subacute combined degeneration due to copper deficiency','45-year-old female','MRI',['dorsal columns'],'symmetric dorsal column pattern',{'a':'axial T2','b':'sagittal T2'}),
 12: ('subacute combined degeneration due to vitamin B12 deficiency, pernicious anaemia','58-year-old female','MRI',['dorsal spinal cord'],'not_reported',{'a':'pre-treatment sagittal T2','b':'post-treatment sagittal T2'}),
 13: ('ependymoma, source diagnosis','38-year-old female','MRI',['central spinal cord; more than two vertebral body levels'],'central; side not reported',{'a':'T2; plane not explicitly named','b':'T2; plane not explicitly named','c':'T1 post-contrast; plane not explicitly named'}),
 14: ('haemangioblastoma, source diagnosis','40-year-old male','MRI',['cervical cord syrinx','cervicomedullary junction','brainstem','lower thoracic cord lesion'],'not_reported',{'a':'cervical syrinx/brainstem image; sequence not explicitly named','b':'cervicomedullary/brainstem image; sequence not explicitly named','c':'sagittal T2 lower thoracic cord','d':'T1 post-contrast fat-saturated'}),
 15: ('spinal astrocytoma, source diagnosis','3-year-old child; sex not reported','MRI',['upper cervical cord','brainstem','fourth ventricle','cerebellum','C7-T1 extent'],'not_reported',{'a':'sagittal T2','b':'T1 post-contrast; plane not explicitly named'}),
 16: ('intramedullary metastasis, source diagnosis','69-year-old male; small-cell lung cancer history','MRI',['intramedullary spinal cord; regional level not reported in caption'],'not_reported',{'a':'T2; plane not explicitly named','b':'coronal T1 post-contrast'}),
 17: ('spinal glioblastoma, historical source terminology','46-year-old female','MRI',['distal spinal cord'],'not_reported',{'a':'T2; plane not explicitly named','b':'caption does not explicitly identify sequence','c':'post-contrast image; exact sequence/plane not explicitly named'}),
 18: ('spinal dural arteriovenous fistula','50-year-old male','MRI',['spinal cord','thecal sac perimedullary vessels','paraspinal artery/venous drainage'],'not_reported',{'a':'axial T2 MRI','b':'sagittal T2 MRI','c':'conventional spinal angiogram'}),
 19: ('spinal dural arteriovenous fistula','72-year-old male; prior lumbar laminectomy','MRI',['spinal cord','posterior thecal sac vessels','right T4-T5 supreme intercostal feeding artery'],'right feeding artery; cord side not reported',{'a':'axial T2 MRI','b':'longitudinal cord T2 MRI; plane not explicitly named','c':'spinal angiogram','d':'MRA'}),
 20: ('spinal arteriovenous malformation','16-year-old male','MRI',['intramedullary vessel nidus','extramedullary feeding/draining vessels'],'clinical left leg symptoms; lesion side not reported',{'a':'sagittal T2 fat-saturated MRI','b':'sagittal T1 post-contrast MRI','c':'conventional angiogram'}),
 21: ('spinal cavernoma, source diagnosis','40-year-old female','MRI',['spinal cord; regional level not reported in caption'],'clinical left upper limb symptoms; lesion side not reported',{'a':'sagittal T2','b':'sagittal GRE','c':'sagittal T1 post-contrast'}),
 22: ('spinal cord infarction, source diagnosis','82-year-old female; hypertension and hyperlipidaemia','MRI',['thoracic cord','lower cord','aorta and lumbar artery filling context'],'bilateral symptoms; lesion side not reported',{'a':'axial T2 MRI','b':'axial CT angiogram','c':'sagittal T2 MRI','d':'sagittal DWI MRI','e':'sagittal ADC MRI'}),
 23: ('degenerative compressive myelopathy','50-year-old patient; sex not reported','MRI',['C3-C4 canal','C3-C4 cord'],'bilateral hand symptoms; compression side not reported',{'a':'sagittal T2','b':'post-contrast image; exact sequence/plane not explicitly named'}),
 24: ('Hirayama disease, source diagnosis','22-year-old male','MRI',['C5-C6 cord anterior horns','dura/thecal sac C3-T2 during flexion'],'left cord atrophy slightly more conspicuous',{'a':'T2 anterior horn image; plane not explicitly named','b':'flexion image; exact sequence not explicitly named'}),
}

def sha(raw): return hashlib.sha256(raw).hexdigest()
def preserve_file(path,raw):
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError("Frozen media bytes differ: "+str(path))
    else:path.write_bytes(raw)
def checked_fetch(url, path):
    url=url.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
    raw=path.read_bytes() if path.exists() else urllib.request.urlopen(url,timeout=30).read()
    expected=urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('md5',[None])[0]
    if expected and hashlib.md5(raw).hexdigest()!=expected: raise ValueError('Source MD5 differs: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);return raw

def jpeg_icc(raw, profile):
    if not raw.startswith(b'\xff\xd8'):raise ValueError('Expected original JPEG')
    chunk_size=65519;count=math.ceil(len(profile)/chunk_size);segments=[]
    for i in range(count):
        payload=b'ICC_PROFILE\0'+bytes([i+1,count])+profile[i*chunk_size:(i+1)*chunk_size]
        segments.append(b'\xff\xe2'+(len(payload)+2).to_bytes(2,'big')+payload)
    insertion=b''.join(segments);display=raw[:2]+insertion+raw[2:]
    if display[:2]+display[2+len(insertion):]!=raw:raise ValueError('Encoded JPEG stream changed')
    return display,len(insertion)

def review(acquire=False):
    FOLDER.mkdir(exist_ok=True);MEDIA.mkdir(exist_ok=True);articles=[];figures=[];image_rows=[];assets=[];total=0
    for spec in ARTICLES:
        pmc=spec['pmcid'];source=FOLDER/spec['folder'];metadata_path=source/(pmc+'.1.json')
        if acquire: checked_fetch(f'https://pmc-oa-opendata.s3.amazonaws.com/{pmc}.1/{pmc}.1.json',metadata_path)
        metadata=json.loads(metadata_path.read_text());assert metadata['pmcid']==pmc and metadata['is_retracted'] is False
        if acquire:
            for link in [metadata['xml_url'],metadata['pdf_url']]+metadata['media_urls']:
                checked_fetch(link,source/urllib.parse.urlparse(link).path.split('/')[-1])
        raw_xml=checked_fetch(metadata['xml_url'],source/(pmc+'.1.xml'));raw_pdf=checked_fetch(metadata['pdf_url'],source/(pmc+'.1.pdf'));tree=ET.fromstring(raw_xml);permissions=tree.find('.//article-meta/permissions');grant=' '.join(permissions.itertext());license_url='https://creativecommons.org/licenses/by/4.0/'
        if license_url not in ET.tostring(permissions,encoding='unicode') or 'Attribution 4.0' not in grant:raise ValueError('Original CC BY 4.0 grant differs')
        authors=[' '.join([name.findtext('given-names',''),name.findtext('surname','')]).strip() for name in tree.findall('.//article-meta/contrib-group/contrib/name')]
        article={'pmcid':pmc,'doi':metadata['doi'],'title':metadata['title'],'authors':authors,'source_article_url':f'https://pmc.ncbi.nlm.nih.gov/articles/{pmc}/','metadata_sha256':sha(metadata_path.read_bytes()),'original_XML_sha256':sha(raw_xml),'original_PDF_sha256':sha(raw_pdf),'xml_url':metadata['xml_url'],'pdf_url':metadata['pdf_url'],'source_metadata_not_retracted':True,'publisher_XML_PDF_MD5_verified':True,'license':'CC BY 4.0','license_url':license_url,'original_article_grant':grant,'permissions_XML':ET.tostring(permissions,encoding='unicode'),'clinical_approval':False,'patient_consent_independently_verified':False}
        if pmc=='PMC6108975':article['acknowledged_figure_creators']=['Nadezhda Kiriyak (illustrations for this publication)','Margaret Kowaluk (figure formatting)','University of Rochester, Department of Imaging Sciences, Digital Illustrations division'];article['patient_ethics_or_consent_statement_in_original_article']='No explicit patient consent or ethics declaration found in the acquired XML; captions report age/sex and histories. Do not infer consent from open-access availability.'
        else:
            article['published_ethics_consent_statements']=[' '.join(e.itertext()) for e in tree.findall('.//p') if any(k in ' '.join(e.itertext()).lower() for k in ['ethical approval','informed consent'])]
            article['patient_ethics_or_consent_statement_in_original_article']='Source states ethics approval waived for retrospective routine care and written informed consent for clinical testing; publication consent is not independently established by this review.'
        pdf_name=spec['prefix']+'-original-publication.pdf';preserve_file(MEDIA/pdf_name,raw_pdf);article['packaged_original_PDF_path']=str((MEDIA/pdf_name).relative_to(ROOT));article['packaged_original_PDF_bytes']=len(raw_pdf);total+=len(raw_pdf)
        reader=PdfReader(io.BytesIO(raw_pdf));doc=pymupdf.open(stream=raw_pdf,filetype='pdf');masters=source/'original-PDF-streams';masters.mkdir(exist_ok=True)
        for n,(oid,page_num) in enumerate(zip(spec['objects'],spec['pages']),1):
            fig=tree.find(f'.//fig[@id="Fig{n}"]')
            if fig is None:fig=tree.find(f'.//fig[@id="F{n}"]')
            if fig is None:
                matching=[v for v in tree.findall('.//fig') if ''.join(v.find('label').itertext()).strip().endswith(str(n))];fig=matching[0] if len(matching)==1 else None
            if fig is None:raise ValueError('Figure binding missing')
            caption=' '.join(fig.find('caption').itertext());rights=any(fig.find(t) is not None for t in ['attrib','permissions','license']);
            if rights or any(token in caption.lower() for token in ['reproduced from','reprinted','courtesy of','with permission','©','copyright']):raise ValueError('Figure requires separate credit review')
            filename=fig.find('graphic').get(XLINK);link=next(u for u in metadata['media_urls'] if '/'+filename+'?' in u);html_raw=checked_fetch(link,source/filename);reference=Image.open(io.BytesIO(html_raw));reference.load();obj=reader.get_object(oid);size=(int(obj['/Width']),int(obj['/Height']));color=obj['/ColorSpace'].get_object();profile=None;icc_object=None
            if isinstance(color,list) and color[0]=='/ICCBased':
                icc_object=color[1].idnum;icc=color[1].get_object();profile=icc.get_data();assert icc['/N']==3;mode='RGB';(source/'source-RGB-profile.icc').write_bytes(profile)
            elif str(color)=='/DeviceGray': mode='L'
            else:raise ValueError('Unreviewed color space: '+str(color))
            if obj.get('/Decode') is not None or obj.get('/SMask') or obj['/BitsPerComponent']!=8:raise ValueError('Unreviewed source sample interpretation')
            page=doc[page_num-1];rects=page.get_image_rects(oid);assert len(rects)==1;rect=rects[0]
            overlay_text=page.get_text('text',clip=rect).strip();vector_paths=[d for d in page.get_drawings() if d['rect'].intersects(rect)]
            if overlay_text or vector_paths:raise ValueError('Extracted image would omit page overlays; preserve page view before packaging')
            stream=obj._data;inserted=0
            if str(obj['/Filter'])=='/DCTDecode':
                original_image=Image.open(io.BytesIO(stream));original_image.load();assert original_image.mode==mode and original_image.size==size;samples=original_image.tobytes();extension='.jpg';encoded,inserted=jpeg_icc(stream,profile) if profile else (stream,0);(masters/f'fig{n}-original.jpg').write_bytes(stream)
            elif str(obj['/Filter'])=='/FlateDecode':
                samples=obj.get_data();assert len(samples)==size[0]*size[1]*(3 if mode=='RGB' else 1);original_image=Image.frombytes(mode,size,samples);buf=io.BytesIO();kwargs={'icc_profile':profile} if profile else {};original_image.save(buf,format='PNG',**kwargs);encoded=buf.getvalue();extension='.png';(masters/f'fig{n}-original.samples').write_bytes(samples)
            else:raise ValueError('Unreviewed image encoding')
            with Image.open(io.BytesIO(encoded)) as back:
                back.load();assert back.mode==mode and back.size==size and back.tobytes()==samples
                if profile:assert back.info.get('icc_profile')==profile
            rms=sum(ImageStat.Stat(ImageChops.difference(original_image.convert('RGB').resize((96,64)),reference.convert('RGB').resize((96,64)))).rms)/3
            if rms>=4:raise ValueError('Numbered HTML/PDF visual binding differs')
            media_name=spec['prefix']+f'-fig{n}'+extension;media_path=MEDIA/media_name;preserve_file(media_path,encoded);total+=len(encoded)
            if pmc=='PMC6108975':condition,case,kind,sites,side,sequences=FACTS[n]
            else:condition,case,kind,sites,side,sequences=('MOG antibody-associated myelitis, source diagnosis','40-year-old male; prior leukaemia','MRI',['C6-T10 spinal cord','central gray matter'],'bilateral symptoms; lesion side not separately reported',{'a':'baseline sagittal T2','b':'baseline axial T2','c':'follow-up axial T2','d':'follow-up sagittal T2'})
            panels=list(sequences);types={p:('CT' if 'CT' in seq else 'DSA' if 'angiogram' in seq else 'MRI') for p,seq in sequences.items()};clinical_panels=[p for p,t in types.items() if t=='MRI'];identity=f'{pmc}-figure-{n}'
            context={'setting':'in_vivo' if kind=='MRI' else 'schematic','reported_case_group':identity if kind=='MRI' else None,'reported_patient':case,'depicted_state':'myelopathy_source_'+pmc.lower()+'_fig'+str(n),'source_reported_condition':condition,'anatomical_sites_from_source_caption':sites,'laterality':side,'source_panel_sequences':sequences,'panel_types':types,'clinical_panels':clinical_panels,'independent_patient_identity_verified':False,'native_sequence_and_registration_verified':False,'native_DICOM_or_volumetric_stack_supplied':False,'complete_structure_boundaries_verified':False,'diagnosis_is_source_reported':True}
            age=re.search(r'(\d+)-year',case);sex=re.search(r'\b(female|male|boy|girl)\b',case)
            context['population']={'life_stage':'paediatric' if age and int(age.group(1))<18 else 'adult' if age else 'not_applicable' if kind=='diagram' else 'not_reported','source_reported_age_years':int(age.group(1)) if age else None,'source_reported_sex':{'boy':'male','girl':'female'}.get(sex.group(1),sex.group(1)) if sex else 'not_reported'}
            if pmc=='PMC6108975' and n in [7,12]:context['panel_timepoints']={p:('follow-up; interval not reported' if n==7 and p=='d' else 'post-treatment; interval not reported' if n==12 and p=='b' else 'baseline/pre-treatment') for p in panels}
            if pmc=='PMC6108975' and n==18:
                context['source_burned_acquisition_panel_markers']={'c':{'text':'LEFT T-7','basis':'preserved source angiogram artwork; not reported in caption','role':'acquisition-panel marker only','lesion_side_or_full_feeder_anatomy_independently_established':False}}
            if pmc=='PMC12394311':
                context['anatomical_sites_from_source_caption']=['central gray matter H-pattern','longitudinally extensive spinal cord myelitis; exact levels not stated in caption']
                context['anatomical_sites_from_article_case_text']=['C6-T10 spinal cord']
                context['anatomical_site_source_basis']={'C6-T10 spinal cord':{'source':'article abstract and Case presentation','source_reported':True},'central gray matter H-pattern':{'source':'Figure 1 caption','source_reported':True}}
            if pmc=='PMC12394311':context['panel_timepoints']={'a':'baseline','b':'baseline','c':'follow-up; interval not reported','d':'follow-up; interval not reported'}
            if pmc=='PMC6108975' and n==24:context['panel_posture']={'a':'source anterior-horn T2 image','b':'flexion'};context['neutral_flexion_registration_verified']=False
            creator_credit=('Illustrations: Nadezhda Kiriyak (published acknowledgement). '+('Artwork printed name: Nadezhda D. Kiriyak. ' if n<=2 else '')+'Figure formatting: Margaret Kowaluk, University of Rochester. ') if pmc=='PMC6108975' and n<=3 else ''
            credit=f"© The Author(s) {'2018' if pmc=='PMC6108975' else '2025'}. "+', '.join(authors)+'. '+metadata['title']+'. DOI '+metadata['doi']+'. CC BY 4.0, '+license_url+'. Complete original Figure '+str(n)+' from the publisher PDF; no resampling, channel transformation or annotation removal. '+('Original RGB ICC profile retained by metadata insertion; original JPEG stream remains separately retained. ' if inserted else 'Lossless source sample packaging. ')+creator_credit+'NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
            intent=str(obj.get('/Intent')) if obj.get('/Intent') is not None else None;header_intent=int.from_bytes(profile[64:68],'big') if profile else None
            color_context={'PDF_source_rendering_intent':intent,'source_ICC_header_rendering_intent':header_intent,'source_ICC_header_intent_label':'perceptual' if header_intent==0 else None,'original_samples_and_profile_preserved':True,'full_PDF_rendering_context_and_object_override_preserved_in_unchanged_PDF':True,'standalone_browser_display_equivalence_verified':False}
            limits='Complete selected published figure; no native DICOM acquisition, full sequence stack, spatial calibration, independently verified patient identity or timing, volumetric geometry, fine anatomical boundaries or independently approved diagnosis. Author-reported levels, sequences and conditions remain source descriptions. Other modalities and follow-up/posture panels cannot supply missing MRI evidence or independently registered geometry. Clinical and fine anatomical approval remain pending. Standalone browser/display colour equivalence is unverified; the unchanged source PDF preserves its complete rendering context and explicit image-object rendering intent.'
            record={'pmcid':pmc,'figure_number':n,'figure_id':fig.get('id'),'source_caption_full':caption,'HTML_figure_url':link,'HTML_sha256':sha(html_raw),'HTML_dimensions':list(reference.size),'publisher_figure_MD5_verified':True,'PDF_object_id':oid,'PDF_page':page_num,'PDF_image_rect_points':list(rect),'PDF_image_filter':str(obj['/Filter']),'PDF_source_color_space':str(color),'source_mode':mode,'width':size[0],'height':size[1],'bytes':len(encoded),'packaged_path':str(media_path.relative_to(ROOT)),'sha256':sha(encoded),'decoded_source_channel_sha256':sha(samples),'original_encoded_stream_sha256':sha(stream),'original_PDF_encoded_stream_retained':True,'original_PDF_samples_verified':True,'highest_resolution_of_acquired_HTML_and_PDF_verified':size[0]>=reference.size[0] and size[1]>=reference.size[1],'native_acquisition_or_author_working_master_verified':False,'source_pixels_changed':False,'annotations_removed':False,'resampling_or_enhancement':False,'PDF_overlay_text_within_image_rect':overlay_text,'PDF_vector_paths_intersecting_image_rect':len(vector_paths),'original_PDF_preserves_all_vectors_text_and_profiles':True,'illustrator_acknowledgement_name':'Nadezhda Kiriyak' if pmc=='PMC6108975' and n<=3 else None,'illustrator_artwork_printed_name':'Nadezhda D. Kiriyak' if pmc=='PMC6108975' and n<=2 else None,'PDF_source_rendering_intent':intent,'source_ICC_header_rendering_intent':header_intent,'standalone_browser_display_equivalence_verified':False,'color_context':color_context,'ICC_profile_sha256':sha(profile) if profile else None,'ICC_profile_bytes':len(profile) if profile else 0,'ICC_PDF_object':icc_object,'JPEG_ICC_inserted_metadata_bytes':inserted,'source_profile_exact_readback_verified':bool(profile),'numbered_HTML_PDF_thumbnail_RGB_RMS':rms,'separate_figure_attribution_or_permission_block':False,'caption_separate_credit_exception_found':False,'source_context':context,'clinical_approval':False,'anatomical_approval':False}
            figures.append(record)
            row={'id':'open-'+spec['prefix']+f'-fig{n}','kind':'clinical-image' if kind=='MRI' else 'anatomical-illustration','src':'/app/reference-media/radiology-open/'+media_name,'width':size[0],'height':size[1],'sha256':sha(encoded),'source_url':article['source_article_url'],'figure_url':article['source_article_url']+'/#'+fig.get('id'),'figure_number':n,'asset_source_url':metadata['pdf_url'].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/'),'modality':kind,'image_state':context['depicted_state'],'source_context':context,'color_context':color_context,'caption':caption,'alt':f'Complete source figure {n}: '+caption,'license':'CC BY 4.0','license_url':license_url,'attribution':credit,'limits':limits,'clinical_panels':clinical_panels,'structures_visible':['Source-described '+site for site in sites],'rights_reviewed_on':DATE,'source_background':'white','integration_status':'proposed_not_registered'}
            row['ancillary_panels']=[{'kind':kind_name,'panels':[p for p,t in types.items() if t==kind_name],'limits':'Separate acquired modality; cannot supply unperformed MRI signal, full geometry or independent registration.'} for kind_name in ['CT','DSA'] if kind_name in types.values()]
            image_rows.append(row);assets.append({'id':row['id'],'kind':'clinical_image' if kind=='MRI' else 'anatomical_illustration','local_path':record['packaged_path'],'sha256':row['sha256'],'investigation_ids':['ra.mri-myelopathy'],'structure_ids':[],'requirement_coverage':{},'source':{'url':row['source_url'],'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':{'name':'CC BY 4.0','url':license_url,'commercial_use':True,'redistribution':True,'review_status':'verified_source_grant','attribution':credit}},'modality':kind,'source_context':context,'color_context':color_context,'pixel_provenance':record,'anatomical_review':{'status':'pending','reason':limits},'runtime_registered':False})
        articles.append(article)
    proof={'reviewed_at':DATE,'investigation_id':'ra.mri-myelopathy','articles':articles,'figures':figures,'packaged_asset_bytes':total,'packaged_asset_MiB':total/1024**2,'runtime_margin_context_bytes':26000000,'storage_plan':'All selected complete figures and the two unchanged original PDFs fit within the stated 26 MB margin without reducing resolution or channels. The proposed asset bundle is below 15 MB.','standalone_browser_display_equivalence_verified':False,'full_source_named_scope_independently_audited':False,'commercial_redistribution_source_grants_verified':True,'licence_attribution_and_third_party_caption_review':True,'clinical_approval':False,'fine_anatomical_approval':False,'requirement_coverage_granted':False,'runtime_registry_mutated':False}
    proof_bytes=(json.dumps(proof,indent=2,ensure_ascii=False)+'\n').encode();proof_sha=sha(proof_bytes)
    for asset in assets:asset['source']['license'].update(evidence_path=str((FOLDER/'original-source-review.json').relative_to(ROOT)),evidence_sha256=proof_sha,reviewed_at=DATE)
    for name,data in [('original-source-review.json',proof),('proposed-image-rows.json',{'ra.mri-myelopathy':image_rows}),('proposed-asset-evidence-rows.json',{'assets':assets})]: (FOLDER/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    print(f'Preserved {len(figures)} complete figures and {len(articles)} original PDFs; {total} bytes ({total/1024**2:.3f} MiB); original samples, JPEG streams and source ICC verified. No runtime/clinical promotion.')


def requirement_draft():
    """Enumerate source-specific scope; examples never close complete anatomy."""
    existing=json.loads((FOLDER/'existing-requirement-contract.json').read_text());contract=existing['reporting_contract'];guide=contract['reporting'];shared=json.loads((FOLDER/'existing-shared-curriculum-contract.json').read_text());proof=json.loads((FOLDER/'original-source-review.json').read_text());structures=[]
    def add(key,name,parts,sites,side,reports,steps,modes=None,condition='every_actual_covered_normal_variant_lesion_or_post_treatment_state',basis='reporting_and_walkthrough',figures=None):
        ident='myelopathy.'+key
        structures.append({'id':ident,'name':name,'tissue_class':'source_resolved_spinal_cord_tract_compartment_interface_or_assessment','required_parts':[{'id':ident+'.'+p,'name':p.replace('_',' ')} for p in parts], 'anatomical_site_scope':sites,'laterality':side,'modality_scope':modes or ['MRI'],'condition':condition,'requirement_basis':basis,'report_refs':[{'checklist_index':i,**guide['checklist'][i]} for i in reports],'walkthrough_step_indices':steps,'requires_site_instantiation':True,'context_requirements':{'purpose':'pathology_or_anatomical_reference','population':'instantiate_actual_adult_paediatric_and_developmental_context','source_state':'instantiate_actual_disease_case_timepoint_posture_and_acquisition'},'candidate_figure_ids':figures or [],'representation_status':{'image':'pending_fine_boundary_and_full_extent_review','schematic':'pending_independent_anatomical_review','model':'missing_source_native_complete_geometry'},'clinical_approval':False})
    tissue=['full_actual_obtained_extent','each_resolved_boundary_and_tissue_interface','each_actual_level_lesion_variant_or_treatment_change','matched_axial_sagittal_source_sequences_and_coordinates','neural_versus_vertebral_level_mapping_if_supported','partial_volume_motion_and_unassessed_extent']
    lesion=tissue+['each_resolved_internal_signal_enhancement_diffusion_or_haemorrhagic_component','full_longitudinal_and_axial_extent_or_explicit_crop_limit','calibrated_length_area_or_volume_if_source_supplied','clinical_timing_and_differential_separate_from_pixels']
    route=tissue+['every_resolved_branch_origin_connection_and_endpoint','feeding_draining_or_perimedullary_relation_if_acquired','flow_haemodynamics_or_angiographic_confirmation_separate_from_static_MRI']
    sites=['cervicomedullary_junction','cervical_cord','thoracic_cord','conus_medullaris']
    for site in sites:
        for side in ['left','right']:
            for part in ['dorsal_white_column','lateral_white_column','anterior_white_column','anterior_gray_horn','posterior_gray_horn']:
                add(site+'.'+side+'.'+part,f'{side} {part.replace("_"," ")} at {site.replace("_"," ")}',tissue,[site],side,[1,2,3],[1,2,3])
        for part in ['complete_cord_contour_and_calibre','central_gray_matter_and_commissural_region','central_canal_if_resolved','cord_CSF_surface_and_pial_interface','covered_neural_segment_and_vertebral_level_registration','each_additional_actual_neural_tract_or_component_if_reported']:
            add(site+'.'+part,f'{part.replace("_"," ")} at {site.replace("_"," ")}',tissue,[site],'midline_or_whole_cross_section',[1,2,3],[1,2,3])
    for region in ['cervical_spine','thoracic_spine','lumbar_spine_and_conus_root_transition']:
        for part in ['vertebral_body_and_posterior_cortex','intervertebral_disc_and_disc_osteophyte_interface','spinal_canal_and_thecal_sac','posterior_longitudinal_ligament_and_source_ossification','ligamentum_flavum','posterior_epidural_compartment','anterior_epidural_compartment','lateral_epidural_compartment','source_intradural_extramedullary_abnormality','dura_and_arachnoid_interfaces_if_resolved','actual_compressive_focus_and_adjacent_cord_or_roots']:
            add(region+'.'+part,f'{part.replace("_"," ")} in {region.replace("_"," ")}',lesion,[region],'every_actual_left_right_midline_or_circumferential_site',[0,1,3],[0,1,3],['MRI','CT_if_acquired_for_bone_or_calcification'],'instantiate_every_actual_level_cause_and_component_of_compression')
    for side in ['left','right']:
        for part in ['conus_root_transition','cauda_equina_each_actual_covered_root','lumbar_and_sacral_root_thecal_sac_interface','each_actual_foraminal_or_extraforaminal_root_if_reported']:
            add('roots.'+side+'.'+part,f'{side} {part.replace("_"," ")}',route,['conus','lumbar_and_sacral_thecal_sac','each_actual_root_exit_and_foramen'],side,[0,4],[0,4],condition='GBS_or_compression_or_other_actual_root_process_separate_from_intramedullary_lesion')
    for part in ['dorsal_perimedullary_veins','ventral_perimedullary_vessels','each_actual_radiculomedullary_or_paraspinal_feeding_artery','each_actual_DAVF_connection','each_actual_AVM_nidus','each_actual_draining_vein','covered_anterior_spinal_arterial_territory','covered_aorta_and_relevant_segmental_arteries_if_acquired']:
        add('vascular.'+part,part.replace('_',' '),route,['every_actual_covered_cord_level','conus','thecal_sac','covered_paraspinal_or_aortic_vascular_route'],'instantiate_every_actual_side_and_vascular_endpoint',[2,4],[2,4],['MRI','MRA_if_acquired','DSA_if_acquired','CTA_if_acquired'],condition='DAVF_AVM_cavernoma_infarct_or_other_actual_vascular_process')
    for part in ['left_optic_nerve_and_obtained_orbital_path','right_optic_nerve_and_obtained_orbital_path','brainstem_and_cervicomedullary_relation','thalami_and_actual_deep_gray_matter_lesions','each_actual_periventricular_subcortical_callosal_or_cerebellar_lesion','fourth_ventricle_and_actual_tumour_pressure_effect','each_actual_extra_spinal_or_systemic_association_if_imaged']:
        add('associated.'+part,part.replace('_',' '),lesion,['actual_covered_brain_orbit_or_extra_spinal_sites'],'derive_only_from_actual_source_side_marker_or_caption',[4],[4],condition='associated_brain_optic_or_extra_spinal_findings_only_if_actually_acquired')
    conditions=[
      ('multiple_sclerosis',[4,5],['short_or_uncommonly_long_segment','dorsal_lateral_or_other_actual_distribution','active_enhancing_and_nonactive_or_atrophic_states']),
      ('AQP4_NMOSD',[6],['central_gray_white_involvement','longitudinally_extensive_or_actual_short_lesion','actual_optic_and_brain_associations']),
      ('MOGAD',[],['actual_short_or_long_gray_matter_H_pattern','conus_and_root_involvement_if_acquired','actual_follow_up_and_enhancement_state']),
      ('ADEM',[7],['cervical_and_thoracic_cord','brainstem_and_deep_gray_associations','actual_follow_up']),
      ('acute_partial_transverse_myelitis',[9],['actual_short_lesion','cross_sectional_distribution','clinical_and_laboratory_aetiology_not_proven_by_MRI']),
      ('acute_complete_transverse_myelitis',[9],['actual_long_lesion','bilateral_or_diffuse_distribution','clinical_and_laboratory_aetiology_not_proven_by_MRI']),
      ('idiopathic_or_systemic_autoimmune_transverse_myelitis',[],['actual_level_extent_and_enhancement','SLE_Sjogren_Behcet_or_other_actual_clinical_association']),
      ('vasculitis',[],['actual_spinal_and_brain_lesions','infarct_or_enhancing_pattern','histologic_serologic_and_vessel_evidence_if_supplied']),
      ('infectious_or_post_infectious_myelitis',[],['actual_level_lesion_or_meningeal_root_component','organism_and_inflammatory_aetiology_require_clinical_sources']),
      ('HIV_myelopathy',[10],['dorsal_cord_pattern','actual_calibre_or_atrophy','source_HIV_context_not_inferred_from_pixels']),
      ('vitamin_B12_deficiency',[12],['dorsal_column_pattern','actual_pre_post_treatment_states','biochemical_confirmation_not_image_morphology']),
      ('copper_deficiency',[11],['symmetric_dorsal_column_pattern','actual_longitudinal_extent','biochemical_confirmation']),
      ('other_actual_metabolic_or_exposure_myelopathy',[],['actual_dorsal_or_other_tract_pattern','actual_exposure_laboratory_context']),
      ('Guillain_Barre_root_process',[8],['conus_if_abnormal','each_actual_enhancing_root','separate_peripheral_root_from_cord_tissue']),
      ('intramedullary_astrocytoma',[15],['each_actual_solid_cystic_or_infiltrative_component','cord_brainstem_or_other_extension','acquired_histologic_molecular_identity']),
      ('intramedullary_ependymoma',[13],['central_cord_component','each_actual_cyst_syrinx_haemorrhage_or_cap_if_resolved','actual_histology_and_subtype']),
      ('haemangioblastoma',[14],['each_actual_enhancing_nodule','feeding_vessels_and_syrinx','VHL_context_if_supplied']),
      ('intramedullary_metastasis',[16],['each_actual_lesion_enhancing_component_and_oedema','known_systemic_cancer_and_multiplicity','do_not_substitute_intramedullary_case_for_epidural_metastasis']),
      ('spinal_high_grade_glioma',[17],['each_actual_expansile_component_and_enhancement','actual_distal_cord_or_other_level','historical_GBM_label_not_a_current_molecular_WHO_diagnosis']),
      ('spinal_DAVF',[18,19],['cord_congestion','perimedullary_flow_voids','actual_fistula_feeder_drainer_angiographic_evidence']),
      ('spinal_AVM',[20],['actual_nidus','feeding_draining_routes','haemorrhage_or_oedema_if_acquired']),
      ('spinal_cavernoma',[21],['each_actual_mixed_signal_component','haemosiderin_and_GRE_or_SWI_susceptibility','actual_enhancement']),
      ('spinal_cord_infarction',[22],['actual_anterior_or_other_territory','paired_DWI_ADC','aortic_or_segmental_vascular_context_if_acquired']),
      ('degenerative_compressive_myelopathy',[23],['actual_disc_osteophyte_or_ligament_cause','adjacent_cord_signal_calibre_and_enhancement','each_actual_level']),
      ('Hirayama_flexion_process',[24],['actual_anterior_horn_and_asymmetric_atrophy','dural_displacement_epidural_change_and_thecal_sac','neutral_flexion_posture_and_no_false_registration']),
      ('epidural_haemorrhagic_compression',[],['actual_compartment_and_blood_component','cord_or_root_compression','blood_age_and_anticoagulation_context']),
      ('epidural_neoplastic_compression',[],['vertebral_epidural_and_paraspinal_components','full_obtained_craniocaudal_extent','whole_spine_multiplicity_and_urgent_communication']),
      ('traumatic_compressive_myelopathy',[],['fracture_displaced_bone_disc_or_ligament','actual_cord_haemorrhage_oedema_and_tissue_bridges','actual_stability_neurological_context']),
      ('each_other_actual_postoperative_radiation_or_treatment_related_cord_process',[],['actual_timing_level_component_and_comparison','clinical_causality_separate_from_published_example'])]
    for condition,numbers,details in conditions:
        ids=['open-myelopathy-moghaddam2018-fig'+str(n) for n in numbers]
        if condition=='MOGAD':ids=['open-myelopathy-mogad2025-fig1']
        add('condition.'+condition,condition.replace('_',' '),lesion+details,['every_actual_obtained_neural_and_vertebral_level','each_actual_brain_orbit_root_vessel_or_extra_spinal_association'],'instantiate_left_right_midline_bilateral_or_circumferential_actual_distribution',[0,1,2,3,4],[0,1,2,3,4],condition=condition,basis='named_reporting_reading_walkthrough_and_source_case_scope',figures=ids)
    # Historical literal associations are separate conditional obligations,
    # not modern diagnoses or causal claims. No source-table image is copied.
    table_url='https://radiologyassistant.nl/assets/spine-myelopathy/a509797ada1d4c_TAB-2.png'
    table_entries=[
      ('Parainfectious / Viral','HSV','HSV'),
      ('Parainfectious / Viral','herpes zoster','herpes_zoster'),
      ('Parainfectious / Viral','cytomegalovirus','cytomegalovirus'),
      ('Parainfectious / Viral','Epstein-Barr virus','Epstein_Barr_virus'),
      ('Parainfectious / Viral','enteroviruses','enteroviruses'),
      ('Parainfectious / Viral / enteroviruses','poliomyelitis','poliomyelitis'),
      ('Parainfectious / Viral / enteroviruses','Coxsackie virus','Coxsackie_virus'),
      ('Parainfectious / Viral / enteroviruses','echovirus','echovirus'),
      ('Parainfectious / Viral','human T-cell, leukemia virus','ambiguous_human_T_cell_comma_leukemia_virus'),
      ('Parainfectious / Viral','human immunodeficiency virus','human_immunodeficiency_virus'),
      ('Parainfectious / Viral','influenza','influenza'),
      ('Parainfectious / Viral','rabies','rabies_infectious_context'),
      ('Parainfectious / Bacterial','Mycoplasma pneumoniae','Mycoplasma_pneumoniae'),
      ('Parainfectious / Bacterial','Lyme borreliosis','Lyme_borreliosis'),
      ('Parainfectious / Bacterial','syphilis','syphilis'),
      ('Parainfectious / Bacterial','tuberculosis','tuberculosis'),
      ('Postvaccinal','rabies','rabies_postvaccinal_context'),
      ('Postvaccinal','cowpox','cowpox_postvaccinal_context'),
      ('Systemic autoimmune disease','SLE','SLE'),
      ('Systemic autoimmune disease',"Sjogren's syndrome",'Sjogrens_syndrome'),
      ('Systemic autoimmune disease','Sarcoidosis','sarcoidosis'),
      ('Named condition','Multiple Sclerosis','Multiple_Sclerosis_table_context'),
      ('Named condition','Paraneoplastic syndrome','paraneoplastic_syndrome'),
      ('Vascular','Thrombosis of spinal arteries','thrombosis_of_spinal_arteries'),
      ('Vascular','Vasculitis secondary to heroin abuse','heroin_associated_vasculitis'),
      ('Vascular','AV-malformation','AV_malformation_table_context')]
    literal_scope=[]
    for category,label,key in table_entries:
        add('literal_TM_table.'+key,'Historical TM table association: '+label,lesion+['actual_source_reported_organism_exposure_or_systemic_context','actual_acquired_microbiology_serology_or_tissue_evidence_if_supplied','actual_temporal_relation_with_no_causal_approval_from_table','source_label_and_modern_interpretation_separately_recorded','historical_source_association_requires_current_specialist_review'],['every_actual_covered_spinal_cord_level','each_actual_root_meningeal_brain_or_systemic_site_if_acquired'],'instantiate_every_actual_left_right_midline_or_bilateral_distribution',[0,1,2,3,4],[0,1,2,3,4],condition='conditional_actual_source_reported_'+key,basis='literal_historical_RA_TM_association_table')
        record={'source_title':'Diseases associated with TM','source_url':table_url,'source_category':category,'literal_label':label,'requirement_group_id':'myelopathy.literal_TM_table.'+key,'source_basis':'Independent reviewer personally read the primary table image; literal transcription supplied 2026-10-11','current_clinical_or_causal_validity_approved':False,'source_image_acquired_or_redistributed':False,'fine_anatomical_approval':False,'status':'explicit_conditional_requirement_pending_independent_reaudit_and_specialist_review'}
        if key=='ambiguous_human_T_cell_comma_leukemia_virus':record.update(literal_label_tokens=['human T-cell','leukemia virus'],normalization='No modern organism name inferred; source comma and wording retained. Historical label interpretation remains pending.')
        literal_scope.append(record)
    for label,key in [('Herpes','Herpes_artwork'),('Polio','Polio_artwork'),('Post-vaccination','Post_vaccination_artwork'),('Anterior Horn Ischemia','Anterior_Horn_Ischemia_artwork'),('Cross Sectional Ischemia','Cross_Sectional_Ischemia_artwork')]:
        add('literal_Fig2.'+key,'Source Figure 2 label: '+label,lesion+['each_actual_source_resolved_tract_horn_or_cross_sectional_distribution','clinical_aetiology_or_exposure_evidence_separate_from_schematic','historical_label_and_modern_interpretation_require_review'],['each_actual_covered_cord_level'],'instantiate_actual_left_right_midline_or_bilateral_pattern',[1,2,3],[1,2,3],condition='conditional_actual_source_context_'+key,basis='literal_2018_Figure2_artwork',figures=['open-myelopathy-moghaddam2018-fig2'])
        literal_scope.append({'source_title':'2018 Figure 2 artwork','source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6108975/#Fig2','literal_label':label,'requirement_group_id':'myelopathy.literal_Fig2.'+key,'source_role':'schematic historical context; no acquired clinical case for this label','status':'explicit_conditional_requirement_pending_independent_reaudit_and_specialist_review','clinical_or_causal_approval':False})
    fine_tract_parts=tissue+['actual_named_tract_course_within_obtained_extent','every_source_resolved_fascicular_boundary_or_explicitly_unresolved_subdivision','adjacent_horn_white_column_commissural_and_pial_interfaces_if_resolved','every_actual_level_branch_crossing_or_variant_if_source_resolved','source_dependent_signal_lesion_contact_and_full_obtained_extent','source_reported_function_separate_from_image_or_model_geometry']
    for label,key in [('Spinothalamic tract','spinothalamic_tract'),('Lateral corticospinal tract','lateral_corticospinal_tract')]:
        ids=[]
        for site in sites:
            for side in ['left','right']:
                add('literal_tract.'+site+'.'+side+'.'+key,side+' '+label+' at '+site.replace('_',' '),fine_tract_parts,[site],side,[1,2,3],[1,2,3],condition='every_actual_named_tract_normal_variant_lesion_or_treatment_state',basis='literal_2018_Figure1_artwork_and_source_intramedullary_anatomy',figures=['open-myelopathy-moghaddam2018-fig1']);ids.append(structures[-1]['id'])
        literal_scope.append({'source_title':'2018 Figure 1 artwork','source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6108975/#Fig1','literal_label':label,'requirement_group_ids':ids,'fine_parts_explicit':True,'source_role':'named schematic tract; acquired MRI/fine fascicular boundaries and native 3D remain pending','status':'explicit_conditional_requirement_pending_independent_reaudit_and_specialist_review','clinical_approval':False})
    for label,part in [('Dorsal columns','dorsal_white_column'),('Central canal','central_canal_if_resolved')]:
        literal_scope.append({'source_title':'2018 Figure 1 artwork','source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6108975/#Fig1','literal_label':label,'requirement_group_ids':[s['id'] for s in structures if s['id'].endswith('.'+part)],'status':'existing_explicit_named_parts_crosswalked; pending_source_specific_boundaries_and_review','clinical_approval':False})
    differential_url='https://radiologyassistant.nl/assets/spine-myelopathy/a509797ad7c935_Diff-Diagn-1.0.png'
    differential_entries=[('Demyelinating','MS','MS'),('Demyelinating','TM','TM'),('Demyelinating','NMO','NMO'),('Demyelinating','ADEM','ADEM'),('Tumor','Astrocytoma','Astrocytoma'),('Tumor','Ependymoma','Ependymoma'),('Tumor','Hemangioblastoma','Hemangioblastoma'),('Tumor','Metastases','Metastases'),('Tumor','Lymphoma','Lymphoma'),('Vascular','Ischemia','Ischemia'),('Vascular','Spinal AVM','Spinal_AVM'),('Inflammatory','Vasculitis','Vasculitis'),('Inflammatory','Sarcoidosis','Sarcoidosis'),('Infection','Herpes - VZV','Herpes_VZV'),('Infection','HIV - VM - TB','HIV_VM_TB'),('Infection','Bacteria','Bacteria'),('Infection','Toxo - Fungus','Toxo_Fungus'),('Infection','Cysticercosis','Cysticercosis')]
    for category,label,key in differential_entries:
        add('literal_RA_differential.'+key,'Historical differential graphic: '+label,lesion+['each_actual_named_infectious_neoplastic_inflammatory_or_vascular_context','source_abbreviation_and_literal_label_without_silent_normalization','clinical_tissue_microbiology_or_causal_evidence_if_actually_supplied'],['every_actual_covered_cord_level','actual_acquired_brain_meningeal_root_or_systemic_association'],'instantiate_actual_left_right_midline_bilateral_or_circumferential_distribution',[0,1,2,3,4],[0,1,2,3,4],condition='conditional_actual_source_label_'+key,basis='literal_RA_differential_diagnosis_artwork')
        record={'source_title':'Guide Differential diagnosis graphic','source_url':differential_url,'source_category':category,'literal_label':label,'requirement_group_id':'myelopathy.literal_RA_differential.'+key,'source_basis':'Independent reviewer personally read the complete primary graphic; literal transcription supplied 2026-10-11','historical_source_label':True,'source_graphic_is_not_clinical_case_evidence':True,'current_clinical_or_causal_validity_approved':False,'source_image_acquired_or_redistributed':False,'status':'explicit_conditional_requirement_pending_independent_reaudit_and_specialist_review'}
        if key=='HIV_VM_TB':record.update(source_label_tokens=['HIV','VM','TB'],normalization='VM abbreviation retained verbatim; no expansion or modern diagnosis inferred. HIV and TB also have distinct table requirements.')
        if key=='Herpes_VZV':record.update(source_label_tokens=['Herpes','VZV'],normalization='Both historical label tokens retained; source graphic supplies no organism confirmation.')
        if key=='Toxo_Fungus':record.update(source_label_tokens=['Toxo','Fungus'],normalization='Both label tokens retained; toxoplasma/fungal interpretations require actual source clinical or laboratory evidence, not this schematic.')
        literal_scope.append(record)
    supplied_contexts=[('Nitric oxide use / Nitric oxide inhalation','literal_nitric_oxide','2018 metabolic section and Table 2','Historical source wording retained: nitric oxide and nitrous oxide are different chemicals. No silent normalization; clinical/editorial reconciliation pending.'),('Neurofibromatosis','neurofibromatosis','Guide spinal cord tumour discussion','An actual supplied clinical association is required; no diagnosis from an enhancing mass.'),('NF2','NF2','2018 ependymoma section','Source NF2 association/gene context retained; no genetic test or neurofibromatosis diagnosis inferred from MRI.'),('Neurofibromatosis type I','neurofibromatosis_type_I','2018 astrocytoma section','Actual supplied clinical association remains required.'),('Von Hippel Lindau syndrome (VHL)','VHL','2018 haemangioblastoma section','Actual supplied clinical or genetic context remains required.')]
    for label,key,basis,qualification in supplied_contexts:
        add('literal_article_context.'+key,'Source clinical/exposure context: '+label,lesion+['actual_source_reported_clinical_genetic_or_exposure_context','specific_source_term_and_modern_interpretation_kept_distinct','clinical_causality_or_genetic_approval_not_provided_by_pixels'],['every_actual_covered_cord_or_associated_site'],'actual_source_reported_side_only',[1,2,3,4],[1,2,3,4],condition='conditional_actual_supplied_'+key,basis=basis)
        literal_scope.append({'source_title':basis,'source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6108975/' if key!='neurofibromatosis' else 'https://radiologyassistant.nl/neuroradiology/spine/myelopathy','literal_label':label,'requirement_group_id':'myelopathy.literal_article_context.'+key,'qualification':qualification,'clinical_or_causal_approval':False,'status':'explicit_supplied_context_dependency_pending_independent_reaudit_and_specialist_review'})
    # All shared curriculum quiz rows are retained as distinct requirements,
    # including the disc/trauma rows not illustrated by this source batch.
    quiz_descriptors=[
      ('disc_extrusion_geometry',['L5-S1'],'side_not_reported',['MRI'],['disc_space','parent_disc','herniation_base_and_displaced_extent','canal_and_actual_root_relation']),
      ('migrated_sequestered_fragment',['L4_vertebral_level','L4-L5_origin'],'right',['MRI'],['right_lateral_recess','right_L5_root','disc_continuity','enhancing_rim_and_non_enhancing_centre']),
      ('postoperative_scar_versus_recurrent_disc',['L5-S1'],'left',['MRI_pre_and_early_post_contrast_with_recorded_timing'],['left_anterior_epidural_compartment','operated_disc','scar_or_disc_components','thecal_sac_and_root_interfaces']),
      ('TLICS_burst_PLC_neurology',['L1','thoracolumbar_junction'],'midline_and_each_actual_posterior_component',['CT','MRI_STIR_or_equivalent'],['retropulsed_posterior_wall','interspinous_space','supraspinous_ligament','interspinous_ligament','actual_neurological_status']),
      ('disc_nomenclature_definitions',['every_actual_lumbar_disc_level'],'every_actual_zone_and_side',['MRI'],['circumferential_bulge','focal_herniation','base_and_displaced_geometry','continuity_or_sequestration']),
      ('metastatic_epidural_conus_compression',['T12','whole_obtained_spine'],'side_not_reported',['MRI_whole_spine'],['vertebral_marrow','epidural_mass','conus','additional_non_contiguous_lesions']),
      ('cord_vs_cauda_equina_compartment',['T9-T10','L4-L5','conus_and_sacrum'],'central_and_each_actual_root_side',['MRI'],['thoracic_cord','conus_termination','lumbar_sacral_roots','actual_upper_and_lower_exam_extent']),
      ('benign_vs_pathological_collapse',['L2'],'superior_endplate_and_each_actual_cortex_pedicle_side',['MRI','CT_if_acquired'],['superior_endplate_subendplate_band','fatty_marrow','posterior_corner','both_pedicles','epidural_paraspinal_tissue']),
      ('Modic1_vs_infection',['L4-L5'],'both_adjacent_endplates_and_actual_paraspinal_sides',['MRI'],['disc_signal_and_intranuclear_cleft','continuous_or_eroded_endplate_cortex','marrow_oedema','paraspinal_epidural_tissue']),
      ('Chance_flexion_distraction_and_bowel_mesenteric_association',['L2','abdomen'],'both_pedicles_and_actual_abdominal_site',['CT','MRI_if_PLC_acquired'],['spinous_process','pedicles','posterior_body','anterior_wedge','bowel','mesentery','free_fluid_and_gas']),
      ('vertebral_height_loss',['actual_thoracic_vertebral_level'],'anterior_and_posterior_body',['lateral_radiograph'],['anterior_height','posterior_reference_height','superior_and_inferior_endplates','adjacent_reference_vertebrae']),
      ('PLC_integrity',['L1','actual_adjacent_posterior_levels'],'midline_and_both_facets',['CT','MRI_STIR_or_equivalent'],['supraspinous_ligament','interspinous_ligament','ligamentum_flavum','both_facet_capsules_and_alignment','avulsion_sites','indeterminate_vs_disrupted_complex'])]
    quiz=[]
    for i,(key,q) in enumerate(zip(quiz_descriptors,shared['quiz']),1):
        concept,qs,side,modes,parts=key;add('quiz'+str(i)+'.'+concept,concept.replace('_',' '),lesion+parts,qs,side,[0],[0],modes,condition=concept,basis='shared_curriculum_quiz_Q'+str(i))
        quiz.append({'quiz_index':i,'kind':q['kind'],'prompt':q['prompt'],'authored_answer':q.get('answer'),'requirement_group_id':'myelopathy.quiz'+str(i)+'.'+concept,'anatomical_sites':qs,'laterality':side,'modality_scope':modes,'required_named_parts':parts,'candidate_source_coverage':'none; selected intramedullary myelopathy figures cannot establish this shared disc/trauma/epidural/radiographic requirement','status':'draft_dependency_unverified_not_removed'})
    field_crosswalk=[]
    fields={k:guide.get(k) for k in ['protocol','checklist','measurements','classification','criteria_table','pitfalls','impression_prompts','escalation','template_sections']}
    for section,value in fields.items():
        if value is None:field_crosswalk.append({'source_path':'reporting.'+section,'source_value':None,'status':'explicitly_not_authored_no_classification_invented'});continue
        for i,item in enumerate(value):field_crosswalk.append({'source_path':f'reporting.{section}[{i}]','source_value':item,'coverage_contract':'complete_field_retained; instantiate every actual named level, structure, source acquisition and limitation','clinical_review_status':'pending'})
    for i,template in enumerate(contract['report_templates']):
        for j,section in enumerate(template['sections']):field_crosswalk.append({'source_path':f'report_templates[{i}].sections[{j}]','source_value':section,'status':'all_heading_and_body_fields_retained','clinical_review_status':'pending'})
    for i,step in enumerate(contract['walkthrough']['steps']):
        field_crosswalk.append({'source_path':f'walkthrough.steps[{i}]','source_value':step,'candidate_figure_ids':{'0':[23],'1':[4,5,6,7,9,13,15,18,22],'2':[4,5,6,9,11,22,24],'3':[5,6,9,10,13,14,15,17,21,23],'4':[6,7,8,14,18,19,20]}[str(i)],'image_binding_status':'proposed_named_examples_only; fine boundaries, full acquired extent and condition coverage remain pending'})
    for part in ['start','finish']:field_crosswalk.append({'source_path':'walkthrough.'+part,'source_value':contract['walkthrough'][part],'status':'complete_named_sections_retained'})
    review_flags=[
      'The current inherited walkthrough normal text says no enhancement: this must only be selectable with diagnostic post-contrast acquisition; otherwise enhancement is not assessed.',
      'Two-vertebral-segment lesions do not fit the inherited <2 versus >=3 binary. Preserve exact level/length rather than force a disease label or round a boundary.',
      'The source review includes short partial transverse myelitis; long-versus-short and axial patterns narrow a differential and do not establish aetiology or exclude overlap.',
      'The original metabolic source says nitric oxide use/inhalation; do not silently substitute nitrous oxide. These are different chemicals and source wording requires clinical/editorial reconciliation.',
      'MOGAD H-sign, infarct anterior horns and other gray-matter patterns overlap; require timing, actual paired DWI/ADC, antibodies and clinical data when relevant.',
      'Inherited shared Q4 answer5 assumes PLC disruption. Edema/high STIR without unequivocal rupture may be indeterminate (2 points), not automatically disrupted (3); the stem needs specialist reconciliation before a fixed clinical-grade answer is certified.',
      'Inherited shared Q5 treats bulge, protrusion, extrusion and sequestration as a single increasing-displacement grade. Standard nomenclature separates geometry and continuity; retain as an assessment dependency requiring editorial/clinical review.',
      'Shared Q3 precise early versus delayed contrast timings and management statements need current protocol/specialist validation; published myelopathy examples cannot certify postoperative lumbar scar/disc behavior.',
      'Historical source glioblastoma terminology and imaging morphology do not establish a current integrated molecular tumour diagnosis or WHO grade.',
      'No acquired source supplies a full native DICOM study, source-native patient-specific 3D tissue model, quantitative flow/cord function, complete fine tract/meningeal boundaries, or whole-site normal reference.']
    draft={'schema_version':1,'investigation_id':'ra.mri-myelopathy','module_id':'rad.4.spine-imaging','title':'MRI myelopathy: full named reporting, walkthrough and shared quiz requirement draft','scope_status':'expanded_draft_not_integrated_requires_neuroradiologist_review','clinical_validation_status':'draft_requires_neuroradiologist_and_spinal_specialist_review','required_representations':['image','schematic','model'],'modality_scope':['MRI','MRA_if_acquired','DSA_if_acquired','CTA_or_CT_if_acquired_for_named_ancillary_role','radiograph_only_for_explicit_shared_quiz_dependency'],'source_contract_sha256':existing['reporting_contract_sha256'],'source_contract_file_sha256':sha((FOLDER/'existing-requirement-contract.json').read_bytes()),'shared_curriculum_contract_file_sha256':sha((FOLDER/'existing-shared-curriculum-contract.json').read_bytes()),'reporting_checklist':guide['checklist'],'reporting_template_sections':guide['template_sections'],'structures':structures,'report_template_walkthrough_crosswalk':field_crosswalk,'reading_sections_retained':contract['reading'],'shared_quiz_requirement_crosswalk':quiz,'literal_named_source_scope_crosswalk':literal_scope,'literal_TM_table_source_entry_count':len(table_entries),'literal_RA_differential_graphic_entry_count':len(differential_entries),'full_source_named_scope_independently_audited':False,'named_source_scope_status':'literal_primary_table_and_artwork_entries_expanded_pending_independent_reaudit; no_full_source_completion_claim','scope_review_flags':review_flags,'site_instantiation_rules':['Instantiate each actual neural cord segment separately from vertebral body/disc level. Adult lumbar/sacral neural segments lie in the lower cord and must not be modelled as a spinal cord extending throughout the lumbar vertebral canal.','Instantiate every actual left/right/midline/bilateral tract, horn, root, lesion, interface, vascular connection and full obtained course, including cropped/unassessed boundaries.','MRI sequence/plane/phase, CT, DSA/MRA, post-treatment and flexion panels are separate evidence roles; complete figures do not supply unperformed acquisitions or independent registration.','Calibrated measurements and full-volume lesion length/area/count require their actual source acquisitions. Published composite pixels do not authorize new measurement calibration.','Normal, abnormal, paediatric/adult, neutral/flexion and pre/post treatment states are not interchangeable. Microscopic or absent tissue interfaces remain pending rather than inferred normal.'],'sources':[{'title':a['title'],'url':a['source_article_url'],'license':a['license'],'reviewed_at':DATE} for a in proof['articles']]+[{'title':'Inherited myelopathy reporting source','url':'https://radiologyassistant.nl/neuroradiology/spine/myelopathy','role':'scope/reference only; no copied clinical images'},{'title':'Shared disc nomenclature task-force recommendations','url':'https://pubmed.ncbi.nlm.nih.gov/24768732/','role':'shared assessment dependency'},{'title':'NICE NG234','url':'https://www.nice.org.uk/guidance/ng234/chapter/Recommendations','role':'urgent whole-spine MRI and communication source'}],'clinical_approval':False,'fine_anatomical_approval':False,'structure_coverage_granted':False,'runtime_integrated':False,'shared_inventory_or_evidence_mutated':False}
    parts=sum(len(s['required_parts']) for s in structures);draft['draft_counts']={'structure_groups':len(structures),'required_parts':parts,'representation_obligations':3*parts,'report_template_walkthrough_entries':len(field_crosswalk),'shared_quiz_rows':len(quiz),'published_figure_examples':25,'literal_TM_table_entries':len(table_entries),'literal_RA_differential_graphic_entries':len(differential_entries),'literal_named_source_crosswalk_entries':len(literal_scope),'verified_complete_anatomical_requirements':0}
    (FOLDER/'complete-requirement-draft.json').write_text(json.dumps(draft,indent=2,ensure_ascii=False)+'\n')
    (FOLDER/'proposed-integration-plan.json').write_text(json.dumps({'investigation_id':'ra.mri-myelopathy','registry_rows_file':'proposed-image-rows.json','asset_rows_file':'proposed-asset-evidence-rows.json','structure_draft_file':'complete-requirement-draft.json','source_proof_file':'original-source-review.json','byte_bound':proof['packaged_asset_bytes'],'do_not_promote':['clinical_approval','fine_anatomical_approval','requirement_coverage','3D_native_complete_geometry'],'preserve_existing_source_rows_and_historical_issues':True,'suggested_walkthrough_examples':{'compression':['open-myelopathy-moghaddam2018-fig23'],'longitudinal_extent':['open-myelopathy-moghaddam2018-fig5','open-myelopathy-moghaddam2018-fig6','open-myelopathy-mogad2025-fig1'],'axial_pattern':['open-myelopathy-moghaddam2018-fig4','open-myelopathy-moghaddam2018-fig11','open-myelopathy-moghaddam2018-fig22','open-myelopathy-mogad2025-fig1'],'calibre_enhancement':['open-myelopathy-moghaddam2018-fig13','open-myelopathy-moghaddam2018-fig15','open-myelopathy-moghaddam2018-fig21'],'associated_findings':['open-myelopathy-moghaddam2018-fig6','open-myelopathy-moghaddam2018-fig14','open-myelopathy-moghaddam2018-fig18','open-myelopathy-moghaddam2018-fig19']},'root_owned_next_steps':['Independent source/licence and source-pixel review','Neuroradiologist review of full named anatomy, inherited qualification issues and source-specific gaps','Reconcile into existing structure catalogue only with honest pending/verified statuses','Integrate selected complete image rows and original PDF source links with attribution','Run focused registry/schema/display QA and preserve existing fingerprints and issues','Validate actual narrow/wide reader views and any separately acquired native 3D geometry'],'integration_authorization_status':'source preparation only; no shared mutation executed'},indent=2)+'\n')
    print('Drafted',len(structures),'groups,',parts,'parts,',3*parts,'representation obligations,',len(field_crosswalk),'report/walkthrough entries and',len(quiz),'shared quiz rows; zero complete fine-anatomical approvals.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--acquire',action='store_true');review(parser.parse_args().acquire);requirement_draft()
