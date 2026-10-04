#!/usr/bin/env python3
"""Preserve complete original bowel-wall CT figures and grayscale samples with actual CC BY 2.0 attribution."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import xml.etree.ElementTree as ET

# Original PDF page, image number, object identity and actual labelled panels.
SELECTION = {'PMC3999365': {
 6:(6,5,105,{}),9:(7,8,129,dict.fromkeys('ab','CT')),
 12:(8,11,167,{}),13:(9,12,189,{}),14:(9,13,190,{}),15:(10,14,198,{}),
 17:(10,16,200,{}),18:(10,17,201,{}),20:(11,19,209,dict.fromkeys('ab','CT')),
 22:(12,21,233,dict.fromkeys('ab','CT')),
}}



def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def acquire(root, output, selection=None):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
    from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
    rows = []; articles = []
    for pmc, selected in (SELECTION if selection is None else selection).items():
        meta_path = root / (pmc + '.1.json'); meta = json.loads(meta_path.read_text())
        http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
        xml = download_verified(http(meta['xml_url']), root / (pmc + '.1.xml'))
        pdf_path = root / (pmc + '.1.pdf'); pdf = download_verified(http(meta['pdf_url']), pdf_path)
        if meta['pmcid'] != pmc or meta['is_retracted'] is not False:
            raise ValueError('Original article identity/retraction differs')
        tree = ET.fromstring(xml)
        if tree.findtext('.//article-id[@pub-id-type="doi"]') != meta['doi']:
            raise ValueError('Original XML/metadata DOI differs')
        permissions = tree.find('.//article-meta/permissions')
        name, url = exact_license(permissions)
        if name != 'CC BY 2.0':
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
            if str(obj['/ColorSpace']) != '/DeviceGray' or obj.get('/Decode', [0, 1]) != [0, 1] or obj.get('/SMask') is not None:
                raise ValueError('Selected source grayscale/mask interpretation differs')
            jpeg = str(obj['/Filter']) == '/DCTDecode'
            prefix = 'wall-pdf'
            path = root / (prefix + '-' + f'{index:03d}' + ('.jpg' if jpeg else '.png'))
            if not jpeg and not path.exists():
                if str(obj['/ColorSpace']) != '/DeviceGray' or str(obj['/Filter']) != '/FlateDecode':
                    raise ValueError('Unreviewed original PDF samples')
                Image.frombytes('L', (obj['/Width'], obj['/Height']), obj.get_data()).save(path)
            raw = path.read_bytes()
            with Image.open(io.BytesIO(raw)) as im:
                im.load(); width, height = im.size; pixels = im.tobytes(); mode = im.mode
            if [width, height] != [obj['/Width'], obj['/Height']] or obj['/BitsPerComponent'] != 8:
                raise ValueError('Source image shape/sample interpretation differs')
            if jpeg:
                if raw != obj._data:
                    raise ValueError('Encoded JPEG stream readback differs')
                method = 'original_pdf_dct_stream_byte_identical'
            else:
                if str(obj['/ColorSpace']) != '/DeviceGray' or str(obj['/Filter']) != '/FlateDecode' or obj.get('/Decode', [0, 1]) != [0, 1] or obj.get('/SMask') is not None:
                    raise ValueError('Unreviewed grayscale PDF interpretation')
                source_pixels = obj.get_data()
                with Image.open(root / (prefix + '-' + f'{index:03d}' + '.ppm')) as independent:
                    samples = independent.tobytes()
                    if independent.mode != 'RGB' or independent.size != (width, height) or samples[::3] != source_pixels or samples[1::3] != source_pixels or samples[2::3] != source_pixels:
                        raise ValueError('Independent Poppler grayscale readback differs')
                if mode != 'L' or pixels != source_pixels:
                    raise ValueError('PNG samples differ from independently decoded original grayscale PDF stream')
                method = 'lossless_png_original_devicegray_pdf_samples_exact'
            rows.append({'pmcid': pmc, 'figure_number': number, 'source_figure_id':figure.get('id'), 'source_caption': caption, 'source_panel_types': types,
                'single_unlettered_figure': not types, 'source_modality':'CT', 'source_media_url': http(urls[0]), 'publisher_media_md5_verified': True,
                'repository_media_sha256': sha(media), 'repository_dimensions': dimensions, 'pdf_page': page,
                'pdf_image_index': index, 'pdf_object_id': oid, 'extracted_file': path.name, 'acquisition': method,
                'sha256': sha(raw), 'width': width, 'height': height, 'pixel_mode': mode, 'decoded_pixel_sha256': sha(pixels),
                'original_encoded_stream_or_decoded_pixel_readback_verified': True, 'source_pixels_changed': False,
                'clinical_approval': False, 'display_color_calibration_verified': False})
    holds = []
    for number in [1,2,3,4,5,7,8,10,11,16,19,21]:
        fig = tree.find('.//fig[@id="Fig' + str(number) + '"]')
        holds.append({'pmcid': 'PMC3999365', 'figure_number': number,
            'source_caption': ' '.join(fig.find('caption').itertext()),
            'reason': 'Separate earlier-poster adaptation credit requires source-specific reuse evidence; not declared unlicensed.',
            'credited_source_doi': '10.5444/esgar2011/EE-063',
            'resolver_observation': 'DOI redirected to abstracts.webges.com; that host failed DNS resolution during 2026-10-04 review.',
            'runtime_promoted': False})
    output.mkdir(parents=True, exist_ok=True)
    (output / 'original-source-review.json').write_text(json.dumps({'articles': articles, 'figures': rows, 'rights_holds': holds,
        'clinical_approval': False, 'runtime_promoted': False}, indent=2) + '\n')
    print(str(len(rows)) + ' complete original bowel CT figures verified.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); acquire(args.source_root, args.output)
