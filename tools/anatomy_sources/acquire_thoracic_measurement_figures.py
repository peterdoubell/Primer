#!/usr/bin/env python3
"""Preserve complete original publisher measurement figures without CMYK recomposition or pixel edits."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
from PIL import Image
from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'docs/thoracic-measurement-published-source-review'
METADATA_SHA='e3d77290bfba4e77154b0ba3275e3469cd633571db730a72abee1d6c4d0f1241'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def acquire(root):
    root.mkdir(parents=True,exist_ok=True);metadata=root/'PMC3874367.1.json'
    if not metadata.exists():
        with urllib.request.urlopen('https://pmc-oa-opendata.s3.amazonaws.com/PMC3874367.1/PMC3874367.1.json',timeout=60) as r:metadata.write_bytes(r.read())
    if sha(metadata.read_bytes())!=METADATA_SHA:raise ValueError('Reviewed metadata differs')
    m=json.loads(metadata.read_text());http=lambda u:u.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
    if m['is_retracted'] is not False:raise ValueError('Source retraction status differs')
    xml=download_verified(http(m['xml_url']),root/'PMC3874367.1.xml');tree=ET.fromstring(xml)
    permissions=tree.find('.//article-meta/permissions');name,url=exact_license(permissions)
    if name!='CC BY 3.0':raise ValueError('Original grant differs')
    rows=[]
    for number in [1,2,3]:
        figure=tree.find('.//fig[@id="fig'+str(number)+'"]');caption=' '.join(figure.find('caption').itertext())
        if figure.find('attrib') is not None or figure.find('permissions') is not None or any(w in caption.lower() for w in ['adapted','reprinted','reproduced','courtesy']):raise ValueError('Separate source credit needs review')
        filename=figure.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        media=next(u for u in m['media_urls'] if '/'+filename+'?' in u);raw=download_verified(http(media),root/filename)
        with Image.open(root/filename) as image:
            image.load();pixels=image.tobytes();profile=image.info.get('icc_profile')
            rows.append({'figure_number':number,'source_figure_id':figure.get('id'),'source_caption':caption,
                'original_filename':filename,'source_media_url':http(media),'publisher_media_md5_verified':True,
                'sha256':sha(raw),'width':image.width,'height':image.height,'pixel_mode':image.mode,
                'decoded_pixel_sha256':sha(pixels),'source_icc_sha256':sha(profile) if profile else None,
                'method':'original_publisher_complete_jpeg_byte_identical','source_pixels_changed':False,
                'source_modality':'MRI' if number==3 else 'CT','clinical_approval':False})
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/'original-source-review.json').write_text(json.dumps({'pmcid':m['pmcid'],'doi':m['doi'],'title':m['title'],
        'metadata_sha256':METADATA_SHA,'xml_sha256':sha(xml),'original_license':name,'original_license_url':url,
        'permissions_xml':ET.tostring(permissions,encoding='unicode'),'copyright':permissions.findtext('copyright-statement'),
        'authors':[' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')],
        'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC3874367/','figures':rows,
        'source_pixels_changed':False,'clinical_approval':False,'model_promoted':False},indent=2)+'\n')
    print('Three complete publisher CT/MRI JPEG figures and original CC BY 3.0 grant verified.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    acquire(p.parse_args().source_root)
