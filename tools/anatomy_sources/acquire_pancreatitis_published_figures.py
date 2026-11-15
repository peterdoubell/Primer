#!/usr/bin/env python3
"""Acquire licensed original clinical figure bytes with publisher MD5 and explicit panel facts."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

PANEL_TYPES={1:{'whole':'CT'},3:{'a':'CT','b':'CT'},4:{'a':'MRI','b':'MRI'},
             5:{'a':'Ultrasound','b':'CT','c':'CT','d':'Ultrasound','e':'CT','f':'MRI'},6:{'whole':'CT'},
             7:{'a':'Ultrasound','b':'CT','c':'MRI'},8:{'a':'CT','b':'CT'}}


def verify_license(tree):
    permissions=tree.find('.//article-meta/permissions')
    links=[r.get('{http://www.w3.org/1999/xlink}href','') for r in permissions.findall('license')]
    if not any(url.rstrip('/') in ['http://creativecommons.org/licenses/by/4.0','https://creativecommons.org/licenses/by/4.0'] for url in links):
        raise ValueError('Original article commercial reuse grant is not CC BY 4.0')
    return permissions


def acquire(root,output):
    from PIL import Image
    metadata_path=root/'PMC4760067.1.json';metadata=json.loads(metadata_path.read_text())
    xml_path=root/'PMC4760067.1.xml';xml=xml_path.read_bytes()
    expected=urllib.parse.parse_qs(urllib.parse.urlparse(metadata['xml_url']).query)['md5'][0]
    if hashlib.md5(xml).hexdigest()!=expected or metadata.get('is_retracted') is not False:raise ValueError('Original article metadata/XML integrity differs')
    tree=ET.fromstring(xml);permissions=verify_license(tree)
    output.mkdir(parents=True,exist_ok=True);records=[]
    for number,types in PANEL_TYPES.items():
        fig=tree.find('.//fig[@id="gov036-F'+str(number)+'"]')
        if fig is None or fig.find('permissions') is not None or fig.find('attrib') is not None:
            raise ValueError('Missing figure or figure-specific rights require separate review')
        filename=fig.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        links=[url for url in metadata['media_urls'] if urllib.parse.urlparse(url).path.endswith('/'+filename)]
        if len(links)!=1:raise ValueError('Original media distribution is ambiguous')
        url=links[0].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/');path=root/filename
        if not path.exists():path.write_bytes(urllib.request.urlopen(url,timeout=45).read())
        raw=path.read_bytes();expected=urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['md5'][0]
        if hashlib.md5(raw).hexdigest()!=expected:raise ValueError('Original figure publisher MD5 differs')
        with Image.open(io.BytesIO(raw)) as pixels:
            pixels.verify()
        with Image.open(io.BytesIO(raw)) as pixels:width,height=pixels.size
        records.append({'figure_number':number,'source_figure_id':fig.get('id'),'source_filename':filename,'source_url':url,
                        'original_publisher_md5':expected,'md5_verified':True,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
                        'width':width,'height':height,'figure_caption':' '.join(fig.find('caption').itertext()),
                        'source_panel_types':types,'source_figure_restrictive_credit_found':False,
                        'source_pixels_cropped_resampled_recompressed_or_edited':False,'clinical_approval':False,'runtime_promoted':False})
        print('Original figure',number,width,height,flush=True)
    result={'article_pmcid':'PMC4760067','doi':metadata['doi'],'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC4760067/',
            'source_metadata_sha256':hashlib.sha256(metadata_path.read_bytes()).hexdigest(),'source_xml_sha256':hashlib.sha256(xml).hexdigest(),
            'source_xml_publisher_md5':hashlib.md5(xml).hexdigest(),'article_permissions_xml':ET.tostring(permissions,encoding='unicode'),
            'article_license':'CC BY 4.0','authors':[' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib/name')],
            'source_copyright':permissions.findtext('copyright-statement'),'figures':records,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Published figure pixels are original repository media, not original DICOM series or calibrated whole-volume anatomy.',
                      'Panel modality/temporal correspondence must remain explicit; mixed clinical figures cannot lend MRI/ultrasound facts to CT panels.',
                      'Image grants do not approve anatomical boundaries, histology, phase timing, infection or patient-specific 3D reconstruction.',
                      'Figure 8 includes source biliary stent and duodenal communication; gas is not silently relabelled as microbiologically proved infection.']}
    (output/'original-figure-acquisition.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'source-article-metadata.json').write_bytes(metadata_path.read_bytes())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();acquire(a.source_root,a.output)
