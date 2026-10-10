#!/usr/bin/env python3
"""Retain original licensed cervical MRI/diagram figures and source-only contracts.

Writes only the new source package/evidence directories. It does not change
reporting content, coverage, asset approval or any existing shared data file.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import struct
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as E


INVESTIGATION = 'ra.mri-cervical-cancer'
CCBY = 'https://creativecommons.org/licenses/by/4.0/'
BOOK_DOI = '10.1007/978-3-319-75019-4_3'
BOOK_PDF = 'https://link.springer.com/content/pdf/' + BOOK_DOI + '.pdf'
BOOK_CAPTION = ('Normal MRI Uterine Anatomy Sagittal 3D T2-weighted multiplanar reconstruction of the uterus and cervix demonstrates normal zonal anatomy. '
                'There are three zones identifiable in the uterus: the hyperintense endometrium, the hypointense junctional zone and the intermediate signal intensity of the outer myometrium. '
                'Four zones are distinguished in the cervix: the hyperintense mucous within the endocervical canal, the intermediate signal intensity of the cervical mucosa, '
                'the hypointense cervical stroma, and the intermediate signal intensity of the outer smooth muscle')
# Original PDF page and complete image object, reviewed against numbered captions.
MRI2023 = {1:(4,77),2:(5,97),3:(8,133),4:(8,150),5:(8,151),6:(9,189),
           7:(10,209),8:(10,210),9:(11,248),10:(11,249),11:(12,288),12:(12,289),
           13:(13,327),14:(15,350),15:(15,351),16:(15,352),17:(16,410),18:(17,436)}
GUIDE2024 = {1:(9,103),2:(10,123),3:(11,149),4:(15,190),6:(18,245),8:(20,297),10:(22,356),11:(23,376)}
VARIANTS2020 = {3:(6,48),4:(7,61),6:(9,101)}
ARTICLES = {'PMC10605640':('10.3390/cancers15205105',MRI2023),
            'PMC10886638':('10.3390/cancers16040775',GUIDE2024),
            'PMC11171278':('10.3390/cancers16111983',{1:None,2:None}),
            'PMC7338830':('10.1007/s00330-020-06750-8',VARIANTS2020)}
TITLES2023 = {
    1:'Original cervical plane planning',2:'Original metastatic-node morphology examples',
    3:'Original small anterior-lip tumour with DWI and ADC',4:'Original endocervical tumour and preserved stromal ring',
    5:'Original posterior-lip tumour and vaginal-wall relationship',6:'Original lower-segment and bilateral parametrial extension',
    7:'Original lower-vaginal and uterine-body extension',8:'Original parametrial extension and left hydroureter',
    9:'Original left obturator-node example',10:'Original para-aortic nodes and right hydronephrosis',
    11:'Separate source bullous-oedema and bladder-invasion cases',12:'Original acetabular and sacral bone-metastasis example',
    13:'Original tumour-to-internal-os relationship',14:'Original appropriately positioned brachytherapy devices',
    15:'Original malpositioned brachytherapy applicator',16:'Original parametrial needle and sigmoid-perforation example',
    17:'Original baseline and post-chemoradiotherapy response',18:'Original baseline, post-treatment fibrosis and later rectal recurrence',
}
PANELS2023 = {1:'ab',2:'ab',3:'abc',4:'ab',5:'ab',6:'ab',7:'whole',8:'whole',9:'whole',10:'whole',
              11:'abc',12:'abc',13:'whole',14:'ab',15:'ab',16:'ab',17:'abc',18:'abcd'}
TITLES2024 = {1:'Original multimodal rectal/sigmoid and parametrial case',
              2:'Original conceptual pelvic ultrasound approaches',
              3:'Original multimodal vaginal and parametrial case',
              4:'Separate source cervical-remnant and fertility-planning cases',
              6:'Original multimodal bladder and rectosigmoid case',
              8:'Original conceptual pelvic, abdominal and distant nodal approaches',
              10:'Original right uterosacral/pararectal-node case',
              11:'Original parametrial and vaginal MRI/PET-MRI case'}
ROLES2024 = {
    1:{'a':'Ultrasound','b':'MRI','c':'CT','d':'Ultrasound','e':'MRI','f':'CT','g':'Ultrasound','h':'MRI','i':'MRI','j':'PET-CT'},
    2:dict.fromkeys('abc','Schematic'),3:{**dict.fromkeys('abc','Ultrasound'),**dict.fromkeys('def','MRI')},
    4:{'a':'Ultrasound','b':'MRI','c':'Ultrasound','d':'MRI'},
    6:{'a':'Ultrasound','b':'MRI','c':'Ultrasound','d':'CT'},8:dict.fromkeys('abcde','Schematic'),
    10:{'a':'Ultrasound','b':'PET-CT','c':'MRI','d':'MRI'},
    11:{'a':'MRI','b':'MRI','c':'Nuclear medicine','d':'MRI','e':'Nuclear medicine'},
}
CASES2024 = {1:{'published_48_year_case_Fig1_Fig10':list('abcdefghij')},2:{},
             3:{'published_57_year_case':list('abcdef')},
             4:{'published_59_year_cervical_remnant_case':['a','b'],'published_28_year_fertility_case':['c','d']},
             6:{'published_38_year_case_Fig6_Fig7':list('abcd')},8:{},
             10:{'published_48_year_case_Fig1_Fig10':list('abcd')},
             11:{'published_40_year_case':list('abcde')}}
LIMIT = ('Complete published source views are independent teaching examples, not the current patient, native acquisition arrays, calibrated measurements, '
         'histologically verified tissue-layer segmentations or a registered 3D model. Source arrows, circles, measurements and stage labels remain author annotations. '
         'No automatic FIGO stage, microscopic IA assignment, mucosal certainty, cross-case fitting or every-structure clinical approval is supplied.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def text(node):
    return ' '.join(''.join(node.itertext()).split())


def http(url):
    return url.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')


def restore_jpeg_icc(raw,profile):
    """Insert only ICC APP2 metadata; never re-encode JPEG image/entropy data."""
    from PIL import Image
    if raw[:2]!=b'\xff\xd8':raise ValueError('Original JPEG SOI missing')
    existing=Image.open(io.BytesIO(raw)).info.get('icc_profile')
    if existing is not None:
        if existing!=profile:raise ValueError('Original embedded/PDF ICC profiles differ')
        return raw
    chunks=[profile[i:i+65519] for i in range(0,len(profile),65519)]
    if not chunks or len(chunks)>255:raise ValueError('Unsupported original ICC profile extent')
    metadata=b''.join(b'\xff\xe2'+struct.pack('>H',16+len(chunk))+b'ICC_PROFILE\0'
                      +bytes([i+1,len(chunks)])+chunk for i,chunk in enumerate(chunks))
    # Keep the original JFIF/EXIF/application prefix order intact.
    position=2
    while raw[position:position+1]==b'\xff' and 0xe0<=raw[position+1]<=0xef:
        length=struct.unpack_from('>H',raw,position+2)[0]
        if length<2 or position+2+length>len(raw):raise ValueError('Original JPEG application marker truncated')
        position+=2+length
    tagged=raw[:position]+metadata+raw[position:]
    if Image.open(io.BytesIO(tagged)).info.get('icc_profile')!=profile:
        raise ValueError('Restored original ICC metadata readback differs')
    return tagged


def evidence_stream(output,pmc,oid,obj):
    """Keep original encoded PDF samples, filter/decode descriptors and ICC."""
    from pypdf.generic import IndirectObject
    def descriptor(value):
        if isinstance(value,IndirectObject):
            return {'original_object':value.idnum,'generation':value.generation}
        if isinstance(value,(list,tuple)):
            return [descriptor(x) for x in value]
        if isinstance(value,dict):
            return {str(k):descriptor(v) for k,v in value.items()}
        if value is None or isinstance(value,(int,float,bool)):
            return value
        return str(value)
    directory=output/'original-pdf-image-streams';directory.mkdir(exist_ok=True)
    filename=pmc+'-object'+str(oid)+'.bin.gz'
    encoded=gzip.compress(obj._data,mtime=0);(directory/filename).write_bytes(encoded)
    result={'original_object':oid,'file':'original-pdf-image-streams/'+filename,
            'sha256':sha(encoded),'encoded_source_stream_sha256':sha(obj._data),
            'encoded_source_stream_bytes':len(obj._data),
            'width':int(obj['/Width']),'height':int(obj['/Height']),
            'filter':str(obj['/Filter']),'bits_per_component':int(obj['/BitsPerComponent']),
            'color_space':descriptor(obj['/ColorSpace']),
            'decode':descriptor(obj.get('/Decode')),'decode_parms':descriptor(obj.get('/DecodeParms'))}
    color=obj['/ColorSpace']
    if isinstance(color,list) and str(color[0])=='/ICCBased':
        profile=color[1].get_object();data=profile.get_data()
        name=pmc+'-icc-object'+str(color[1].idnum)+'.icc'
        (directory/name).write_bytes(data)
        result['original_ICC']={'file':'original-pdf-image-streams/'+name,'sha256':sha(data),
                                'channels':int(profile['/N']),'alternative':str(profile.get('/Alternate'))}
    return result


def package(source,output,evidence):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    root=Path(__file__).resolve().parents[2]
    from primer import radiology_catalog as catalog
    output.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
    rows=[];proof=[];articles=[]
    for pmc,(doi,figures) in ARTICLES.items():
        meta_raw=(source/(pmc+'-metadata.json')).read_bytes();meta=json.loads(meta_raw)
        xml=(source/(pmc+'-original.xml')).read_bytes();pdf=(source/(pmc+'-original.pdf')).read_bytes()
        if meta['doi']!=doi or meta['license_code']!='CC BY' or meta['is_retracted'] or not meta['is_pmc_openaccess']:
            raise ValueError('Original commercial grant/version/retraction metadata differs')
        for kind,raw in [('xml',xml),('pdf',pdf)]:
            if hashlib.md5(raw).hexdigest()!=parse_qs(urlparse(meta[kind+'_url']).query)['md5'][0]:
                raise ValueError('Original publisher MD5 differs')
        tree=E.fromstring(xml);permission=tree.find('.//article-meta/permissions')
        grant=E.tostring(permission,encoding='unicode')
        if CCBY not in grant or 'by-nc' in grant:
            raise ValueError('Original explicit CC BY4 grant required')
        author=', '.join(' '.join(filter(None,[n.findtext('given-names'),n.findtext('surname')]))
                        for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name'))
        reader=PdfReader(io.BytesIO(pdf))
        article={'pmcid':pmc,'doi':doi,'title':meta['title'],'citation':meta['citation'],'authors':author,
                 'metadata_sha256':sha(meta_raw),'xml_sha256':sha(xml),'pdf_sha256':sha(pdf),
                 'pdf_bytes':len(pdf),'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/',
                 'source_pdf_url':http(meta['pdf_url']),'source_xml_url':http(meta['xml_url']),
                 'original_pdf_ignored_staging_path':str(source/(pmc+'-original.pdf')),
                 'publisher_XML_PDF_MD5_verified':True,'license':'CC BY 4.0','license_url':CCBY,
                 'original_permissions_xml':grant,'is_retracted':False}
        articles.append(article)
        (evidence/(pmc+'-original.xml')).write_bytes(xml)
        (evidence/(pmc+'-original-metadata.json')).write_bytes(meta_raw)
        for number,mapping in figures.items():
            fig=next(f for f in tree.findall('.//fig') if re.search(r'\b'+str(number)+r'\s*$',f.findtext('label','')))
            caption=text(fig.find('caption'))
            if fig.find('attrib') is not None or fig.find('permissions') is not None or any(token in caption.lower() for token in ['reprinted','reproduced','courtesy','adapted from']):
                raise ValueError('Figure-specific rights review is required')
            streams=[];source_master={}
            if mapping is None:
                # Keep the complete original publisher bitmap. Figure2 adds
                # arrows as PDF vectors; Figure1's circles are already burned in.
                media=next(u for u in meta['media_urls'] if '-g'+str(number).zfill(3)+'.jpg' in u)
                master=source/(pmc+'-figure'+str(number)+'.jpg');raw=master.read_bytes()
                if hashlib.md5(raw).hexdigest()!=parse_qs(urlparse(media).query)['md5'][0]:
                    raise ValueError('Complete original annotated source bitmap differs')
                page=2 if number==1 else 3
                object_ids=[88] if number==1 else [125,126]
                for oid in object_ids:
                    streams.append(evidence_stream(evidence,pmc,oid,reader.get_object(IndirectObject(oid,0,reader))))
                source_master={'kind':'complete_original_publisher_annotated_JPEG','source_url':http(media),
                               'publisher_md5':hashlib.md5(raw).hexdigest(),
                               'reason':('Complete original publisher bitmap retains the source circles and panel letters at795x660, compared with the complete annotated PDF image at767x637. Figure1 has no separate PDF vector overlay.' if number==1 else
                                         'Original publisher bitmap preserves seven vector arrows that are separate objects in the PDF. Bare PDF image objects125/126 omit those annotations and are not substituted.')}
                ext='.jpg'
            else:
                page,oid=mapping;image=next(i for i in reader.pages[page-1].images if i.indirect_reference.idnum==oid)
                obj=image.indirect_reference.get_object()
                if obj.get('/Mask') is not None or obj.get('/SMask') is not None or obj.get('/Decode') is not None or obj['/BitsPerComponent']!=8:
                    raise ValueError('Unreviewed mask/decode source image')
                streams.append(evidence_stream(evidence,pmc,oid,obj))
                if str(obj['/Filter'])=='/DCTDecode':
                    raw=obj._data;ext='.jpg'
                    profile=streams[-1].get('original_ICC')
                    if profile:raw=restore_jpeg_icc(raw,(evidence/profile['file']).read_bytes())
                elif str(obj['/Filter'])=='/FlateDecode':
                    pixels=obj.get_data();width=int(obj['/Width']);height=int(obj['/Height'])
                    if len(pixels)!=width*height*3:
                        raise ValueError('Source PDF samples require separate color/storage review')
                    picture=Image.frombytes('RGB',(width,height),pixels);buffer=io.BytesIO()
                    profile=streams[-1].get('original_ICC')
                    picture.save(buffer,format='PNG',**({'icc_profile':(evidence/profile['file']).read_bytes()} if profile else {}))
                    raw=buffer.getvalue();ext='.png'
                else:
                    raise ValueError('Unsupported native source codec')
                source_master={'kind':('complete_original_PDF_JPEG_with_restored_original_ICC_metadata' if streams[-1].get('original_ICC') else 'complete_original_PDF_image_stream') if ext=='.jpg' else 'lossless_PNG_of_complete_original_decoded_PDF_samples',
                               'source_url':article['source_pdf_url'],'page':page,'object':oid}
            picture=Image.open(io.BytesIO(raw));picture.load();pixels=picture.tobytes()
            if picture.mode not in ['L','RGB']:
                raise ValueError('Unreviewed source colorspace conversion')
            filename='cervical-cancer-'+pmc.lower()+'-fig'+str(number)+ext
            (output/filename).write_bytes(raw)
            ident='open-cervical-cancer-'+pmc.lower()+'-fig'+str(number)
            if pmc=='PMC10605640':
                panels=['whole'] if PANELS2023[number]=='whole' else list(PANELS2023[number])
                roles=dict.fromkeys(panels,'MRI');title=TITLES2023[number]
                cases=({'different_source_patient_a':['a'],'different_source_patient_bc':['b','c']} if number==11 else
                       {'case_identity_unspecified_a':['a'],'case_identity_unspecified_b':['b']} if number==2 else
                       {'published_figure_case_identity_not_supplied':panels})
            elif pmc=='PMC10886638':
                roles=ROLES2024[number];title=TITLES2024[number];cases=CASES2024[number]
            elif pmc=='PMC11171278':
                roles=dict.fromkeys('ABCD' if number==1 else 'ABCDE','MRI')
                title='Original annotated normal cervical, parametrial and sidewall T2 appearances' if number==1 else 'Original stromal, parametrial, vaginal and bladder-wall MRI comparison'
                cases={'published_normal_appearance_group_identity_not_supplied':list(roles)} if number==1 else {p+'_case_identity_not_supplied':[p] for p in roles}
            else:
                roles=dict.fromkeys({3:'ab',4:'abcd',6:'abcd'}[number],'MRI')
                title={3:'Original non-obstructing vaginal septum',4:'Original dedicated-plane comparison in a septate uterus',6:'Original didelphys, obstructed hemivagina and renal agenesis'}[number]
                cases={'published_anomaly_case_identity_not_supplied':list(roles)}
            schematic=set(roles.values())=={'Schematic'};primary='Schematic' if schematic else 'MRI'
            selected=[p for p,r in roles.items() if r==primary]
            context={'setting':'conceptual' if schematic else 'in_vivo','laterality':'not_reported',
                     'population':{'life_stage':'not_reported'},'extent':'source_local_views',
                     'depicted_state':'conceptual_source_anatomical_or_probe_relationships' if schematic else 'published_cervical_or_related_anatomy_case_examples',
                     'selected_panels':selected,'all_source_panels':list(roles),'panel_types':roles,'source_case_groups':cases,
                     'different_panels_assumed_same_patient':False,
                     'different_figures_assumed_same_patient':False,'source_panels_independently_registered':False,
                     'native_acquisition_arrays_included':False,'independent_calibrated_measurements_verified':False,
                     'biological_3d_model_created_from_artwork':False,'current_patient_findings':False}
            issue=''
            if pmc=='PMC10605640':
                context['different_panels_assumed_same_patient']=number in [3,4,18]
                if number in [3,4,18]:
                    context['single_case_link_basis']='Original caption explicitly links corresponding sequences, a plane through the same mass, or the same patient across timepoints.'
                context['source_staging_framework']='FIGO 2018 revision discussed by the 2023 publication; original stage labels retained, not recomputed'
                if number in [14,15,16]:
                    context['source_phase']='during_brachytherapy';issue='Source procedure/device example; not a pretreatment staging finding.'
                if number==17:context['source_timepoint_groups']={'baseline':['a'],'after_chemoradiotherapy':['b','c']}
                if number==18:context['source_timepoint_groups']={'initial_staging':['a'],'6_month_post_treatment':['b'],'later_symptomatic_recurrence':['c','d']}
                if number==11:issue='Panel a and panels b/c are explicitly different patients. Bullous oedema does not become mucosal invasion.'
                if number==8:issue='Source caption labels FIGO IIIB and shows hydroureter; renal obstruction/function and stage are not independently inferred from this bitmap.'
            if pmc=='PMC10886638':
                context['different_panels_assumed_same_patient']=number in [1,3,6,10,11]
                if context['different_panels_assumed_same_patient']:
                    context['single_case_link_basis']='Original caption identifies one age-specific patient and explicitly describes the depicted modalities/views of that case.'
                if number in [1,10]:context['explicit_publication_same_case_figure_links']=[1,10]
                if number==6:context['explicit_publication_same_case_figure_links']=[6,7]
                if number==4:issue='Two different patients: a/b cervical remnant after hysterectomy; c/d fertility-planning case. Source T1b1 terminology beside a 3 cm tumour is retained without silently assigning a new FIGO stage.'
                if number==11:
                    context['source_panel_acquisition_modalities']={'a':'T2-weighted MRI','b':'DWI','c':'fused PET-MRI','d':'T2-weighted MRI','e':'fused PET-MRI'}
                    issue='Original caption calls one sagittal fused view PET-CT although the figure title/panel description says PET-MRI. Preserve this wording discrepancy; c/e remain separate nuclear-medicine fused observations.'
            if pmc=='PMC11171278':
                context['depicted_state']='published_normal_T2_appearance_with_author_annotations' if number==1 else 'separate_source_local_MRI_appearance_examples'
                issue=('Original source circles and panel letters are preserved in the complete publisher JPEG; they are already burned into the lower-resolution PDF image.' if number==1 else
                       'Original source arrows and panel letters are preserved in the complete publisher JPEG; bare PDF image extraction would lose seven vector arrows.')
                issue+=' No source patient matching or fine layer segmentation is inferred.'
            if pmc=='PMC7338830':
                issue='Separate congenital-anomaly source; this is not cervical cancer or a current-patient anatomical variant.'
                if number==4:
                    context['different_panels_assumed_same_patient']=True
                    context['single_case_link_basis']='Original caption explicitly states the same patient and same MRI scanner, with two examinations days apart.'
                    context['source_timepoint_groups']={'first_examination':['b','d'],'recalled_dedicated_examination':['a','c']}
            if issue:context['source_scope_issue']=issue
            storage=('JPEG image encoding and decoded samples; original PDF ICC profile restored in APP2 metadata only' if source_master['kind']=='complete_original_PDF_JPEG_with_restored_original_ICC_metadata' else
                     'publisher JPEG bytes' if mapping is None else 'JPEG stream' if ext=='.jpg' else 'decoded PDF samples in a lossless PNG with original ICC profile')
            attribution=author+'. '+meta['title']+'. DOI '+doi+'. Figure '+str(number)+'. CC BY 4.0. Complete original '+storage+' retained; no crop, resizing, enhancement or new annotations.'
            row={'id':ident,'kind':'schematic' if schematic else 'clinical-image','modality':primary,'figure_number':number,
                 'source_figure_label':fig.findtext('label'),'src':'/app/reference-media/radiology-open/cervical-cancer/'+filename,
                 'sha256':sha(raw),'width':picture.width,'height':picture.height,
                 'source_url':article['source_article_url'],'figure_url':article['source_article_url']+'#'+fig.get('id'),
                 'asset_source_url':source_master['source_url'],'caption':title+'. Complete original source figure.',
                 'alt':title+'; original publication annotations retained.','source_caption_full':caption,
                 'source_context':context,'image_state':context['depicted_state'],'limits':LIMIT+' '+issue,
                 'structures_visible':['Source-local labelled structures and relationships in the original caption; complete structure accuracy remains unapproved'],
                 'license':'CC BY 4.0','license_url':CCBY,'attribution':attribution,'rights_reviewed_on':'2026-10-10',
                 'rights_review':'Original article XML CC BY4 grant and complete figure credits reviewed; no restrictive figure-specific exception found. Source case, role and phase limits retained.'}
            row['schematic_panels' if schematic else 'clinical_panels']=selected
            if schematic:
                row['schematic_structures_visible']=row['structures_visible'];row['schematic_limits']=row['limits']
            ancillary=[]
            for role in sorted(set(roles.values())-{primary}):
                ancillary.append({'kind':role,'panels':[p for p,r in roles.items() if r==role],
                                  'structures_visible':['Separate original '+role+' observations'],
                                  'limits':'Source '+role+' panels are separate from the selected MRI observations; no acquisition registration or current findings inferred.'})
            if ancillary:row['ancillary_panels']=ancillary
            catalog._validate_source_panel_roles(row)
            rows.append(row)
            proof.append({'id':ident,'pmcid':pmc,'source_figure_id':fig.get('id'),'source_figure_label':fig.findtext('label'),
                          'source_PDF_page':page,'source_master':source_master,'original_PDF_streams':streams,
                          'runtime_file':filename,'sha256':sha(raw),'decoded_pixel_sha256':sha(pixels),
                          'width':picture.width,'height':picture.height,'pixel_mode':picture.mode,
                          'source_caption_full':caption,'source_panel_types':roles,'source_case_groups':cases,
                          'source_pixels_modified':False,'complete_original_publication_annotations_retained':True,
                          'source_only_fidelity_review':'pending visual verification','clinical_approval':False})
    # Keep the full chapter ignored: its externally credited Figure3.2 has a
    # conflicting noncommercial primary grant. Retain only approved image7.
    book_raw=(source/'candidate-0.pdf').read_bytes();reader=PdfReader(io.BytesIO(book_raw))
    book_text='\n'.join(p.extract_text() for p in reader.pages)
    if 'Creative Commons Attribution 4.0' not in book_text or 'The images or other third party material' not in book_text:
        raise ValueError('Original chapter/figure grant missing')
    image=next(i for i in reader.pages[1].images if i.indirect_reference.idnum==7);obj=image.indirect_reference.get_object()
    if str(obj['/Filter'])!='/DCTDecode' or obj.get('/Decode') is not None or obj.get('/SMask') is not None:
        raise ValueError('Normal MRI native source codec differs')
    book_stream=evidence_stream(evidence,'normal-uterus-2018',7,obj)
    raw=obj._data
    if book_stream.get('original_ICC'):
        raw=restore_jpeg_icc(raw,(evidence/book_stream['original_ICC']['file']).read_bytes())
    picture=Image.open(io.BytesIO(raw));picture.load()
    filename='cervical-cancer-normal-uterus-2018-fig3-1.jpg';(output/filename).write_bytes(raw)
    ident='open-cervical-cancer-normal-uterus-2018-fig3-1'
    context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},
             'extent':'single_source_local_MPR','depicted_state':'published_normal_uterine_and_cervical_zonal_anatomy',
             'selected_panels':['whole'],'all_source_panels':['whole'],'panel_types':{'whole':'MRI'},
             'source_case_groups':{'normal_case_identity_and_age_not_supplied':['whole']},
             'different_panels_assumed_same_patient':False,'different_figures_assumed_same_patient':False,
             'source_panels_independently_registered':False,'native_acquisition_arrays_included':False,
             'independent_calibrated_measurements_verified':False,'biological_3d_model_created_from_artwork':False,
             'source_scope_issue':'Source caption describes a sagittal reconstruction from a 3D T2 acquisition. Only this published 2D bitmap is included; no 3D acquisition or histological geometry is supplied.'}
    credit='Karen Kinkel, Susan M. Ascher and Caroline Reinhold. Benign Disease of the Uterus (2018), DOI '+BOOK_DOI+'. Figure 3.1. Original JPEG image encoding and decoded samples retained; original PDF ICC profile restored in APP2 metadata only. CC BY 4.0.'
    row={'id':ident,'kind':'clinical-image','modality':'MRI','figure_number':'3.1','source_figure_label':'Fig. 3.1',
         'src':'/app/reference-media/radiology-open/cervical-cancer/'+filename,'sha256':sha(raw),'width':picture.width,'height':picture.height,
         'source_url':'https://link.springer.com/chapter/'+BOOK_DOI,'figure_url':'https://link.springer.com/chapter/'+BOOK_DOI+'#Fig1',
         'asset_source_url':BOOK_PDF,'caption':'Original normal uterine and cervical T2 zonal anatomy · source Figure 3.1.',
         'alt':'Complete original sagittal normal uterine and cervical T2 source image.','source_caption_full':BOOK_CAPTION,
         'clinical_panels':['whole'],'source_context':context,'image_state':context['depicted_state'],'limits':LIMIT+' '+context['source_scope_issue'],
         'structures_visible':['Source uterine endometrium, junctional zone, outer myometrium; source cervical canal/mucosa, stroma and outer smooth-muscle appearances'],
         'license':'CC BY 4.0','license_url':CCBY,'attribution':credit,'rights_reviewed_on':'2026-10-10',
         'rights_review':'Original chapter last-page CC BY4 grant explicitly includes images unless a credit states otherwise; Figure3.1 has no restrictive external credit. Referenced schematic3.2 is held separately.'}
    catalog._validate_source_panel_roles(row);rows.append(row)
    proof.append({'id':ident,'source_PDF_page':2,'source_figure_label':'Fig. 3.1','source_master':{'kind':'complete_original_PDF_JPEG_with_restored_original_ICC_metadata','source_url':BOOK_PDF,'page':2,'object':7},
                  'original_PDF_streams':[book_stream],'runtime_file':filename,
                  'sha256':sha(raw),'decoded_pixel_sha256':sha(picture.tobytes()),'width':picture.width,'height':picture.height,'pixel_mode':picture.mode,
                  'source_caption_full':BOOK_CAPTION,'source_pixels_modified':False,'complete_original_publication_annotations_retained':True,
                  'source_only_fidelity_review':'pending visual verification','clinical_approval':False})
    articles.append({'source_id':'normal-uterus-2018','doi':BOOK_DOI,'title':'Benign Disease of the Uterus','authors':'Karen Kinkel; Susan M. Ascher; Caroline Reinhold',
                     'source_pdf_url':BOOK_PDF,'pdf_sha256':sha(book_raw),'pdf_bytes':len(book_raw),'license':'CC BY 4.0','license_url':CCBY,
                     'original_pdf_ignored_staging_path':str(source/'candidate-0.pdf'),'whole_PDF_redistributed':False,
                     'original_permissions_text':book_text[book_text.index('Open Access This chapter is licensed'):],
                     'no_figure3_1_third_party_credit':True,'other_figure3_2_external_credit_requires_separate_rights_review':True})
    save(evidence/'normal-uterus-2018-license-and-caption-evidence.json',{
        'source_doi':BOOK_DOI,'source_pdf_url':BOOK_PDF,'original_pdf_sha256':sha(book_raw),
        'original_pdf_ignored_staging_path':str(source/'candidate-0.pdf'),
        'original_chapter_authors':['Karen Kinkel','Susan M. Ascher','Caroline Reinhold'],
        'original_copyright_statement':'© The Author(s) 2018',
        'original_permissions_text':articles[-1]['original_permissions_text'],
        'selected_figure':'Fig. 3.1','selected_original_PDF_page':2,'selected_original_image_object':7,
        'source_caption_full':BOOK_CAPTION,'selected_figure_has_no_third_party_credit':True,
        'license':'CC BY 4.0','license_url':CCBY,'commercial_use':True,'redistribution':True,
        'whole_PDF_redistributed':False,'externally_credited_Fig3_2_held_for_conflicting_primary_NC_grant':True,
        'rights_reviewed_on':'2026-10-10','clinical_approval':False})
    published={'schema_version':1,'investigation_id':INVESTIGATION,'articles':articles,'figures':proof,
               'figure_count':len(proof),'runtime_total_bytes':sum((output/p['runtime_file']).stat().st_size for p in proof),
               'source_pixels_modified':False,'clinical_approval':False,'complete_reporting_anatomy_approved':False,
               'every_structure_approved':False,'fine_3D_tissue_layers_supplied':False,'native_acquisition_arrays_included':False,
               'patient_calibration_or_lesion_registration_verified':False}
    save(evidence/'published-source-preservation.json',published)
    save(evidence/'source-figure-contract.json',{'investigation_id':INVESTIGATION,'structure_atlas':rows,
                                              'registration_or_coverage_applied':False,'clinical_approval':False})
    (output/'ATTRIBUTION.md').write_text('# Original cervical MRI and conceptual source figures\n\n'
        +'\n\n'.join(row['attribution'] for row in rows)+'\n\n'+LIMIT+'\n')
    print(json.dumps({'figures':len(proof),'runtime_total_bytes':published['runtime_total_bytes'],
                      'contract':str(evidence/'source-figure-contract.json'),'clinical_approval':False}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--review-output',type=Path,required=True)
    a=p.parse_args();package(a.source_root,a.output,a.review_output)
