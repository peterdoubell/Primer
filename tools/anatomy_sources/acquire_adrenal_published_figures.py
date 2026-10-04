#!/usr/bin/env python3
"""Preserve complete original adrenal figures and verify their PDF pixels/streams."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

PMCID = 'PMC6349247'
# Original PDF page, image number and object identity, checked against pdfimages.
SELECTION = {
    1: (3, 1, 62, {'a': 'CT', 'b': 'MRI', 'c': 'MRI'}),
    2: (4, 2, 85, dict.fromkeys('abcd', 'MRI')),
    3: (5, 3, 106, dict.fromkeys('ab', 'CT')),
    4: (6, 4, 133, dict.fromkeys('abc', 'MRI')),
    5: (7, 5, 151, {'a': 'CT', **dict.fromkeys('bcde', 'MRI')}),
    6: (9, 6, 213, dict.fromkeys('abc', 'MRI')),
    7: (10, 7, 233, dict.fromkeys('abc', 'CT')),
    8: (11, 8, 259, {'a': 'Ultrasound', **dict.fromkeys('bcd', 'MRI')}),
    9: (12, 9, 288, dict.fromkeys('abc', 'CT')),
    11: (14, 11, 341, {'a': 'CT', 'b': 'CT', **dict.fromkeys('cdef', 'MRI')}),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def download_verified(url, path):
    if not path.exists():
        path.write_bytes(urllib.request.urlopen(url, timeout=45).read())
    raw = path.read_bytes()
    expected = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['md5'][0]
    if hashlib.md5(raw).hexdigest() != expected:
        raise ValueError('Publisher checksum differs: ' + path.name)
    return raw


def acquire(root, output):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license

    root.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    meta_path = root / (PMCID + '.1.json')
    if not meta_path.exists():
        meta_path.write_bytes(urllib.request.urlopen(
            'https://pmc-oa-opendata.s3.amazonaws.com/' + PMCID + '.1/' + meta_path.name, timeout=45).read())
    meta = json.loads(meta_path.read_text())
    if meta['pmcid'] != PMCID or meta['is_retracted'] is not False:
        raise ValueError('Original metadata identity/retraction differs')
    http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    xml = download_verified(http(meta['xml_url']), root / (PMCID + '.1.xml'))
    pdf_path = root / (PMCID + '.1.pdf')
    pdf = download_verified(http(meta['pdf_url']), pdf_path)
    tree = ET.fromstring(xml)
    permissions = tree.find('.//article-meta/permissions')
    license_name, license_url = exact_license(permissions)
    if license_name != 'CC BY 4.0':
        raise ValueError('Selected article grant differs')
    reader = PdfReader(pdf_path)
    rows = []
    for number, (page, image_index, object_id, types) in SELECTION.items():
        fig = tree.find('.//fig[@id="Fig' + str(number) + '"]')
        caption = ' '.join(fig.find('caption').itertext())
        if fig.find('attrib') is not None or fig.find('permissions') is not None or any(
                x in caption.lower() for x in ['reproduced', 'reprinted', 'courtesy', 'provided by', '(from:']):
            raise ValueError('Unreviewed separate figure credit')
        filename = fig.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        urls = [u for u in meta['media_urls'] if urllib.parse.urlparse(u).path.endswith('/' + filename)]
        if len(urls) != 1:
            raise ValueError('Original media absent/ambiguous')
        media = download_verified(http(urls[0]), root / filename)
        with Image.open(io.BytesIO(media)) as original:
            repository_dimensions = list(original.size)
        obj = reader.get_object(IndirectObject(object_id, 0, reader))
        page_objects = reader.pages[page - 1]['/Resources']['/XObject']
        if object_id not in {ref.idnum for ref in page_objects.values()}:
            raise ValueError('Selected original image is not on the declared PDF page')
        if obj.get('/Decode') is not None or obj['/BitsPerComponent'] != 8:
            raise ValueError('Unsupported source sample interpretation')
        is_jpeg = str(obj['/Filter']) == '/DCTDecode'
        extracted = root / ('original-pdf-' + f'{image_index:03d}' + ('.jpg' if is_jpeg else '.png'))
        raw = extracted.read_bytes()
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            width, height = image.size
            pixels = image.tobytes()
            mode = image.mode
        if [width, height] != [obj['/Width'], obj['/Height']]:
            raise ValueError('Original PDF object dimensions differ')
        if is_jpeg:
            if obj._data != raw:
                raise ValueError('Original encoded JPEG stream differs from independent extraction')
            method = 'original_pdf_dct_stream_byte_identical'
        else:
            # pdfimages independently decodes the original Flate stream. The PNG
            # encoding changes the container only, retaining every image sample.
            colorspace = obj['/ColorSpace']
            expected_mode = 'L' if str(colorspace) == '/DeviceGray' else 'RGB'
            if expected_mode == 'RGB' and (str(colorspace[0]) != '/ICCBased' or colorspace[1].get_object()['/N'] != 3):
                raise ValueError('Unreviewed PDF colour space')
            if mode != expected_mode or pixels != obj.get_data():
                raise ValueError('PNG pixels differ from independently decoded original PDF samples')
            method = 'lossless_png_original_pdf_samples_exact'
        color_space = obj['/ColorSpace']
        icc = color_space[1].get_object().get_data() if isinstance(color_space, list) else None
        rows.append({'figure_number': number, 'figure_id': fig.get('id'), 'source_caption': caption,
            'source_panel_types': types, 'source_media_url': http(urls[0]), 'repository_media_sha256': sha(media),
            'repository_dimensions': repository_dimensions, 'pdf_page': page, 'pdf_image_index': image_index,
            'pdf_object_id': object_id, 'pdf_filter': str(obj['/Filter']), 'extracted_file': extracted.name,
            'sha256': sha(raw), 'width': width, 'height': height, 'pixel_mode': mode,
            'decoded_pixel_sha256': sha(pixels), 'acquisition': method,
            'source_pdf_color_space': str(color_space), 'source_pdf_icc_profile_sha256': sha(icc) if icc else None,
            'display_color_calibration_verified': False,
            'original_encoded_stream_or_decoded_sample_readback_verified': True,
            'source_pixels_changed': False, 'clinical_approval': False})
    proof = {'pmcid': PMCID, 'doi': meta['doi'], 'article_title': meta['title'],
        'source_article_url': 'https://pmc.ncbi.nlm.nih.gov/articles/' + PMCID + '/',
        'pdf_url': http(meta['pdf_url']), 'pdf_sha256': sha(pdf), 'xml_sha256': sha(xml),
        'metadata_sha256': sha(meta_path.read_bytes()), 'publisher_xml_pdf_and_media_md5_verified': True,
        'license': license_name, 'license_url': license_url,
        'permissions_xml': ET.tostring(permissions, encoding='unicode'),
        'source_copyright': permissions.findtext('copyright-statement'),
        'authors': [' '.join([n.findtext('given-names', ''), n.findtext('surname', '')])
                    for n in tree.findall('.//article-meta/contrib-group/contrib/name')],
        'figures': rows, 'excluded_figure': {'figure_number': 10,
            'reason': 'External Nuclear Medicine Service database credit needs separate reuse review.'},
        'figure2_sequence_label_ambiguity_preserved': True,
        'clinical_approval': False, 'runtime_promoted': False}
    (output / 'original-source-review.json').write_text(json.dumps(proof, indent=2) + '\n')
    print('Ten complete original adrenal figures verified; separately credited figure excluded.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    acquire(args.source_root, args.output)
