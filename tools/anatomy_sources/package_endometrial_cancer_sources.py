#!/usr/bin/env python3
"""Preserve licensed original endometrial MRI figures without patient/model claims.

Only selected complete source figures, metadata, captions and byte/sample evidence
are written. Full PDFs remain ignored acquisition masters. Existing reporting,
clinical approval and shared runtime data are never edited by this packager.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as E

from package_cervical_cancer_sources import evidence_stream, restore_jpeg_icc

INVESTIGATION = 'ra.mri-endometrial-cancer'
DATE = '2026-10-11'
# Matched to caption positions, not numeric image-object enumeration order.
MAP2024 = {4:(6,100),5:(6,94),6:(7,109),7:(7,121),8:(8,129),9:(8,135),
           10:(9,144),11:(10,153),12:(10,159),13:(11,168),14:(12,178),
           15:(12,184),16:(13,193),18:(17,222),19:(18,231)}
MAP2025 = {1:(3,14),2:(4,22),3:(4,20),4:(5,28),5:(6,35),6:(6,33),7:(7,41),
           8:(8,49),9:(8,47),10:(9,57),11:(9,55),12:(10,64),13:(10,62),14:(11,70)}
ARTICLES = {
    'PMC11119523':('10.3390/cancers16101869',4,MAP2024),
    'PMC12830431':('10.1007/s00261-025-05058-9',4,MAP2025),
    'PMC13025262':('10.3390/cancers18061005',4,{1:(6,262),2:(7,325)}),
    'PMC7643338':('10.1007/s00261-020-02453-2',4,{2:(12,373),3:(13,389)}),
    'PMC8648287':('10.7759/cureus.19286',3,{4:(5,65),5:(6,76)}),
}
PANELS2024 = {4:'abcde',5:['whole'],6:'abcdef',7:'abcd',8:'abcd',9:'abcdef',
              10:'abcdef',11:'abcdef',12:'abcdef',13:'abcde',14:'abcd',15:'abcd',
              16:'abcd',18:['whole'],19:'abcdef'}
PANELS2025 = {1:'AB',2:'AB',3:'ABC',4:'ABC',5:'AB',6:'AB',7:'AB',8:'ABC',
              9:'AB',10:'AB',11:'ABC',12:'AB',13:'AB',14:'AB'}
TITLES2024 = {4:'Original superficial myometrial invasion example',5:'Original same-wall myometrial depth measurement',
    6:'Original deep myometrial invasion example',7:'Original expansile serous tumour without myometrial invasion',
    8:'Original cervical stromal involvement example',9:'Original carcinosarcoma and upper endocervical extension',
    10:'Original right tube, broad ligament and ovarian spread',11:'Original pelvic sidewall deposit with published molecular result',
    12:'Original bilateral pelvic nodes and cervicovaginal extent',13:'Original bladder, rectosigmoid, distal ureter and hydronephrosis example',
    14:'Original CT abdominal peritoneal spread',15:'Original upper vaginal and peritoneal spread',
    16:'Original pelvic MRI and separate chest CT lung spread',18:'Original normal uterine and cervical T2 zones',
    19:'Original local MRI and fused PET observations'}
TITLES2025 = {1:'Original endometrial polyp without myometrial invasion',2:'Original superficial myometrial invasion',
    3:'Original endometrial and left ovarian case',4:'Original deep myometrial invasion',5:'Original cavity distension with preserved junctional zone',
    6:'Original cervical canal and stromal invasion',7:'Original superficial invasion in carcinosarcoma',8:'Original cervical stroma and right ovary involvement',
    9:'Original myometrial and right adnexal spread',10:'Original serosal involvement',11:'Original Douglas pouch implants',
    12:'Original para-aortic node',13:'Original direct rectal extension',14:'Original MRI abdominal peritoneal implant'}
STRUCTURES2024 = {4:['Endometrium','Myometrium'],5:['Expected endomyometrial interface','Local invaded myometrium','Total same-wall myometrial thickness'],
    6:['Endometrium','Myometrium','Rectum'],7:['Endometrial cavity','Junctional zone'],8:['Myometrium','Endocervical canal','Cervical stroma'],
    9:['Fundal myometrium','Right uterine body','Superior endocervical canal'],10:['Right fallopian tube','Broad ligament','Right ovary'],
    11:['Pelvic sidewall','Left obturator muscle'],12:['Cervical lips','Vaginal fornix','Bilateral iliac nodes'],
    13:['Bladder wall','Rectosigmoid','Vaginal cuff','Ureterovesical junctions','Distal ureters','Renal collecting systems'],
    14:['Abdominal peritoneum','Perihepatic space','Subdiaphragmatic space'],15:['Cervix','Upper vagina','Peritoneal implant','Ascites'],
    16:['Uterus','Lungs on CT'],18:['Endometrium','Junctional zone','Myometrium','Endocervical canal','Cervical stroma','Bladder','Vagina','Rectum'],
    19:['Bladder base','Urethra']}
STRUCTURES2025 = {1:['Endometrial polyp','Myometrium'],2:['Endometrium','Myometrium'],3:['Endometrium','Left ovary','Right ovarian cysts'],
    4:['Myometrium','Junctional zone'],5:['Endometrial cavity','Junctional zone'],6:['Junctional zone','Myometrium','Endocervical canal','Cervical stroma'],
    7:['Superficial myometrium','Peripheral enhancing myometrium'],8:['Endometrial cavity','Cervical stroma','Right ovary'],
    9:['Myometrium','Right adnexa'],10:['Myometrium','Uterine serosa'],11:['Uterine mass','Douglas pouch peritoneum'],
    12:['Para-aortic node'],13:['Myometrium','Serosa','Rectum'],14:['Abdominal peritoneum']}
LIMIT = ('Complete published source views are independent teaching examples, not the current patient, native acquisition arrays, '
    'calibrated measurements, histologically segmented wall layers or registered 3D geometry. Source arrows, scales, ADC/SUV values, '
    'tumour measurements and stage labels remain author annotations. MRI does not establish microscopic LVSI, molecular class, '
    'histologic grade, nodal micro/macrometastasis size or a complete FIGO 2023 stage. No cross-case fitting or every-structure clinical approval is supplied.')


def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(path,value): path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def plain(node): return ' '.join(''.join(node.itertext()).split())
def http(url): return url.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')


def meaning(pmc,n,caption):
    issue=''; extra={}; positions=False
    if pmc=='PMC11119523':
        panels=list(PANELS2024[n]);roles=dict.fromkeys(panels,'CT' if n==14 else 'MRI')
        if n==16:roles.update(c='CT',d='CT')
        if n==19:roles.update(b='Nuclear medicine',c='Nuclear medicine',e='Nuclear medicine',f='Nuclear medicine')
        title=TITLES2024[n];visible=STRUCTURES2024[n]
        same=n not in [5,18];cases={'published_age_specific_single_case':panels} if same else {('measurement_case_identity_not_supplied' if n==5 else 'normal_case_identity_age_cycle_not_supplied'):panels}
        extra['source_staging_framework']='FIGO 2023 discussed by 2024 publication; original source labels retained without recomputing stage'
        if n==11:issue='Original IIIB2POLEmut source glyph is retained. FIGO 2023 modifies stage categories using molecular findings in stages I/II; in stages III/IV molecular class may be recorded with m without changing the anatomic stage category. This particular source glyph formatting is not endorsed as independently verified FIGO notation or reconstructed from MRI. The POLE result is supplied by the publication.'
        if n==12:issue='Original IIIC1ii designation and histologic grade are supplied by the publication. MRI pixels do not verify nodal macro/micrometastasis or grade. Original caption phrase "posterior final fornix" is preserved verbatim.'
        if n==13:issue='The publication describes bladder and rectosigmoid invasion, distal ureter obstruction and hydronephrosis; mucosal certainty, renal function and FIGO stage are not independently established from these bitmaps.'
        if n==15:issue='Original Stage IVB is author-supplied. The local source view depicts a peritoneal implant and ascites; complete peritoneal distribution and staging eligibility are unresolved from these selected views. No current or revised stage is inferred from the bitmap.'
        if n==16:issue='Panels a/b are pelvic MRI; c/d are chest CT. The lungs are not assessed by the selected pelvic MRI observations.'
        if n==18:extra['depicted_state']='published_normal_T2_zonal_anatomy';issue='Normal source age, menopausal/cycle status and acquisition calibration are not supplied; named signal zones are not independent 3D tissue layers.'
        if n==19:
            extra['source_panel_acquisition_modalities']={'a':'sagittal T2 MRI','b':'sagittal PET-CT','c':'sagittal T2-weighted PET-MRI','d':'axial T2 MRI','e':'axial PET-CT','f':'axial T2-weighted PET-MRI'}
            issue='Original caption calls the disease Stage IV without a substage. MRI, PET-CT and fused PET-MRI are distinct observations; source fusion does not supply native acquisition registration or postoperative timing.'
        if n==5:issue='Original green/yellow/red lines illustrate a local same-wall ratio; no source pixel spacing, independently calibrated dimensions or actual current-patient measurement is supplied.'
    elif pmc=='PMC12830431':
        panels=list(PANELS2025[n]);roles=dict.fromkeys(panels,'MRI');title=TITLES2025[n];visible=STRUCTURES2025[n]
        cases={'published_age_specific_single_case':panels};same=True
        extra['source_staging_framework']='FIGO 2023 discussed by publication first online 2025-06-13, issue 2026-01; original labels are supplied clinicopathological context'
        issue='Source stage, histologic type/grade, no-LVSI statements and pathological confirmations are publication-supplied information; they are not inferred from MRI. Source TR/TE, slice thickness and ADC values remain author-reported and do not calibrate this bitmap.'
        if n==3:issue+=' IA3 requires additional clinicopathologic criteria; the two shown organs alone do not establish its complete criteria.'
        if n==9:issue+=' Original caption does not specify the plane of panel A; no plane is invented.'
        if n==13:issue+=' Source describes direct rectal mucosal extension; pixels alone do not certify mucosal invasion.'
    elif pmc=='PMC13025262':
        panels=list('ABCDEFG' if n==1 else 'ABCD');roles=dict.fromkeys(panels,'MRI');same=True
        cases={'published_61_year_single_case' if n==1 else 'published_40_year_single_case':panels}
        title='Original left ovary and right obturator-node case' if n==1 else 'Original early subendometrial enhancement-rim example'
        visible=['Left ovary','Right obturator node','Uterus'] if n==1 else ['Endometrium','Early subendometrial enhancement rim']
        extra['source_staging_framework']='FIGO 2023 discussed by 2026 review; no complete stage assigned by package'
        if n==2:extra['explicit_publication_same_case_figure_links']=[2,4,5]
        issue='Original yellow arrows, star, circle and outline are burned into the complete native source image. PDF white rectangular underlays precede and are fully covered by its opaque image; no visible vector annotation is omitted.'
    elif pmc=='PMC7643338':
        panels=list('abcd' if n==2 else 'abcdef');roles=dict.fromkeys(panels,'MRI');same=False
        cases={p+'_distinct_published_tumour':[p] for p in panels} if n==2 else {'published_apex_endometrioid_case':['a','b'],'published_nodular_mixed_clear_cell_case':['c','d'],'published_lower_vagina_serous_case':['e','f']}
        title='Separate baseline vaginal recurrence appearances' if n==2 else 'Three separate vaginal recurrence and rim-enhancement cases'
        visible=['Vaginal apex','Lower vagina','Periurethral space','Vaginal wall'] if n==2 else ['Vaginal apex','Posterior lower vaginal wall','Tumour peripheral rim','Cystic and necrotic components']
        extra['source_phase']='baseline_vaginal_recurrence_after_primary_treatment';extra['source_staging_framework']='2020 recurrence cohort; pretreatment FIGO 2023 is not assigned'
        issue='Figure2 depicts four separate tumours; Figure3 depicts three separate tumours, with corresponding sequence pairs a/b, c/d and e/f. These are recurrence morphology examples, not serial post-radiotherapy response images.'
        extra['same_case_panel_pairs']=[['a','b'],['c','d'],['e','f']] if n==3 else []
    else:
        panels=list('AB') if n==4 else ['coronal_wholebody','axial_paraaortic','axial_supraclavicular'];positions=n==5
        roles=dict.fromkeys(panels,'CT' if n==4 else 'Nuclear medicine')
        cases={'published_54_year_paraaortic_case':['A'],'published_67_year_lung_case':['B']} if n==4 else {'published_one_year_after_treatment_recurrence_case':panels}
        same=n==5;title='Two separate CT regional-node and distant-lung cases' if n==4 else 'Original post-treatment PET-CT nodal recurrence'
        visible=['Para-aortic nodes on CT','Lungs on CT'] if n==4 else ['Para-aortic node on fused PET-CT','Right supraclavicular node on fused PET-CT']
        extra['source_staging_framework']='FIGO 2009 framework discussed by 2021 publication; source labels not silently restaged to FIGO 2023'
        issue='A and B explicitly depict different patients; all panels are CT, not MRI.' if n==4 else 'One year after chemo-radiotherapy, source PET-CT depicts suspected recurrence. Original source 45 cm scale and SUV 5.52 are retained, not independently calibrated or transferred to MRI.'
        if n==5:extra['source_phase']='one_year_post_chemoradiotherapy_recurrence_suspicion'
    if same:extra['single_case_link_basis']='Original caption explicitly identifies one patient and describes the depicted sequences/modalities of that case.'
    return title,roles,cases,same,visible,issue,extra,positions



def package_esr_pitfall(source,output,evidence):
    """Retain only original Figure5; the complete PDF remains an ignored master."""
    from bs4 import BeautifulSoup
    from PIL import Image
    from pypdf import PdfReader
    import pymupdf
    doi='10.1007/s00330-026-12705-2';url='https://link.springer.com/article/'+doi;pdf_url='https://link.springer.com/content/pdf/'+doi+'.pdf'
    html=(source/'ESR2026-original.html').read_bytes();pdf=(source/'ESR2026-original.pdf').read_bytes();soup=BeautifulSoup(html,'html.parser')
    title=soup.find('meta',attrs={'name':'citation_title'})['content'];authors=[n['content'] for n in soup.find_all('meta',attrs={'name':'citation_author'})]
    if soup.find('meta',attrs={'name':'citation_doi'})['content']!=doi:raise ValueError('ESR DOI differs')
    figure=soup.find(id='Fig5').find_parent('figure');caption=figure.find(id='figure-5-desc').get_text(' ',strip=True)
    if caption!='Common pitfalls in the imaging interpretation of endometrial cancer':raise ValueError('Original ESR Figure5 caption differs')
    grant=soup.find(id='rightslink-content');license_url='https://creativecommons.org/licenses/by/4.0/'
    if 'Creative Commons Attribution 4.0' not in grant.get_text() or 'by-nc' in str(grant) or any(t in figure.get_text().lower() for t in ['reproduced','courtesy','adapted from','reprinted']):raise ValueError('ESR figure commercial grant needs review')
    reader=PdfReader(io.BytesIO(pdf));image=next(i for i in reader.pages[9].images if i.indirect_reference.idnum==112);obj=image.indirect_reference.get_object()
    if obj['/Filter']!='/FlateDecode' or obj['/ColorSpace']!='/DeviceRGB' or obj['/BitsPerComponent']!=8 or any(obj.get(k) is not None for k in ['/Mask','/SMask','/Decode']):raise ValueError('Original ESR image storage differs')
    stream=evidence_stream(evidence,'ESR2026',112,obj);pixels=obj.get_data()
    if len(pixels)!=1750*1220*3:raise ValueError('Native ESR samples differ')
    picture=Image.frombytes('RGB',(1750,1220),pixels);buffer=io.BytesIO();picture.save(buffer,format='PNG');raw=buffer.getvalue()
    view=pymupdf.open(stream=pdf,filetype='pdf');page=view[9];rect=pymupdf.Rect(next(x for x in page.get_image_info(xrefs=True) if x['xref']==112)['bbox'])
    if any(not(pymupdf.Rect(x['rect'])&rect).is_empty for x in page.get_drawings()) or any(rect.contains(pymupdf.Rect(x[:4])) for x in page.get_text('words')):raise ValueError('Source ESR separate vector/text overlay needs preservation')
    issue=('Three source interpretation examples: leiomyomas, adenomyosis and cornual tumour location. Original panel labels identify T2-WI, DWI, ADC and post-contrast T1-WI. '
           'The short source caption supplies no patient identities, age/cycle status or explicit same-case correspondence; no whole-examination or cross-row identity is assumed. '
           'Source text elsewhere labels above-renal-vessel nodes IVB, in conflict with FIGO 2023 primary IVC; this figure contains no stage labels and that prose is not used as criteria.')
    panels=[group+'_'+sequence for group in ['leiomyoma','adenomyosis','cornual'] for sequence in ['T2','DWI','ADC','postcontrast_T1']];roles=dict.fromkeys(panels,'MRI')
    context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'separate_source_local_examples','depicted_state':'published_myometrial_interpretation_pitfalls',
        'selected_panels':panels,'all_source_panels':panels,'panel_types':roles,'panel_identifier_scheme':'descriptive_source_positions',
        'source_case_groups':{p+'_identity_not_supplied':[p] for p in panels},'different_panels_assumed_same_patient':False,'different_figures_assumed_same_patient':False,
        'source_panels_independently_registered':False,'native_acquisition_arrays_included':False,'independent_calibrated_measurements_verified':False,'biological_3d_model_created_from_artwork':False,
        'current_patient_findings':False,'source_scope_issue':issue,'source_staging_framework':'No stage assigned by selected Figure5; source nodal prose conflict held separately'}
    ident='open-endometrial-cancer-esr2026-fig5';filename='endometrial-cancer-esr2026-fig5.png';(output/filename).write_bytes(raw)
    attribution=', '.join(authors)+'. '+title+'. DOI '+doi+'. Figure 5. CC BY 4.0. Complete original PDF samples retained in lossless PNG; no crop, resizing, enhancement or new annotations.'
    row={'id':ident,'kind':'clinical-image','modality':'MRI','figure_number':5,'source_figure_label':'Fig. 5','src':'/app/reference-media/radiology-open/endometrial-cancer/'+filename,
        'sha256':sha(raw),'width':1750,'height':1220,'source_url':url,'figure_url':url+'/figures/5','asset_source_url':pdf_url,
        'caption':'Original leiomyoma, adenomyosis and cornual-location pitfalls. Complete original source figure.','alt':'Original MRI pitfall examples with publication sequence labels and annotations.',
        'source_caption_full':caption,'source_context':context,'image_state':context['depicted_state'],'limits':LIMIT+' '+issue,'structures_visible':['Myometrium','Leiomyomas','Adenomyosis','Cornual endometrial tumour'],
        'clinical_panels':panels,'panel_identifier_scheme':'descriptive_source_positions','license':'CC BY 4.0','license_url':license_url,'attribution':attribution,'rights_reviewed_on':DATE,
        'rights_review':'Original publisher article CC BY4 grant includes images unless a credit states otherwise; Figure5 HTML caption and native PDF image have no restrictive third-party credit. Full PDF remains ignored.'}
    annotation={'source_id':'ESR2026','figure':5,'page':10,'object':112,'image_rect':list(rect),'intersecting_vector_paths':0,'text_over_image':[],
        'white_rectangular_underlays_precede_opaque_image':False,'visible_annotation_master':'original_complete_image_samples','source_vector_or_text_annotation_loss':False}
    evidence_name='ESR2026-figure5-license-and-caption-evidence.json'
    licence={'source_doi':doi,'source_url':url,'source_pdf_url':pdf_url,'original_html_sha256':sha(html),'original_pdf_sha256':sha(pdf),
        'original_HTML_ignored_staging_path':str(source/'ESR2026-original.html'),'original_pdf_ignored_staging_path':str(source/'ESR2026-original.pdf'),
        'selected_figure':'Fig. 5','selected_original_PDF_page':10,'selected_original_image_object':112,'original_publication_date':'2026-07-01','original_citation_authors':authors,
        'original_permissions_text':grant.get_text(' ',strip=True),'original_permissions_HTML_fragment':str(grant),'original_figure_HTML_fragment':str(figure),'source_caption_full':caption,
        'license':'CC BY 4.0','license_url':license_url,'commercial_use':True,'redistribution':True,'selected_figure_has_no_third_party_credit':True,'whole_PDF_redistributed':False,
        'source_nodal_stage_prose_conflict':'Article calls nodes above renal vessels Stage IVB; corrected FIGO2023 primary calls distant nodes above renal vessels IVC. No such label is in selected Figure5.',
        'rights_reviewed_on':DATE,'clinical_approval':False}
    save(evidence/evidence_name,licence)
    article={'source_id':'ESR2026','doi':doi,'title':title,'authors':', '.join(authors),'source_article_url':url,'source_pdf_url':pdf_url,'pdf_sha256':sha(pdf),'pdf_bytes':len(pdf),
        'original_pdf_ignored_staging_path':str(source/'ESR2026-original.pdf'),'license':'CC BY 4.0','license_url':license_url,'license_and_caption_evidence_file':evidence_name,
        'license_and_caption_evidence_sha256':sha((evidence/evidence_name).read_bytes()),'whole_PDF_redistributed':False,'selected_figure_has_no_third_party_credit':True}
    proof={'id':ident,'source_id':'ESR2026','source_figure_id':'Fig5','source_figure_label':'Fig. 5','source_PDF_page':10,
        'source_master':{'kind':'lossless_PNG_of_complete_original_decoded_PDF_samples','source_url':pdf_url,'page':10,'object':112},'original_PDF_streams':[stream],
        'runtime_file':filename,'sha256':sha(raw),'decoded_pixel_sha256':sha(pixels),'width':1750,'height':1220,'pixel_mode':'RGB','source_caption_full':caption,
        'source_panel_types':roles,'source_case_groups':context['source_case_groups'],'annotation_preservation':annotation,'source_pixels_modified':False,
        'complete_original_publication_annotations_retained':True,'source_only_fidelity_review':'pending independent source review','clinical_approval':False}
    return row,proof,article,annotation


def package(source,output,evidence):
    from PIL import Image
    from pypdf import PdfReader
    import pymupdf
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
    from primer import radiology_catalog as catalog
    output.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
    rows=[];proof=[];articles=[];overlay_inventory=[]
    for pmc,(doi,version,figures) in ARTICLES.items():
        meta_raw=(source/(pmc+'-metadata.json')).read_bytes();meta=json.loads(meta_raw)
        xml=(source/(pmc+'-original.xml')).read_bytes();pdf=(source/(pmc+'-original.pdf')).read_bytes()
        if meta['doi']!=doi or meta['license_code']!='CC BY' or meta['is_retracted'] or not meta['is_pmc_openaccess']:raise ValueError('Original commercial grant/version/retraction metadata differs')
        for kind,raw in [('xml',xml),('pdf',pdf)]:
            if hashlib.md5(raw).hexdigest()!=parse_qs(urlparse(meta[kind+'_url']).query)['md5'][0]:raise ValueError('Original publisher MD5 differs')
        tree=E.fromstring(xml);permission=tree.find('.//article-meta/permissions');grant=E.tostring(permission,encoding='unicode');license_url=f'https://creativecommons.org/licenses/by/{version}.0/'
        if license_url not in grant or 'by-nc' in grant:raise ValueError('Original explicit CC BY grant required')
        author=', '.join(' '.join(filter(None,[n.findtext('given-names'),n.findtext('surname')])) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name'))
        reader=PdfReader(io.BytesIO(pdf));view=pymupdf.open(stream=pdf,filetype='pdf')
        article={'pmcid':pmc,'doi':doi,'title':meta['title'],'citation':meta['citation'],'authors':author,'metadata_sha256':sha(meta_raw),'xml_sha256':sha(xml),'pdf_sha256':sha(pdf),'pdf_bytes':len(pdf),
            'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/','source_pdf_url':http(meta['pdf_url']),'source_xml_url':http(meta['xml_url']),
            'original_pdf_ignored_staging_path':str(source/(pmc+'-original.pdf')),'publisher_XML_PDF_MD5_verified':True,'license':f'CC BY {version}.0','license_url':license_url,
            'original_permissions_xml':grant,'is_retracted':False,'whole_PDF_redistributed':False}
        articles.append(article);(evidence/(pmc+'-original.xml')).write_bytes(xml);(evidence/(pmc+'-original-metadata.json')).write_bytes(meta_raw)
        for number,(page,oid) in figures.items():
            fig=next(f for f in tree.findall('.//fig') if re.search(r'\b'+str(number)+r'\s*$',f.findtext('label','')));caption=plain(fig.find('caption'))
            if fig.find('attrib') is not None or fig.find('permissions') is not None or any(t in caption.lower() for t in ['reprinted','reproduced','courtesy','adapted from']):raise ValueError('Figure-specific rights review required')
            image=next(i for i in reader.pages[page-1].images if i.indirect_reference.idnum==oid);obj=image.indirect_reference.get_object()
            if any(obj.get(k) is not None for k in ['/Mask','/SMask','/Decode']) or obj['/BitsPerComponent']!=8:raise ValueError('Unreviewed native source mask/decode')
            stream=evidence_stream(evidence,pmc,oid,obj);profile=stream.get('original_ICC');icc=(evidence/profile['file']).read_bytes() if profile else None
            if str(obj['/Filter'])=='/DCTDecode':
                raw=obj._data;ext='.jpg'
                if icc:raw=restore_jpeg_icc(raw,icc)
            elif str(obj['/Filter'])=='/FlateDecode':
                pixels=obj.get_data();w=int(obj['/Width']);h=int(obj['/Height'])
                if len(pixels)!=w*h*3:raise ValueError('Unreviewed native PDF color/storage')
                picture=Image.frombytes('RGB',(w,h),pixels);b=io.BytesIO();picture.save(b,format='PNG',**({'icc_profile':icc} if icc else {}));raw=b.getvalue();ext='.png'
            else:raise ValueError('Unsupported native source codec')
            picture=Image.open(io.BytesIO(raw));picture.load()
            if picture.mode not in ['L','RGB'] or (icc and picture.info.get('icc_profile')!=icc):raise ValueError('Native samples/profile readback differs')
            placed=next(x for x in view[page-1].get_image_info(xrefs=True) if x['xref']==oid);rect=pymupdf.Rect(placed['bbox']);drawings=[x for x in view[page-1].get_drawings() if not (pymupdf.Rect(x['rect'])&rect).is_empty]
            text_overlay=[x[4] for x in view[page-1].get_text('words') if rect.contains(pymupdf.Rect(x[:4]))]
            image_sequence=next(i for i,(kind,bbox) in enumerate(view[page-1].get_bboxlog()) if kind=='fill-image' and all(abs(a-b)<0.001 for a,b in zip(bbox,rect)))
            underlay=bool(drawings) and all(x['type']=='f' and x['fill']==(1.,1.,1.) and x['seqno']<image_sequence and len(x['items'])==1 and x['items'][0][0]=='re' and (pymupdf.Rect(x['rect'])+(-0.001,-0.001,0.001,0.001)).contains(rect) for x in drawings)
            if (drawings and not underlay) or text_overlay:raise ValueError(f'Visible source vector/text annotations need a complete publisher master: {pmc} {number}, vectors={len(drawings)}, text={text_overlay}')
            annotation={'pmcid':pmc,'figure':number,'page':page,'object':oid,'image_rect':list(rect),'intersecting_vector_paths':len(drawings),'text_over_image':text_overlay,'white_rectangular_underlays_precede_opaque_image':underlay,
                        'visible_annotation_master':'original_complete_image_samples','source_vector_or_text_annotation_loss':False}
            overlay_inventory.append(annotation)
            title,roles,cases,same,visible,issue,extra,positions=meaning(pmc,number,caption);primary='CT' if set(roles.values())=={'CT'} else 'Nuclear medicine' if set(roles.values())=={'Nuclear medicine'} else 'MRI';selected=[p for p,r in roles.items() if r==primary]
            context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'source_local_views','depicted_state':'published_independent_endometrial_or_recurrence_examples',
                'selected_panels':selected,'all_source_panels':list(roles),'panel_types':roles,'source_case_groups':cases,'different_panels_assumed_same_patient':same,'different_figures_assumed_same_patient':False,
                'source_panels_independently_registered':False,'native_acquisition_arrays_included':False,'independent_calibrated_measurements_verified':False,'biological_3d_model_created_from_artwork':False,
                'current_patient_findings':False,'source_scope_issue':issue,**extra}
            name='endometrial-cancer-'+pmc.lower()+'-fig'+str(number)+ext;ident='open-endometrial-cancer-'+pmc.lower()+'-fig'+str(number);(output/name).write_bytes(raw)
            storage='Original JPEG image encoding and decoded samples retained; original external PDF ICC restored in APP2 metadata only' if icc and ext=='.jpg' else 'Original JPEG bytes retained' if ext=='.jpg' else 'Original complete decoded PDF samples retained in lossless PNG with original ICC'
            attribution=f'{author}. {meta["title"]}. DOI {doi}. Figure {number}. CC BY {version}.0. {storage}; no crop, resizing, enhancement or new annotations.'
            row={'id':ident,'kind':'clinical-image','modality':primary,'figure_number':number,'source_figure_label':fig.findtext('label'),'src':'/app/reference-media/radiology-open/endometrial-cancer/'+name,
                'sha256':sha(raw),'width':picture.width,'height':picture.height,'source_url':article['source_article_url'],'figure_url':article['source_article_url']+'#'+fig.get('id'),
                'asset_source_url':article['source_pdf_url'],'caption':title+'. Complete original source figure.','alt':title+'; complete original publication annotations retained.',
                'source_caption_full':caption,'source_context':context,'image_state':context['depicted_state'],'limits':LIMIT+' '+issue,'structures_visible':visible,'clinical_panels':selected,
                'license':f'CC BY {version}.0','license_url':license_url,'attribution':attribution,'rights_reviewed_on':DATE,
                'rights_review':'Original article XML CC BY grant and complete selected figure caption/credits reviewed; no restrictive figure-specific exception found. Source case, modality and phase limits retained.'}
            if positions:row['panel_identifier_scheme']='descriptive_source_positions';context['panel_identifier_scheme']='descriptive_source_positions'
            ancillary=[]
            for role in sorted(set(roles.values())-{primary}):ancillary.append({'kind':role,'panels':[p for p,r in roles.items() if r==role],'structures_visible':['Separate original '+role+' source observations'],'limits':'Separate original '+role+' observations do not constitute MRI or independently registered acquisitions.'})
            if ancillary:row['ancillary_panels']=ancillary
            catalog._validate_source_panel_roles(row);rows.append(row)
            proof.append({'id':ident,'pmcid':pmc,'source_figure_id':fig.get('id'),'source_figure_label':fig.findtext('label'),'source_PDF_page':page,
                'source_master':{'kind':'complete_original_PDF_JPEG_with_restored_original_ICC_metadata' if icc and ext=='.jpg' else 'complete_original_PDF_JPEG' if ext=='.jpg' else 'lossless_PNG_of_complete_original_decoded_PDF_samples','source_url':article['source_pdf_url'],'page':page,'object':oid},
                'original_PDF_streams':[stream],'runtime_file':name,'sha256':sha(raw),'decoded_pixel_sha256':sha(picture.tobytes()),'width':picture.width,'height':picture.height,'pixel_mode':picture.mode,
                'source_caption_full':caption,'source_panel_types':roles,'source_case_groups':cases,'annotation_preservation':annotation,'source_pixels_modified':False,
                'complete_original_publication_annotations_retained':True,'source_only_fidelity_review':'pending independent source review','clinical_approval':False})
    row,record,article,annotation=package_esr_pitfall(source,output,evidence)
    catalog._validate_source_panel_roles(row);rows.append(row);proof.append(record);articles.append(article);overlay_inventory.append(annotation)
    published={'schema_version':1,'investigation_id':INVESTIGATION,'articles':articles,'figures':proof,'figure_count':len(proof),'runtime_total_bytes':sum((output/p['runtime_file']).stat().st_size for p in proof),
        'source_pixels_modified':False,'clinical_approval':False,'complete_reporting_anatomy_approved':False,'every_structure_approved':False,'fine_3D_tissue_layers_supplied':False,
        'native_acquisition_arrays_included':False,'patient_calibration_or_lesion_registration_verified':False}
    save(evidence/'published-source-preservation.json',published);save(evidence/'source-figure-contract.json',{'investigation_id':INVESTIGATION,'structure_atlas':rows,'registration_or_coverage_applied':False,'clinical_approval':False})
    save(evidence/'original-pdf-annotation-inventory.json',overlay_inventory)
    (output/'ATTRIBUTION.md').write_text('# Original endometrial cancer source figures\n\n'+'\n\n'.join(row['attribution'] for row in rows)+'\n\n'+LIMIT+'\n')
    print(json.dumps({'figures':len(proof),'runtime_total_bytes':published['runtime_total_bytes'],'contract':str(evidence/'source-figure-contract.json'),'clinical_approval':False}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--review-output',type=Path,required=True)
    a=p.parse_args();package(a.source_root,a.output,a.review_output)
