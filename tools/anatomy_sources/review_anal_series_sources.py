#!/usr/bin/env python3
"""Keep public form reuse separate from controlled MRI data and historical staging choices."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import urllib.request

FORM_URL='https://www.cancerimagingarchive.net/wp-content/uploads/Anal-Cancer-Staging-Consensus-Form.pdf'
FORM_SHA='7b0c3d5f8b7c2fc1ea3c431f64cfde979d8eedf09e24274b10de0ce79faee10e'


class Tables(HTMLParser):
    def __init__(self):
        super().__init__();self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        elif tag in {'td','th'} and self.row is not None:self.cell={'parts':[],'urls':[]}
        elif tag=='a' and self.cell is not None:
            href=dict(attrs).get('href')
            if href:self.cell['urls'].append(href)
    def handle_data(self,data):
        if self.cell is not None:self.cell['parts'].append(data)
    def handle_endtag(self,tag):
        if tag in {'td','th'} and self.cell is not None:
            self.row.append({'text':re.sub(r'\s+',' ',' '.join(self.cell['parts'])).strip(),'urls':self.cell['urls']});self.cell=None
        elif tag=='tr' and self.row is not None:
            if self.row:self.rows.append(self.row)
            self.row=None


def source_rows(raw):
    parser=Tables();parser.feed(raw.decode());return parser.rows


def review(root,output,fetch=False):
    from pypdf import PdfReader
    root.mkdir(parents=True,exist_ok=True);output.mkdir(parents=True,exist_ok=True)
    names={'exact.html':'https://www.cancerimagingarchive.net/collection/exact/',
           'pelvic-reference-data.html':'https://www.cancerimagingarchive.net/collection/pelvic-reference-data/',
           'Anal-Cancer-Staging-Consensus-Form.pdf':FORM_URL}
    for name,url in names.items():
        p=root/name
        if fetch or not p.exists():
            with urllib.request.urlopen(url,timeout=60) as response:raw=response.read()
            p.write_bytes(raw)
    raw=(root/'exact.html').read_bytes();rows=source_rows(raw)
    def row(title):
        found=[r for r in rows if r[0]['text']==title]
        if len(found)!=1:raise ValueError('Missing or ambiguous source row: '+title)
        return found[0]
    images,clinical,form=row('Images'),row('Clinical data'),row('Proforma for project panelists')
    if not all('Unavailable' in ' '.join(c['text'] for c in r) and 'NIH Controlled Data Access Policy' in ' '.join(c['text'] for c in r) for r in [images,clinical]):
        raise ValueError('Controlled source access changed; re-review before reuse')
    if not any('CC BY 4.0'==c['text'] and 'https://creativecommons.org/licenses/by/4.0/' in c['urls'] for c in form):raise ValueError('Specific form grant differs')
    if FORM_URL not in [u for c in form for u in c['urls']]:raise ValueError('Specific form identity differs')
    pdf=root/'Anal-Cancer-Staging-Consensus-Form.pdf'
    if hashlib.sha256(pdf.read_bytes()).hexdigest()!=FORM_SHA:raise ValueError('Reviewed form snapshot differs')
    reader=PdfReader(pdf);texts=[p.extract_text() for p in reader.pages]
    if len(texts)!=13 or 'N2' not in texts[10] or 'N3' not in texts[10] or 'M2' not in texts[11]:raise ValueError('Historical staging hold needs re-review')
    shutil.copyfile(pdf,output/'original-consensus-form.pdf')
    ct_raw=(root/'pelvic-reference-data.html').read_bytes();ct_rows=source_rows(ct_raw)
    ct_images=[r for r in ct_rows if r[0]['text']=='Images']
    if len(ct_images)!=1 or ct_images[0][1]['text']!='CT':raise ValueError('CT source modality needs re-review')
    if not all(any(r[0]['text'].startswith(title) for r in ct_rows) for title in ['Transformation Matrices','Landmark Coordinates']):raise ValueError('CT annotations need re-review')
    report={'reviewed_at':'2026-10-05','sources':[{'url':names['exact.html'],'page_sha256':hashlib.sha256(raw).hexdigest(),
             'dataset_doi':'10.7937/2023.na2x-j031','image_access':'unavailable_controlled','clinical_access':'unavailable_controlled',
             'specific_form_license':'CC BY 4.0','specific_form_license_url':'https://creativecommons.org/licenses/by/4.0/',
             'form_url':FORM_URL,'form_file':'original-consensus-form.pdf','form_sha256':FORM_SHA,'form_pages':13,
             'data_citation':'Owczarczyk K., Prezzi D., Boisfwr D., Adams R., Goh V. (2023). Expert Anal Cancer Consensus Staging (ExACT). TCIA. DOI 10.7937/2023.na2x-j031.',
             'form_license_is_image_or_clinical_dataset_permission':False},
             {'url':names['pelvic-reference-data.html'],'page_sha256':hashlib.sha256(ct_raw).hexdigest(),
              'dataset_doi':'10.7937/TCIA.2019.WOSKQ5OO','image_modality':'CT','supporting_annotation_type':'registration_landmarks_and_transforms',
              'source_MRI_or_tumour_mask_grant':False}],
             'staging_holds':[{'source_page':11,'choices':['N2','N3'],'runtime_categories_adopted':False},
                              {'source_page':12,'choices':['M2'],'runtime_categories_adopted':False}],
             'anatomy_source_pages':[4,6,8,10],'form_grouping_is_universal_anatomical_or_staging_truth':False,
             'raw_MRI_or_clinical_data_downloaded':False,'clinical_approval':False,'runtime_promoted':False,
             'separate_diagram_credit_and_anatomical_fidelity_verified':False}
    # Retain only typed access facts; source pages stay in ignored research staging.
    (output/'source-access-and-form-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Public form retained; controlled data and historical staging choices remain excluded.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--fetch',action='store_true')
    a=p.parse_args();review(a.source_root,a.output,a.fetch)
