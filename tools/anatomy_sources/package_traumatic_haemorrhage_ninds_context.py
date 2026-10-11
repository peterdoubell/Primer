#!/usr/bin/env python3
"""Preserve fixed 2025 NINDS source documents and their original embedded artwork.

This is a source-context proposal, separate from the 15 CENTER-TBI gallery objects.
It neither modifies native document layout nor registers standalone clinical images.
"""
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[2]
REVIEW=ROOT/'docs/traumatic-haemorrhage-source-review'
SOURCE=REVIEW/'source-ninds-2025'
MEDIA=ROOT/'web/reference-media/radiology-open/traumatic-haemorrhage'
META_SHA='69689abad41aa13eb3644f4e94e841466fea01e41e54d7cec4b6d3d0e3532724'
FILES=[
    ('PMC12409119.1.pdf','ninds-2025-original-publication.pdf','application/pdf',
     '3ce9d893e1983522cb5c1b33751e19de92c89757a05bd6973fbd52403bafdc3f'),
    ('neu.2025.0079_supplementary_appendix.docx','ninds-2025-original-supplementary-appendix.docx',
     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
     '0dbd2e0521778071a2838cf38531f4769799b9d199e1cdfd7370f3422ac45492'),
    ('neu.2025.0079_figure1.jpg','ninds-2025-proposed-template-original.jpg','image/jpeg',
     '8f84bb88da08d9f588efb52ac15c3d3118202a87227d372960190cf9977ee9ea'),
]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def package():
    from PIL import Image
    raw_meta=(SOURCE/'PMC12409119.1.json').read_bytes()
    if sha(raw_meta)!=META_SHA:raise ValueError('Reviewed source metadata changed')
    metadata=json.loads(raw_meta)
    links=[metadata['xml_url'],metadata['pdf_url']]+metadata['media_urls']
    records=[]
    for link in links:
        parsed=urllib.parse.urlparse(link);name=parsed.path.split('/')[-1]
        if parsed.netloc!='pmc-oa-opendata' or not parsed.path.startswith('/PMC12409119.1/'):
            raise ValueError('Fixed publisher packet scope changed')
        raw=(SOURCE/name).read_bytes();expected=urllib.parse.parse_qs(parsed.query)['md5'][0]
        if hashlib.md5(raw).hexdigest()!=expected:raise ValueError('Publisher MD5 changed: '+name)
        records.append({'filename':name,'source_url':link.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/'),
                        'bytes':len(raw),'sha256':sha(raw),'publisher_MD5':expected,'publisher_MD5_verified':True})
    tree=ET.parse(SOURCE/'PMC12409119.1.xml');permissions=tree.find('.//article-meta/permissions')
    if 'https://creativecommons.org/licenses/by/4.0/' not in ET.tostring(permissions,encoding='unicode'):
        raise ValueError('Original NINDS unrestricted BY4 grant changed')
    authors=[' '.join([n.findtext('given-names',''),n.findtext('surname','')]).strip()
             for n in tree.findall('.//article-meta/contrib-group/contrib/name')]
    donor_folder=REVIEW/'source-palmieri-rights';donor=ET.parse(donor_folder/'PMC8976800.1.xml')
    donor_grant=ET.tostring(donor.find('.//permissions'),encoding='unicode')
    if 'https://creativecommons.org/licenses/by/4.0/' not in donor_grant:
        raise ValueError('Borrowed figure donor BY4 grant changed')
    images=[];paragraphs=[]
    with ZipFile(SOURCE/'neu.2025.0079_supplementary_appendix.docx') as document:
        for entry in document.infolist():
            if entry.filename.startswith('word/media/'):
                raw=document.read(entry);image=Image.open(io.BytesIO(raw));image.load()
                images.append({'native_DOCX_member':entry.filename,'bytes':len(raw),'sha256':sha(raw),
                               'width':image.width,'height':image.height,'mode':image.mode,
                               'decoded_channel_sha256':sha(image.tobytes()),'source_pixels_changed':False})
        text=ET.fromstring(document.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in text.findall('.//w:p',ns)]
    if len(images)!=28:raise ValueError('Complete 28-media-entry native appendix changed')
    credit=[p for p in paragraphs if any(k in p for k in ('Exemplar images taken','Palmieri M'))]
    if len(credit)!=2:raise ValueError('Original appendix attribution chain changed')
    documents=[]
    for source_name,name,mime,expected in FILES:
        raw=(SOURCE/source_name).read_bytes()
        if sha(raw)!=expected:raise ValueError('Frozen source document changed')
        destination=MEDIA/name
        if destination.exists() and destination.read_bytes()!=raw:raise ValueError('Frozen public original changed')
        destination.write_bytes(raw)
        record=next(r for r in records if r['filename']==source_name)
        title={'application/pdf':'NINDS imaging working group recommendations (2025)',
               'application/vnd.openxmlformats-officedocument.wordprocessingml.document':'NINDS imaging common data elements: original illustrated appendix (2025)',
               'image/jpeg':'Proposed neuroimaging reporting template (NINDS, 2025)'}[mime]
        documents.append({'id':'traumatic-ninds-2025-'+name.split('ninds-2025-')[1].split('.')[0],
                          'kind':'source-document','title':title,'src':'/app/reference-media/radiology-open/traumatic-haemorrhage/'+name,
                          'local_path':str(destination.relative_to(ROOT)),'mime_type':mime,'bytes':len(raw),'sha256':sha(raw),
                          'source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC12409119/',
                          'asset_source_url':record['source_url'],'license':'CC BY 4.0',
                          'license_url':'https://creativecommons.org/licenses/by/4.0/',
                          'attribution':', '.join(authors)+'. '+metadata['title']+'. DOI 10.1089/neu.2025.0079. © The Author(s) 2025. CC BY4. Unchanged original; acknowledged TRACK-TBI/MGH sources and Palmieri et al. borrowed-figure credit remain in the source appendix.',
                          'unchanged_original':True,'clinical_approval':False,'fine_structure_coverage_granted':False,
                          'current_patient_findings':False,'patient_registration_verified':False})
    repeated={}
    for image in images:repeated.setdefault(image['sha256'],[]).append(image['native_DOCX_member'])
    proof={'schema_version':1,'reviewed_at':'2026-10-11','pmcid':'PMC12409119','doi':'10.1089/neu.2025.0079',
           'title':metadata['title'],'authors':authors,'metadata_sha256':META_SHA,'source_files':records,
           'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
           'permissions_XML':ET.tostring(permissions,encoding='unicode'),'documents':documents,
           'original_source_appendix_all_media':images,'native_media_entries':28,'unique_native_artwork_digests':len(repeated),
           'repeated_native_artwork':{k:v for k,v in repeated.items() if len(v)>1},
           'original_appendix_credit_paragraphs':credit,
           'source_autogenerated_accessibility_descriptions_are_clinical_evidence':False,
           'source_autogenerated_accessibility_descriptions_establish_synthetic_image_provenance':False,
           'borrowed_figure_donor':{
               'pmcid':'PMC8976800','doi':'10.1007/s10143-021-01657-4',
               'source_url':'https://link.springer.com/article/10.1007/s10143-021-01657-4',
               'permissions_XML':donor_grant,'original_XML_sha256':sha((donor_folder/'PMC8976800.1.xml').read_bytes()),
               'license':'CC BY 4.0','figure_specific_excluded_credit_found':False,
               'source_appendix_disclosed_slight_revision_retained':True,
               'native_DOCX_member':'word/media/image21.png',
               'source_revision_scope':'Source appendix keeps the later C/D CTA pair from donor Figure 1 with an added caption; original first-admission A/B pair is not supplied in this appendix image. Primer does not alter this revised source artwork.'},
           'complete_native_DOCX_layout_vectors_text_labels_and_media_preserved':True,
           'standalone_clinical_figures_registered':False,'runtime_registry_mutated':False,
           'clinical_approval':False,'fine_structure_coverage_granted':False,
           'source_case_registration_between_TRACK_TBI_and_CENTER_TBI_established':False,
           'native_DICOM_segmentation_or_mesh_supplied':False,'total_public_context_document_bytes':sum(r['bytes'] for r in documents)}
    (REVIEW/'ninds-2025-source-context-proposal.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n')
    (REVIEW/'ninds-2025-native-appendix-paragraphs.json').write_text(json.dumps(paragraphs,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'documents':len(documents),'native_appendix_media':28,'unique_artwork':len(repeated),
                      'bytes':proof['total_public_context_document_bytes'],'clinical_approval':False}))


if __name__=='__main__':package()
