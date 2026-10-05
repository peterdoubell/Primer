#!/usr/bin/env python3
"""Preserve complete original bowel/mesenteric trauma CT artwork and repeated PDF placements."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET

SELECTION = {'PMC6780049': {1:(2,4,92,'jcm-08-01300-f001'),2:(2,5,93,'jcm-08-01300-f002'),3:(2,6,94,'jcm-08-01300-f003')},
             'PMC7676803': {1:(2,0,5,'f1-cpcem-04-620')}}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def acquire(root, output):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
    from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
    from tools.anatomy_sources.acquire_small_bowel_tumour_figures import placements
    articles, rows = [], []
    for pmc, selected in SELECTION.items():
        meta_path = root / (pmc+'.1.json'); meta = json.loads(meta_path.read_text())
        http = lambda u: u.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
        if meta['pmcid'] != pmc or meta['is_retracted'] is not False:
            raise ValueError('Original article identity/retraction differs')
        xml = download_verified(http(meta['xml_url']),root/(pmc+'.1.xml'))
        pdf_path = root/(pmc+'.1.pdf'); pdf = download_verified(http(meta['pdf_url']),pdf_path)
        tree = ET.fromstring(xml); permissions = tree.find('.//article-meta/permissions')
        name, url = exact_license(permissions)
        if name != 'CC BY 4.0':
            raise ValueError('Original commercial grant differs')
        article = {'pmcid':pmc,'doi':meta['doi'],'title':meta['title'],'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/',
                   'metadata_sha256':sha(meta_path.read_bytes()),'xml_sha256':sha(xml),'pdf_sha256':sha(pdf),'pdf_url':http(meta['pdf_url']),
                   'license':name,'license_url':url,'permissions_xml':ET.tostring(permissions,encoding='unicode'),
                   'copyright':permissions.findtext('copyright-statement'),'publisher_xml_pdf_md5_verified':True,
                   'authors':[' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]}
        articles.append(article); reader = PdfReader(pdf_path); prefix = pmc.lower()+'-pdf'
        subprocess.run(['pdfimages','-j',str(pdf_path),str(root/prefix)],check=True)
        for number,(page,index,oid,fid) in selected.items():
            figure = tree.find('.//fig[@id="'+fid+'"]'); caption = ' '.join(figure.find('caption').itertext())
            if figure.find('attrib') is not None or figure.find('permissions') is not None or any(w in caption.lower() for w in ['adapted','reproduced','reprinted','courtesy','provided by']):
                raise ValueError('Unreviewed separate image credit')
            filename = figure.find('graphic').get('{http://www.w3.org/1999/xlink}href'); links = [u for u in meta['media_urls'] if urllib.parse.urlparse(u).path.endswith('/'+filename)]
            if len(links) != 1:
                raise ValueError('Original repository image ambiguous')
            media = download_verified(http(links[0]),root/filename)
            with Image.open(io.BytesIO(media)) as image:
                dimensions = list(image.size)
            obj = reader.get_object(IndirectObject(oid,0,reader))
            source_placements = [p for p in placements(reader,page) if p['pdf_object_id'] == oid]
            if (not source_placements
                    or str(obj['/Filter']) != '/DCTDecode' or str(obj['/ColorSpace']) != '/DeviceRGB'
                    or obj['/BitsPerComponent'] != 8 or obj.get('/Decode') is not None or obj.get('/SMask') is not None):
                raise ValueError('Original source placement/sample interpretation differs')
            path = root/(prefix+'-'+f'{index:03d}'+'.jpg'); raw = path.read_bytes()
            if raw != obj._data:
                raise ValueError('Independent encoded JPEG readback differs')
            with Image.open(path) as image:
                image.load()
                if image.mode != 'RGB' or image.size != (obj['/Width'],obj['/Height']):
                    raise ValueError('Original image shape/pixel mode differs')
                pixels = image.tobytes(); width,height = image.size
            repeats = []
            if pmc == 'PMC6780049':
                # The publication repeats the same artwork; retain all source
                # object placements without counting them as independent cases.
                for duplicate_id in {1:[120,141],2:[121,142],3:[122,143]}[number]:
                    duplicate = reader.get_object(IndirectObject(duplicate_id,0,reader))
                    if duplicate._data != raw:
                        raise ValueError('Repeated original artwork differs')
                    repeats.append(duplicate_id)
            rows.append({'pmcid':pmc,'figure_number':number,'source_figure_id':fid,'source_caption':caption,
                         'source_panel_types':dict.fromkeys('AB','CT') if pmc=='PMC6780049' else {},'source_modality':'CT',
                         'source_media_url':http(links[0]),'publisher_media_md5_verified':True,'repository_media_sha256':sha(media),'repository_dimensions':dimensions,
                         'pdf_page':page,'pdf_image_index':index,'pdf_object_id':oid,'repeated_same_artwork_pdf_object_ids':repeats,
                         'original_pdf_placements':source_placements,
                         'extracted_file':path.name,'acquisition':'original_pdf_dct_stream_byte_identical','sha256':sha(raw),'width':width,'height':height,'pixel_mode':'RGB',
                         'decoded_pixel_sha256':sha(pixels),'original_encoded_stream_or_decoded_pixel_readback_verified':True,
                         'source_pixels_changed':False,'clinical_approval':False,'display_color_calibration_verified':False})
    output.mkdir(parents=True,exist_ok=True)
    (output/'original-source-review.json').write_text(json.dumps({'articles':articles,'figures':rows,
        'rights_holds':[{'pmcid':'PMC10157329','reason':'Original CC BY-NC 4.0 grant does not clear commercial image reuse.','runtime_promoted':False}],
        'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')
    print('Four complete original bowel-trauma figures verified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); acquire(args.source_root,args.output)
