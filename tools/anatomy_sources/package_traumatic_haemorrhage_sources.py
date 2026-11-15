#!/usr/bin/env python3
"""Preserve the complete licensed CENTER-TBI publication and all native figures.

All destinations and source objects are fixed. This writes an integration proposal,
never the curriculum, runtime registries, source geometry, or clinical approvals.
RGB PNGs interpret the PDF's DeviceCMYK colour space at its native dimensions;
original DCT streams and the entire unchanged PDF remain independently inspectable.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'docs/traumatic-haemorrhage-source-review'
SOURCE = REVIEW / 'source-center-tbi-2024'
MEDIA = ROOT / 'web/reference-media/radiology-open/traumatic-haemorrhage'
DATE = '2026-10-11'
DOI = '10.1089/neu.2023.0553'
ARTICLE = 'https://journals.sagepub.com/doi/10.1089/neu.2023.0553'
SOURCE_URL = 'https://researchmgt.monash.edu/ws/portalfiles/portal/660520113/659672588-oa.pdf'
PDF_NAME = 'vande-vyvere-2024-original-publication.pdf'
PDF_SHA = '5f9dd9f79dc0ca55d1c465dc3dfcbee2eda5d3631d59770789e3685b68f2250b'
AUTHORS = ['Thijs Vande Vyvere', 'Dana Pisică', 'Guido Wilms', 'Lene Claes',
           'Pieter Van Dyck', 'Annemiek Snoeckx', 'Luc van den Hauwe',
           'Pim Pullens', 'Jan Verheyden', 'Max Wintermark', 'Sven Dekeyzer',
           'Christine L. Mac Donald', 'Andrew I.R. Maas', 'Paul M. Parizel',
           'The CENTER-TBI Participants and Investigators']
# figure ID, native PDF image object, placement page, caption page, source space
OBJECTS = [
    ('1',193,8,8,'DeviceCMYK'), ('2-panel-1',206,11,10,'DeviceCMYK'),
    ('2-panel-2',215,13,12,'DeviceCMYK'), ('3',219,14,14,'DeviceCMYK'),
    ('4',226,16,16,'DeviceCMYK'), ('5',242,21,21,'DeviceCMYK'),
    ('6',250,23,23,'DeviceCMYK'), ('7',263,27,27,'DeviceCMYK'),
    ('8',267,28,28,'DeviceCMYK'), ('9',271,29,29,'DeviceCMYK'),
    ('10',284,32,32,'DeviceCMYK'), ('11',289,33,33,'DeviceCMYK'),
    ('12',288,33,33,'DeviceGray'), ('13',295,34,34,'DeviceCMYK'),
    ('14',299,35,35,'DeviceCMYK'),
]
SUMMARIES = {
    '1':'Cohort combinations of four frequent CT lesion types and six-month outcomes; a statistical figure, not a patient image.',
    '2-panel-1':'Complete source panel 1: skull fractures and published 3D CT reformats, epidural and acute/chronic subdural blood, traumatic SAH, midline-shift methods, and third/fourth-ventricle compression.',
    '2-panel-2':'Complete source panel 2: cisternal compression, serial contusions and intracerebral blood, intraventricular sedimentation, source-described axonal injury, and cerebral swelling. L4/L5 are MRI, separate from the CT examples.',
    '3':'Source axial and coronal noncontrast CT bone windows show skull-base fractures involving the carotid canal; arterial dissection is a risk, not a demonstrated diagnosis in these images.',
    '4':'Cohort haematoma/contusion volume distributions by source-defined TBI severity; statistical distributions, not calibrated measurements on the selected images.',
    '5':'Cohort combinations of cisternal compression locations; this chart supplies no patient-specific cisternal boundaries.',
    '6':'Cohort combinations of brain herniation locations; this chart supplies no patient-specific geometry.',
    '7':'Source MRI FLAIR and SWI illustrate temporal and brainstem traumatic injury, with the brainstem lesion visible only on SWI. MRI context does not supply CT visibility.',
    '8':'Cohort frequencies of source-labelled axonal injury foci by location; statistical figure only.',
    '9':'Two distinct patients on axial noncontrast CT: pontomesencephalic or pontine/midbrain haemorrhage associated with subdural blood and descending herniation; source secondary brainstem injury context.',
    '10':'Cohort co-occurrence correlations among source CT common data elements; correlation does not establish a causal mechanism or individual prognosis.',
    '11':'Cohort combinations of CT common data elements in source mild and moderate-severe groups; statistical figure only.',
    '12':'Cohort hierarchical lesion clustering in source mild and moderate-severe groups; statistical figure only.',
    '13':'Source distributions of six CT grading systems on admission imaging; no grading rule or clinical threshold is validated for the current reader by this chart.',
    '14':'Source six-month GOSE outcome distributions within CT score categories; cohort outcome association is separate from patient-specific prediction.',
}
LIMITS = ('Complete published artwork at the PDF image object’s original dimensions; selected sections only, '
          'without native DICOM, pixel spacing, CT Hounsfield values, a complete acquired stack, source segmentation, '
          'patient-specific mesh, or independently calibrated calipers. Source arrows, dashed lines and labels are retained. '
          'Cohort statistics and source diagnoses do not establish clinical approval, complete fine-structure coverage, '
          'patient registration or current-patient findings. Original untagged DeviceCMYK interpretation is preserved '
          'in the PDF and encoded streams; display PNGs use a declared PDF colour conversion, not photographic enhancement.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def preserve(path, raw):
    if path.exists() and path.read_bytes() != raw:
        raise ValueError('Frozen source bytes differ: ' + str(path.relative_to(ROOT)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def panels_for(identifier):
    if identifier == '2-panel-1':
        counts = {'A':6,'B':5,'C':5,'D':5,'E':5,'F':3,'G':2}
        return {letter+str(n):'CT' for letter,count in counts.items() for n in range(1,count+1)}
    if identifier == '2-panel-2':
        return {letter+str(n):('MRI' if letter == 'L' and n in (4,5) else 'CT')
                for letter in 'HIJKLM' for n in range(1,6)}
    if identifier in {'3','9'}:
        return {'A':'CT','B':'CT'}
    if identifier == '7':
        return {'A':'MRI','B':'MRI'}
    return {}


def relationships(identifier):
    if identifier == '2-panel-1':
        return {'same_case_groups_explicit_in_caption':[['A1','A2'],['A3','A4'],['A5','A6'],['D4','D5'],['F1','F2','F3']],
                'source_3D_volume_rendered_views':['A2','A4','A6'],
                'source_3D_views_are_static_publication_images_not_reconstructable_meshes':True,
                'source_caliper_claims':{'F2':'MLS = 1.94 cm, A/2-B at foramen of Monro',
                                        'F3':'MLS = 2.09 cm, perpendicular to anterior/posterior falx line'},
                'source_numeric_claims_independently_calibrated':False,
                'case_age_and_sex_by_panel':'not reported; cohort demographics cannot establish individual age/sex'}
    if identifier == '2-panel-2':
        return {'same_case_time_groups_explicit_in_caption':[['I1','I2'],['J3','J4','J5']],
                'time_descriptions':{'I1':'initial injury image','I2':'over the next few days; precise interval not supplied',
                                     'J3':'initial time point; initially classified as focal TAI',
                                     'J4':'2 hours later; grew into ICH','J5':'2 days later; further ICH growth'},
                'source_reconsidered_initial_J3_diagnosis':'Likely small intracerebral haemorrhage retrospectively, rather than proved focal axonal injury',
                'MRI_sequences':{'L4':'SWI','L5':'FLAIR; lesion not visible on SWI (not shown)'},
                'cross_modality_same_patient_registration_established':False,
                'source_axonal_injury_terminology_under_debate':True}
    if identifier == '3':
        return {'same_case_groups_explicit_in_caption':[['A','B']],
                'planes':{'A':'axial','B':'coronal'},'CT_window':'bone',
                'carotid_dissection_demonstrated':False}
    if identifier == '7':
        return {'same_case_groups_explicit_in_caption':[['A','B']],
                'MRI_sequences':{'A':'axial FLAIR','B':'axial SWI'},
                'brainstem_lesion_visible_on':['B'],'matching_CT_supplied':False}
    if identifier == '9':
        return {'different_patients_explicit_in_caption':[['A'],['B']],
                'planes':{'A':'axial','B':'axial'},'CT_window':'soft tissue',
                'source_secondary_injury_context':'Descending herniation-associated brainstem haemorrhage; does not prove mechanism from pixels',
                'B_related_MLS_ventricular_compression_not_shown_in_figure':True}
    return {'statistical_population_plot_not_patient_image':True}


def caption(reader, identifier, page):
    text = reader.pages[page-1].extract_text()
    marker = 'FIG. 2 Panel '+identifier[-1]+'.' if identifier.startswith('2-') else 'FIG. '+identifier+'.'
    start = text.index(marker)
    end_markers = ['\nFIG. ', '\nTable ', '\nIMAGING FINDINGS', '\n'+str(2247+page)]
    end = min([text.find(m,start+len(marker)) for m in end_markers if text.find(m,start+len(marker))>=0] or [len(text)])
    return text[start:end].strip()


def validate_proposal(proposal):
    expected = {f'open-traumatic-centertbi-2024-fig{i}' for i,*_ in OBJECTS}
    rows = proposal.get('images',[])
    if {r.get('id') for r in rows} != expected or len(rows) != 15:
        raise ValueError('Complete 15-object source selection required')
    for row in rows:
        context = row['source_context']
        if row['sha256'] != next(f['display_sha256'] for f in proposal['source_figures'] if f['id']==row['id']):
            raise ValueError('Display source digest mismatch')
        if any(context.get(k) is not False for k in ('current_patient_findings','native_DICOM_or_volumetric_stack_supplied',
                                                   'native_patient_registration_verified','fine_structure_coverage_granted')):
            raise ValueError('Unacquired source capability or clinical coverage claimed')
        types = panels_for(row['figure_identifier'])
        if types:
            selected = [p for p,t in types.items() if t==row['modality']]
            if (context.get('panel_types')!=types or context.get('selected_panels')!=selected
                    or row.get('clinical_panels')!=selected):
                raise ValueError('Source modality/selection contradiction')
        if row['license'] != 'CC BY 4.0' or row['license_url'] != 'https://creativecommons.org/licenses/by/4.0/':
            raise ValueError('Original unrestricted BY grant required')
    if any(a.get('requirement_coverage') != {} or a.get('structure_ids') != []
           or a['anatomical_review']['status'] != 'pending' for a in proposal['assets']):
        raise ValueError('Source inspection cannot grant anatomical coverage')


def package(acquire=False):
    from PIL import Image
    from pypdf import PdfReader
    import pymupdf
    SOURCE.mkdir(parents=True,exist_ok=True)
    source_pdf = SOURCE / PDF_NAME
    if acquire and not source_pdf.exists():
        subprocess.run(['curl','--location','--fail','--max-time','60','--user-agent','Mozilla/5.0',
                        SOURCE_URL,'--output',str(source_pdf)],check=True)
    raw_pdf = source_pdf.read_bytes()
    if sha(raw_pdf)!=PDF_SHA:
        raise ValueError('Acquired original publication differs from reviewed digest')
    reader=PdfReader(io.BytesIO(raw_pdf));document=pymupdf.open(stream=raw_pdf,filetype='pdf')
    if len(reader.pages)!=50 or 'Creative Commons License (CC-BY)' not in reader.pages[0].extract_text():
        raise ValueError('Original publication grant/page count differs')
    preserve(MEDIA/PDF_NAME,raw_pdf)
    rows=[];assets=[];figures=[]
    for identifier,object_id,page,caption_page,space in OBJECTS:
        obj=reader.get_object(object_id)
        if obj['/Filter']!='/DCTDecode' or str(obj['/ColorSpace'])!='/'+space:
            raise ValueError('Reviewed native image encoding changed')
        native=obj._data;name='centertbi-2024-fig'+identifier
        preserve(MEDIA/(name+'-original.jpg'),native)
        pix=pymupdf.Pixmap(document,object_id)
        display=pymupdf.Pixmap(pymupdf.csRGB,pix) if pix.colorspace.n!=3 else pix
        image=Image.frombytes('RGB',(display.width,display.height),display.samples)
        output=io.BytesIO();image.save(output,format='PNG',optimize=False)
        display_raw=output.getvalue();preserve(MEDIA/(name+'.png'),display_raw)
        native_image=Image.open(io.BytesIO(native));native_image.load()
        figure_id='open-traumatic-centertbi-2024-fig'+identifier
        original_caption=caption(reader,identifier,caption_page)
        types=panels_for(identifier);modality='MRI' if identifier=='7' else ('CT' if types else 'Schematic')
        selected=[p for p,t in types.items() if t==modality]
        context={'setting':'in_vivo' if types else 'unknown','laterality':'unknown',
                 'population':{'life_stage':'unknown','cohort_context':'4087 acute admission CT patients; median 50 years, range 0–96; 238 under 18. Individual panel ages are not supplied.'},
                 'depicted_state':'source_published_TBI_examples' if types else 'source_cohort_statistics',
                 'extent':'local' if types else 'not_applicable','current_patient_findings':False,
                 'native_DICOM_or_volumetric_stack_supplied':False,'native_patient_registration_verified':False,
                 'fine_structure_coverage_granted':False,**relationships(identifier)}
        if types:context.update(selected_panels=selected,panel_types=types,panel_states={p:'source_'+p for p in types})
        attribution=('© Thijs Vande Vyvere et al. 2024; '+', '.join(AUTHORS)+'. Journal of Neurotrauma 41:2248–2297. DOI '+DOI+'. CC BY 4.0. Complete Figure '+identifier+'; original PDF image stream retained, native-dimension lossless PNG uses disclosed PDF colour interpretation. No endorsement implied.')
        fact={'id':figure_id,'figure_identifier':identifier,'PDF_object_id':object_id,'source_page_1_based':page,
              'caption_page_1_based':caption_page,'source_caption_full':original_caption,'width':display.width,'height':display.height,
              'source_color_space':space,'source_bits_per_component':int(obj['/BitsPerComponent']),
              'original_encoded_stream_path':str((MEDIA/(name+'-original.jpg')).relative_to(ROOT)),
              'original_encoded_stream_sha256':sha(native),'original_encoded_stream_bytes':len(native),
              'original_stream_Pillow_mode':native_image.mode,'original_stream_Pillow_decoded_sha256':sha(native_image.tobytes()),
              'PDF_decoded_channel_sha256':sha(pix.samples),'PDF_decoded_channel_count':pix.n,
              'display_path':str((MEDIA/(name+'.png')).relative_to(ROOT)),'display_sha256':sha(display_raw),
              'display_bytes':len(display_raw),'display_RGB_sample_sha256':sha(display.samples),
              'source_ICC_profile_supplied':False,'PDF_output_intent_supplied':False,'source_geometry_changed':False,
              'source_crop_resample_or_repaint':False,'display_colour_conversion_applied':True,
              'colour_conversion':'MuPDF PDF DeviceCMYK/DeviceGray interpretation to RGB; PNG lossless at exact source dimensions',
              'renderer_version':pymupdf.__version__,'highest_resolution_publisher_master_verified':False}
        figures.append(fact)
        row={'id':figure_id,'kind':'clinical-image' if types else 'schematic','src':'/app/reference-media/radiology-open/traumatic-haemorrhage/'+name+'.png',
             'width':display.width,'height':display.height,'sha256':sha(display_raw),'source_url':ARTICLE,
             'figure_url':ARTICLE+'#fig'+('2' if identifier.startswith('2-') else identifier),'figure_identifier':identifier,
             'asset_source_url':SOURCE_URL,'caption':SUMMARIES[identifier],'alt':SUMMARIES[identifier],
             'source_caption_full':original_caption,
             'modality':modality,'image_state':context['depicted_state'],'structures_visible':['Source-described local published appearances; complete boundaries and extent remain unapproved'] if types else ['Source cohort statistics only'],
             'limits':LIMITS,'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
             'attribution':attribution,'rights_reviewed_on':DATE,
             'rights_review':'Original unchanged publication page 1 explicitly CC BY 4.0; all 14 numbered main figures inspected; no figure-specific excluded credit found. Source cohort ethical statement retained; individual publication consent not independently established.',
             'acquisition':'Complete native PDF image object with lossless RGB display interpretation; unchanged encoded stream and entire original PDF retained',
             'source_context':context,'color_context':{k:fact[k] for k in ('source_color_space','source_ICC_profile_supplied','PDF_output_intent_supplied','display_colour_conversion_applied','colour_conversion','renderer_version')},
             'original_publication_pdf':{'src':'/app/reference-media/radiology-open/traumatic-haemorrhage/'+PDF_NAME,'sha256':PDF_SHA,'bytes':len(raw_pdf),'unchanged_original':True},
             'original_encoded_stream':{'src':'/app/reference-media/radiology-open/traumatic-haemorrhage/'+name+'-original.jpg','sha256':sha(native),'bytes':len(native),'browser_display_without_PDF_colour_interpretation_is_not_authoritative':True}}
        if types:row['clinical_panels']=selected
        if identifier=='2-panel-2':row['ancillary_panels']=[{'kind':'MRI','panels':['L4','L5'],'structures_visible':['Source SWI/FLAIR local traumatic lesion examples'],
                                                         'limits':'MRI panels do not supply CT lesion visibility or establish co-registered CT/MRI cases.'}]
        rows.append(row)
        assets.append({'id':figure_id,'kind':'clinical_image' if types else 'schematic','name':'CENTER-TBI source Figure '+identifier,
                       'local_path':fact['display_path'],'sha256':row['sha256'],'regions':['brain'],
                       'investigation_ids':['ra.ct-traumatic-haemorrhage'],'structure_ids':[],'modality':modality,
                       'source_context':context,'requirement_coverage':{},
                       'source':{'url':ARTICLE,'figure_url':row['figure_url'],'asset_url':SOURCE_URL,
                                 'license':{'name':'CC BY 4.0','url':row['license_url'],'commercial_use':True,'redistribution':True,
                                            'review_status':'verified','evidence_path':'docs/traumatic-haemorrhage-source-review/original-source-review.json',
                                            'evidence_sha256':'PENDING_SOURCE_REVIEW_DIGEST','attribution':attribution,'reviewed_at':DATE}},
                       'pixel_provenance':{'acquisition':row['acquisition'],'original_source_PDF_sha256':PDF_SHA,
                                           'original_encoded_stream_sha256':sha(native),'source_pixels_changed':True,
                                           'source_pixels_changed_reason':'Declared colour-space interpretation only; original channels/encoded source remain retained separately',
                                           'source_geometry_changed':False,'cropped_resampled_or_repainted':False,
                                           'highest_resolution_acquired_master_verified':False},
                       'anatomical_review':{'status':'pending','reason':'Publication source checking does not establish complete fine boundaries, calibrated acquisition or source-native geometry.'},
                       'visual_review':{'status':'source_checked','sha256':row['sha256'],'reviewed_at':DATE,
                                        'evidence_path':'docs/traumatic-haemorrhage-source-review/visual-source-review.json'}})
    original={'schema_version':1,'reviewed_at':DATE,'doi':DOI,'source_article_url':ARTICLE,'original_PDF_source_url':SOURCE_URL,
              'authors':AUTHORS,'original_PDF_path':str((MEDIA/PDF_NAME).relative_to(ROOT)),'original_PDF_sha256':PDF_SHA,
              'original_PDF_bytes':len(raw_pdf),'page_count':50,'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
              'grant_page_1_based':1,'copyright_grant_full':'ª Thijs'+reader.pages[0].extract_text().split('ª Thijs')[1].split('Journal of Neurotrauma')[0] if 'ª Thijs' in reader.pages[0].extract_text() else reader.pages[0].extract_text()[-900:],
              'publisher_HTML_rights_url':ARTICLE,'main_figure_numbers':list(range(1,15)),'native_image_object_count':15,
              'figures':figures,'preserved_original_document_vectors_text_and_labels':True,
              'source_ICC_profile_or_PDF_output_intent_supplied':False,'clinical_approval':False,'fine_structure_coverage_granted':False,
              'patient_consent_independently_verified':False,'retraction_status_independently_verified':False,
              'publisher_MD5_or_other_publisher_digest_supplied':False,'highest_resolution_publisher_master_verified':False,
              'ethical_statement_original_page_1_based':46,'ethical_statement_original_text':reader.pages[45].extract_text(),
              'supplementary_source_documents':{'publisher_listed_DOCX_count':52,'acquired_count':0,
                  'same_CC_BY_grant_reported_by_publisher':True,'publisher_listing_url':ARTICLE,
                  'acquisition_limitation':'Publisher HTML and supplemental DOCX fetches returned HTTP 403 to this runtime. Independent higher-resolution figure masters were not acquired. Unacquired supplements and masters are not represented as acquired sources.'},
              'missing_native_deliverables':['original DICOM/complete acquisition stack','native calibrated HU and pixel spacing',
                                            'complete source segmentation and patient-specific 3D surfaces','individual clinical diagnosis/registration/consent verification',
                                            'all publisher supplemental DOCX and source-resolution master files'],
              'excluded_sources':[{'pmcid':'PMC5307932','reason':'CC BY-NC 4.0; no commercial permission supplied'},
                                  {'pmcid':'PMC3026928','reason':'CC BY-NC 4.0; no commercial permission supplied'},
                                  {'pmcid':'PMC4734784','reason':'CC BY-NC 3.0; no commercial permission supplied'},
                                  {'pmcid':'PMC6358760','figure_numbers':[3,4,5,6,7],'reason':'Reprint/third-party credits; broad article BY grant not substituted for independent permission'}]}
    review_raw=(json.dumps(original,indent=2,ensure_ascii=False)+'\n').encode();(REVIEW/'original-source-review.json').write_bytes(review_raw)
    for asset in assets:asset['source']['license']['evidence_sha256']=sha(review_raw)
    proposal={'schema_version':1,'investigation_id':'ra.ct-traumatic-haemorrhage','module_id':'rad.5.intracranial-haemorrhage',
              'source_figures':figures,'images':rows,'assets':assets,'runtime_registry_mutated':False,
              'clinical_approval':False,'fine_structure_coverage_granted':False,'source_review_sha256':sha(review_raw),
              'originals_plus_display_total_bytes':len(raw_pdf)+sum(f['original_encoded_stream_bytes']+f['display_bytes'] for f in figures)}
    validate_proposal(proposal)
    (REVIEW/'integration-proposal.json').write_text(json.dumps(proposal,indent=2,ensure_ascii=False)+'\n')
    document.close()
    print(json.dumps({'source_figures':len(figures),'total_bytes':proposal['originals_plus_display_total_bytes'],
                      'source_review_sha256':sha(review_raw),'clinical_approval':False}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquire',action='store_true',help='Acquire the fixed trusted original publication when absent')
    package(parser.parse_args().acquire)
