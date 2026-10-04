#!/usr/bin/env python3
"""Preserve original CBD-stone ultrasound and adjunct figures with explicit rights and independent PDF readback."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import xml.etree.ElementTree as ET

# Original PDF page, image number, object identity and actual labelled panels.
SELECTION = {
 'PMC4729712': {2:(3,24,52,dict.fromkeys('ab','CT')),3:(3,25,53,{}),4:(3,26,54,{}),5:(4,27,77,{}),6:(4,28,78,dict.fromkeys('abc','CT')),7:(5,29,97,dict.fromkeys('ab','CT')),10:(6,32,121,{})},
 'PMC10066158': {2:(4,1,54,dict.fromkeys('AB','CT')),3:(5,2,84,dict.fromkeys('AB','CT')),4:(6,3,94,dict.fromkeys('ABC','CT'))},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def acquire(root, output):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
    from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
    rows = []; articles = []
    for pmc, selected in SELECTION.items():
        meta_path = root / (pmc + '.1.json'); meta = json.loads(meta_path.read_text())
        http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
        xml = download_verified(http(meta['xml_url']), root / (pmc + '.1.xml'))
        pdf_path = root / (pmc + '.1.pdf'); pdf = download_verified(http(meta['pdf_url']), pdf_path)
        if meta['pmcid'] != pmc or meta['is_retracted'] is not False:
            raise ValueError('Original article identity/retraction differs')
        tree = ET.fromstring(xml); permissions = tree.find('.//article-meta/permissions')
        name, url = exact_license(permissions)
        if name != 'CC BY 4.0':
            raise ValueError('Source grant differs')
        article = {'pmcid': pmc, 'doi': meta['doi'], 'title': meta['title'], 'source_article_url': 'https://pmc.ncbi.nlm.nih.gov/articles/' + pmc + '/',
            'metadata_sha256': sha(meta_path.read_bytes()), 'xml_sha256': sha(xml), 'pdf_sha256': sha(pdf), 'pdf_url': http(meta['pdf_url']),
            'license': name, 'license_url': url, 'permissions_xml': ET.tostring(permissions, encoding='unicode'),
            'copyright': permissions.findtext('copyright-statement'), 'publisher_xml_pdf_md5_verified': True,
            'authors': [' '.join([n.findtext('given-names', ''), n.findtext('surname', '')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]}
        articles.append(article); reader = PdfReader(pdf_path)
        for number, (page, index, oid, types) in selected.items():
            figure = tree.find('.//fig[@id="Fig' + str(number) + '"]'); caption = ' '.join(figure.find('caption').itertext())
            if figure.find('attrib') is not None or figure.find('permissions') is not None or any(
                    s in caption.lower() for s in ['adapted', 'reproduced', 'reprinted', 'courtesy', 'provided by', '(from:']):
                raise ValueError('Unreviewed separate credit')
            filename = figure.find('graphic').get('{http://www.w3.org/1999/xlink}href')
            urls = [u for u in meta['media_urls'] if urllib.parse.urlparse(u).path.endswith('/' + filename)]
            if len(urls) != 1:
                raise ValueError('Ambiguous original media')
            media = download_verified(http(urls[0]), root / filename)
            with Image.open(io.BytesIO(media)) as im:
                dimensions = list(im.size)
            obj = reader.get_object(IndirectObject(oid, 0, reader))
            if oid not in {r.idnum for r in reader.pages[page - 1]['/Resources']['/XObject'].values()}:
                raise ValueError('Image object not on declared original page')
            jpeg = str(obj['/Filter']) == '/DCTDecode'
            prefix = 'postop-pdf' if pmc == 'PMC4729712' else 'ischemia-pdf'
            path = root / (prefix + '-' + f'{index:03d}' + ('.jpg' if jpeg else '.png')); raw = path.read_bytes()
            with Image.open(io.BytesIO(raw)) as im:
                im.load(); width, height = im.size; pixels = im.tobytes(); mode = im.mode
            if [width, height] != [obj['/Width'], obj['/Height']] or obj['/BitsPerComponent'] != 8:
                raise ValueError('Source image shape/sample interpretation differs')
            if jpeg:
                if raw != obj._data:
                    raise ValueError('Encoded JPEG stream readback differs')
                method = 'original_pdf_dct_stream_byte_identical'
            else:
                space = obj['/ColorSpace']
                if str(space[0]) != '/Indexed' or str(space[1]) != '/DeviceRGB' or obj['/Decode'] != [0, 255]:
                    raise ValueError('Unreviewed indexed PDF interpretation')
                indices = obj.get_data(); palette = space[3].get_object().get_data()
                if max(indices) > space[2] or len(palette) != 3 * (space[2] + 1):
                    raise ValueError('Original colour-table bounds differ')
                source_pixels = b''.join(palette[i * 3:i * 3 + 3] for i in indices)
                if mode != 'RGB' or pixels != source_pixels:
                    raise ValueError('PNG samples differ from independently decoded original PDF colour table')
                method = 'lossless_png_original_indexed_pdf_pixels_exact'
            rows.append({'pmcid': pmc, 'figure_number': number, 'source_figure_id':figure.get('id'), 'source_caption': caption, 'source_panel_types': types,
                'single_unlettered_figure': not types, 'source_modality':'CT', 'source_media_url': http(urls[0]), 'publisher_media_md5_verified': True,
                'repository_media_sha256': sha(media), 'repository_dimensions': dimensions, 'pdf_page': page,
                'pdf_image_index': index, 'pdf_object_id': oid, 'extracted_file': path.name, 'acquisition': method,
                'sha256': sha(raw), 'width': width, 'height': height, 'pixel_mode': mode, 'decoded_pixel_sha256': sha(pixels),
                'original_encoded_stream_or_decoded_pixel_readback_verified': True, 'source_pixels_changed': False,
                'clinical_approval': False, 'display_color_calibration_verified': False})
    holds = []
    output.mkdir(parents=True, exist_ok=True)
    (output / 'original-source-review.json').write_text(json.dumps({'articles': articles, 'figures': rows, 'rights_holds': holds,
        'clinical_approval': False, 'runtime_promoted': False}, indent=2) + '\n')
    print('Ten complete original bowel obstruction/ischemia figures verified.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); acquire(args.source_root, args.output)
