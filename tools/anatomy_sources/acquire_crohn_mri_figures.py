#!/usr/bin/env python3
"""Preserve complete native PDF Crohn MRI figures and their distinct source panels."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

SELECTION = {1: (5, 14, 65), 2: (6, 15, 85), 3: (7, 16, 97), 4: (8, 17, 109), 6: (9, 19, 116)}
PANELS = {1: {'a': 'Ultrasound', 'b': 'Ultrasound', **dict.fromkeys('cde', 'MRI')},
          2: {'a': 'Ultrasound', 'b': 'Ultrasound', 'c': 'MRI', 'd': 'MRI'},
          3: dict.fromkeys('abcdef', 'MRI'),
          4: {'a': 'MRI', 'b': 'MRI', 'c': 'CT', 'd': 'MRI', 'e': 'CT', 'f': 'Ultrasound', 'g': 'Ultrasound'},
          6: {'a': 'MRI', 'b': 'CT', 'c': 'CT', 'd': 'CT'}}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def acquire(root, output, selection=None, panel_roles=None, modality='MRI'):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
    from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
    pmc = 'PMC12634764'
    metadata = root / (pmc + '.1.json')
    meta = json.loads(metadata.read_text())
    http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    if meta['pmcid'] != pmc or meta['is_retracted'] is not False:
        raise ValueError('Source identity/retraction differs')
    xml = download_verified(http(meta['xml_url']), root / (pmc + '.1.xml'))
    pdf_path = root / (pmc + '.1.pdf')
    pdf = download_verified(http(meta['pdf_url']), pdf_path)
    tree = ET.fromstring(xml)
    permissions = tree.find('.//article-meta/permissions')
    license_name, license_url = exact_license(permissions)
    if license_name != 'CC BY 4.0':
        raise ValueError('Original grant differs')
    article = {'pmcid': pmc, 'doi': meta['doi'], 'title': meta['title'],
               'source_article_url': 'https://pmc.ncbi.nlm.nih.gov/articles/' + pmc + '/',
               'metadata_sha256': sha(metadata.read_bytes()), 'xml_sha256': sha(xml), 'pdf_sha256': sha(pdf),
               'pdf_url': http(meta['pdf_url']), 'license': license_name, 'license_url': license_url,
               'permissions_xml': ET.tostring(permissions, encoding='unicode'),
               'copyright': permissions.findtext('copyright-statement'), 'publisher_xml_pdf_md5_verified': True,
               'authors': [' '.join([n.findtext('given-names', ''), n.findtext('surname', '')])
                           for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]}
    subprocess.run(['pdfimages', '-j', str(pdf_path), str(root / 'crohn-pdf')], check=True)
    reader = PdfReader(pdf_path)
    rows = []
    selected = SELECTION if selection is None else selection
    roles = PANELS if panel_roles is None else panel_roles
    for number, (page, index, oid) in selected.items():
        figure = tree.find('.//fig[@id="Fig' + str(number) + '"]')
        caption = ' '.join(figure.find('caption').itertext())
        if figure.find('attrib') is not None or figure.find('permissions') is not None or any(
                word in caption.lower() for word in ['adapted', 'reproduced', 'reprinted', 'courtesy', 'provided by']):
            raise ValueError('Separate figure credit requires review')
        filename = figure.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        urls = [u for u in meta['media_urls'] if urllib.parse.urlparse(u).path.endswith('/' + filename)]
        if len(urls) != 1:
            raise ValueError('Original repository figure is ambiguous')
        media = download_verified(http(urls[0]), root / filename)
        with Image.open(io.BytesIO(media)) as image:
            repository_dimensions = list(image.size)
        obj = reader.get_object(IndirectObject(oid, 0, reader))
        if (oid not in {r.idnum for r in reader.pages[page - 1]['/Resources']['/XObject'].values()}
                or obj['/BitsPerComponent'] != 8 or obj.get('/SMask') is not None
                or obj.get('/Decode') not in (None, [0, 1, 0, 1, 0, 1])):
            raise ValueError('Original PDF placement or sample interpretation differs')
        prefix = root / ('crohn-pdf-' + f'{index:03d}')
        if str(obj['/Filter']) == '/DCTDecode' and str(obj['/ColorSpace']) == '/DeviceRGB':
            path = prefix.with_suffix('.jpg')
            raw = path.read_bytes()
            if raw != obj._data:
                raise ValueError('Independent encoded JPEG stream readback differs')
            mode, method = 'RGB', 'original_pdf_dct_stream_byte_identical'
        elif (str(obj['/Filter']) == '/FlateDecode' and str(obj['/ColorSpace']) == '/DeviceGray'
              and obj.get('/DecodeParms') is None and obj.get('/Decode') is None):
            samples = zlib.decompress(obj._data)
            if samples != obj.get_data() or len(samples) != obj['/Width'] * obj['/Height']:
                raise ValueError('Independent grayscale source readback differs')
            with Image.open(prefix.with_suffix('.ppm')) as independent:
                independent.load()
                channels = independent.split()
                if (independent.mode != 'RGB' or len(channels) != 3
                        or any(channel.tobytes() != samples for channel in channels)):
                    raise ValueError('Poppler grayscale samples differ')
            path = prefix.with_suffix('.png')
            Image.frombytes('L', (obj['/Width'], obj['/Height']), samples).save(path)
            raw = path.read_bytes()
            mode, method = 'L', 'lossless_png_original_pdf_gray_samples_exact'
        else:
            raise ValueError('Unreviewed source filter or colour interpretation')
        with Image.open(path) as image:
            image.load()
            if (image.mode != mode or list(image.size) != [obj['/Width'], obj['/Height']]
                    or (mode == 'L' and image.tobytes() != samples)):
                raise ValueError('Original JPEG dimensions/sample mode differs')
            pixels = image.tobytes()
            width, height = image.size
        rows.append({'pmcid': pmc, 'figure_number': number, 'source_figure_id': figure.get('id'),
                     'source_caption': caption, 'source_panel_types': roles[number], 'source_modality': modality,
                     'source_media_url': http(urls[0]), 'publisher_media_md5_verified': True,
                     'repository_media_sha256': sha(media), 'repository_dimensions': repository_dimensions,
                     'pdf_page': page, 'pdf_image_index': index, 'pdf_object_id': oid, 'extracted_file': path.name,
                     'acquisition': method, 'sha256': sha(raw),
                     'width': width, 'height': height, 'pixel_mode': mode, 'decoded_pixel_sha256': sha(pixels),
                     'original_encoded_stream_or_decoded_pixel_readback_verified': True,
                     'source_pixels_changed': False, 'clinical_approval': False, 'display_color_calibration_verified': False})
    output.mkdir(parents=True, exist_ok=True)
    (output / 'original-source-review.json').write_text(json.dumps({'articles': [article], 'figures': rows,
        'clinical_approval': False, 'runtime_promoted': False}, indent=2) + '\n')
    print(str(len(rows)) + ' complete original ' + modality + '-bearing figures verified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    acquire(args.source_root, args.output)
