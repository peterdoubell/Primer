#!/usr/bin/env python3
"""Preserve original vascular-complication figures and conflicting source modality facts."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

SELECTION=[('PMC12490646','F2','CT','pancreatitis_gda_pseudoaneurysm_source_context'),
           ('PMC9870600','FIG5','CT','recurrent_pancreatitis_pseudoaneurysm_source_context'),
           ('PMC12358223','FIG2','CT','pancreatitis_portal_vein_thrombus_source_context')]


def exact_license(permissions):
    urls=[]
    for element in permissions.iter():
        urls += [v for k,v in element.attrib.items() if k.endswith('href')]
        if element.tag.endswith('license_ref') and element.text:urls.append(element.text.strip())
    found={url.replace('http://','https://').rstrip('/')+'/' for url in urls if 'creativecommons.org/licenses/' in url}
    for name,url in [('CC BY 4.0','https://creativecommons.org/licenses/by/4.0/'),('CC BY 3.0','https://creativecommons.org/licenses/by/3.0/')]:
        if found=={url}:return name,url
    raise ValueError('Original source grant is missing, ambiguous or restricted')


def acquire(root,output):
    from PIL import Image
    output.mkdir(parents=True,exist_ok=True);rows=[]
    for pmc,figid,modality,state in SELECTION:
        metadata_path=root/(pmc+'.1.json');metadata=json.loads(metadata_path.read_text());xml_path=root/(pmc+'.1.xml');xml=xml_path.read_bytes()
        expected=urllib.parse.parse_qs(urllib.parse.urlparse(metadata['xml_url']).query)['md5'][0]
        if hashlib.md5(xml).hexdigest()!=expected or metadata.get('is_retracted') is not False or metadata.get('pmcid')!=pmc:
            raise ValueError('Source identity/XML MD5/retraction metadata differs')
        tree=ET.fromstring(xml);permissions=tree.find('.//article-meta/permissions');license_name,license_url=exact_license(permissions)
        doi=tree.findtext('.//article-id[@pub-id-type="doi"]')
        if doi!=metadata['doi']:raise ValueError('Original article DOI differs')
        fig=tree.find('.//fig[@id="'+figid+'"]')
        if fig is None or fig.find('attrib') is not None or fig.find('permissions') is not None:raise ValueError('Figure-specific rights require review')
        name=fig.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        links=[u for u in metadata['media_urls'] if urllib.parse.urlparse(u).path.endswith('/'+name)]
        if len(links)!=1:raise ValueError('Original media is missing or ambiguous')
        url=links[0].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/');path=root/name
        if not path.exists():path.write_bytes(urllib.request.urlopen(url,timeout=45).read())
        raw=path.read_bytes();md5=urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['md5'][0]
        if hashlib.md5(raw).hexdigest()!=md5:raise ValueError('Original media publisher MD5 differs')
        with Image.open(io.BytesIO(raw)) as image:image.verify()
        with Image.open(io.BytesIO(raw)) as image:width,height=image.size
        caption=' '.join(fig.find('caption').itertext());body_facts=[]
        if pmc=='PMC12490646':
            for paragraph in tree.findall('.//body//p'):
                text=' '.join(paragraph.itertext())
                if 'CT angiogram' in text and 'Figure' in text:body_facts.append(text)
            if not body_facts:raise ValueError('Original body CTA statement no longer found')
        rows.append({'pmcid':pmc,'doi':doi,'article_title':metadata['title'],'figure_id':figid,'source_filename':name,'source_url':url,
                     'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/', 'publisher_md5':md5,'publisher_md5_verified':True,
                     'sha256':hashlib.sha256(raw).hexdigest(),'width':width,'height':height,'bytes':len(raw),'source_caption':caption,
                     'article_permissions_xml':ET.tostring(permissions,encoding='unicode'),'license':license_name,'license_url':license_url,
                     'source_copyright':permissions.findtext('copyright-statement'),
                     'authors':[' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib/name')],
                     'metadata_sha256':hashlib.sha256(metadata_path.read_bytes()).hexdigest(),'xml_sha256':hashlib.sha256(xml).hexdigest(),
                     'selected_modality':modality,'source_state':state,'source_modality_caption_body_discrepancy':pmc=='PMC12490646',
                     'retained_original_body_modality_statements':body_facts,
                     'source_pixels_altered':False,'clinical_approval':False,'runtime_promoted':False})
        print(pmc,figid,license_name,width,height,flush=True)
    (output/'original-source-review.json').write_text(json.dumps({'figures':rows,'clinical_approval':False,
        'limits':['Original article/body/legend statements remain distinct from direct image-modality inspection and independently verified acquisition phase.',
                  'CT enhancement focus alone does not verify active extravasation, complete arterial neck geometry or a treatment decision.',
                  'The recurrent-pancreatitis source case is not relabelled as an established acute-only episode.',
                  'Original XML CC BY 3.0 is retained; a different publisher PDF grant is not silently substituted.']},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();acquire(a.source_root,a.output)
