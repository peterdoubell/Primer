#!/usr/bin/env python3
"""Preserve original cyst/nodule figures with separate modalities and source pathology claims."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

SELECTION={
 'PMC8355307':{'Fig4':{'a':'CT','b':'MRI','c':'MRI','d':'MRI'},'Fig9':{'a':'CT','b':'CT','c':'MRI','d':'MRI'},
              'Fig13':{'a':'MRI','b':'MRI','c':'CT'},'Fig18':{'a':'MRI','b':'MRI'}},
 'PMC13315461':{'Fig3':{**{c:'MRI' for c in 'abcdef'},'g':'PET-CT','h':'Ultrasound'},
               'Fig4':{**{c:'MRI' for c in 'abcdef'},'g':'PET-CT','h':'Ultrasound','i':'Histology','j':'Histology'},
               'Fig5':{**{c:'MRI' for c in 'abcdef'},'g':'PET-CT','h':'Ultrasound','i':'Histology','j':'Histology'}}}


def acquire(root,output):
    from PIL import Image
    from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
    records=[];output.mkdir(parents=True,exist_ok=True)
    for pmc,selection in SELECTION.items():
        meta_path=root/(pmc+'.1.json');meta=json.loads(meta_path.read_text());xml_path=root/(pmc+'.1.xml');xml=xml_path.read_bytes()
        expected=urllib.parse.parse_qs(urllib.parse.urlparse(meta['xml_url']).query)['md5'][0]
        if hashlib.md5(xml).hexdigest()!=expected or meta['pmcid']!=pmc or meta['is_retracted'] is not False:raise ValueError('Original XML/identity/retraction metadata differs')
        tree=ET.fromstring(xml);permissions=tree.find('.//article-meta/permissions');name,url=exact_license(permissions)
        if name!='CC BY 4.0':raise ValueError('Selected cyst source grant differs')
        for figid,types in selection.items():
            fig=tree.find('.//fig[@id="'+figid+'"]');caption=' '.join(fig.find('caption').itertext())
            if any(s in caption.lower() for s in ['(from:','reproduced','reprinted','courtesy']) or fig.find('attrib') is not None or fig.find('permissions') is not None:
                raise ValueError('Selected figure has unreviewed separate credit')
            file=fig.find('graphic').get('{http://www.w3.org/1999/xlink}href');links=[u for u in meta['media_urls'] if urllib.parse.urlparse(u).path.endswith('/'+file)]
            if len(links)!=1:raise ValueError('Original media distribution is ambiguous')
            media_url=links[0].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/');path=root/file
            if not path.exists():path.write_bytes(urllib.request.urlopen(media_url,timeout=45).read())
            raw=path.read_bytes();md5=urllib.parse.parse_qs(urllib.parse.urlparse(media_url).query)['md5'][0]
            if hashlib.md5(raw).hexdigest()!=md5:raise ValueError('Original figure publisher MD5 differs')
            with Image.open(io.BytesIO(raw)) as image:image.verify()
            with Image.open(io.BytesIO(raw)) as image:width,height=image.size
            records.append({'pmcid':pmc,'doi':meta['doi'],'article_title':meta['title'],'figure_id':figid,'source_filename':file,'source_url':media_url,
                            'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/', 'publisher_md5':md5,'publisher_md5_verified':True,
                            'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'width':width,'height':height,'source_caption':caption,
                            'source_panel_types':types,'selected_mri_panels':[p for p,kind in types.items() if kind=='MRI'],
                            'license':name,'license_url':url,'permissions_xml':ET.tostring(permissions,encoding='unicode'),'source_copyright':permissions.findtext('copyright-statement'),
                            'authors':[' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib/name')],
                            'metadata_sha256':hashlib.sha256(meta_path.read_bytes()).hexdigest(),'xml_sha256':hashlib.sha256(xml).hexdigest(),
                            'source_pixels_altered':False,'anatomical_approval':False})
            print(pmc,figid,width,height,flush=True)
    (output/'original-source-review.json').write_text(json.dumps({'figures':records,'clinical_approval':False,'runtime_promoted':False,
       'separately_credited_2021_book_figure_excluded':'PMC8355307 Fig2',
       'limits':['Published local figures do not supply calibrated native DICOM volumes, complete cyst/duct geometry or independently verified sequence timing.',
                 'MRI, CT, PET-CT, endoscopic ultrasound and histology panels remain distinct; no cross-modality feature credit is borrowed.',
                 'Source low/high-grade histology descriptions are not MRI-derived pathological certainty; enhancement alone does not establish grade.']},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();acquire(a.source_root,a.output)
