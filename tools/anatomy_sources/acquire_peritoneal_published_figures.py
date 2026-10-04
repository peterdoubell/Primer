#!/usr/bin/env python3
"""Acquire original peritoneal CT/operative composites without borrowing surgery into CT."""
import argparse,hashlib,io,json
from pathlib import Path
import urllib.parse,urllib.request
import xml.etree.ElementTree as ET

FIGURES=[3,4,8,9,11,15,16]


def acquire(root,output):
    from PIL import Image
    from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
    pmc='PMC8589944';meta_path=root/(pmc+'.1.json');meta=json.loads(meta_path.read_text());xml_path=root/(pmc+'.1.xml');xml=xml_path.read_bytes()
    expected=urllib.parse.parse_qs(urllib.parse.urlparse(meta['xml_url']).query)['md5'][0]
    if hashlib.md5(xml).hexdigest()!=expected or meta['pmcid']!=pmc or meta['is_retracted'] is not False:raise ValueError('Source XML/identity/retraction metadata differs')
    tree=ET.fromstring(xml);permissions=tree.find('.//article-meta/permissions');name,url=exact_license(permissions)
    if name!='CC BY 4.0':raise ValueError('Selected source grant differs')
    output.mkdir(parents=True,exist_ok=True);rows=[]
    for number in FIGURES:
        fig=tree.find('.//fig[@id="Fig'+str(number)+'"]');caption=' '.join(fig.find('caption').itertext())
        if fig.find('attrib') is not None or fig.find('permissions') is not None or any(v in caption.lower() for v in ['reproduced','reprinted','courtesy','(from:']):raise ValueError('Figure has unreviewed separate credit')
        file=fig.find('graphic').get('{http://www.w3.org/1999/xlink}href');links=[u for u in meta['media_urls'] if urllib.parse.urlparse(u).path.endswith('/'+file)]
        if len(links)!=1:raise ValueError('Source media missing or ambiguous')
        media_url=links[0].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/');path=root/file
        if not path.exists():path.write_bytes(urllib.request.urlopen(media_url,timeout=45).read())
        raw=path.read_bytes();md5=urllib.parse.parse_qs(urllib.parse.urlparse(media_url).query)['md5'][0]
        if hashlib.md5(raw).hexdigest()!=md5:raise ValueError('Original figure MD5 differs')
        with Image.open(io.BytesIO(raw)) as image:image.verify()
        with Image.open(io.BytesIO(raw)) as image:w,h=image.size
        rows.append({'figure_id':fig.get('id'),'figure_number':number,'source_filename':file,'source_url':media_url,'publisher_md5':md5,
                     'publisher_md5_verified':True,'sha256':hashlib.sha256(raw).hexdigest(),'width':w,'height':h,'source_caption':caption,
                     'source_panel_types':{'a':'CT','b':'Clinical photograph'},'selected_ct_panels':['a'],'source_pixels_altered':False,
                     'clinical_approval':False,'runtime_promoted':False})
        print('Original peritoneal figure',number,w,h,flush=True)
    pdf_url=meta['pdf_url'].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/');pdf=root/(pmc+'.1.pdf')
    if not pdf.exists():pdf.write_bytes(urllib.request.urlopen(pdf_url,timeout=45).read())
    pdf_md5=urllib.parse.parse_qs(urllib.parse.urlparse(pdf_url).query)['md5'][0]
    if hashlib.md5(pdf.read_bytes()).hexdigest()!=pdf_md5:raise ValueError('Original PDF MD5 differs')
    result={'pmcid':pmc,'doi':meta['doi'],'article_title':meta['title'],'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/',
            'metadata_sha256':hashlib.sha256(meta_path.read_bytes()).hexdigest(),'xml_sha256':hashlib.sha256(xml).hexdigest(),
            'permissions_xml':ET.tostring(permissions,encoding='unicode'),'license':name,'license_url':url,'source_copyright':permissions.findtext('copyright-statement'),
            'authors':[' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib/name')],
            'pdf_url':pdf_url,'pdf_publisher_md5':pdf_md5,'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'figures':rows,
            'clinical_approval':False,'limits':['Selected CT sections are not calibrated whole acquired volumes or complete peritoneal surfaces.',
            'Operative/specimen photographs preserve source correlation but cannot lend features, histology or biological 3D extent to CT panels.',
            'Source diagnosed metastases/mucinous spread are author descriptions, not independently validated grade or cytoreduction eligibility.']}
    (output/'original-source-review.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();acquire(a.source_root,a.output)
