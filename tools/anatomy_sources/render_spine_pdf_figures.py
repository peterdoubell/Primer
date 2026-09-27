#!/usr/bin/env python3
"""Render two complete annotated figures from the reviewed ABCs spine PDF.

This creates derived figure renders, not unchanged original-image assets.
It does not edit the PDF, image catalog, evidence ledger, or runtime assets.
Requires Poppler pdftoppm, pypdf and Pillow. See --help for reproducible usage.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageCms
from pypdf import PdfReader
from pypdf.generic import ContentStream


EXPECTED_PDF_SHA256 = 'affa1a6dc547a274a3d220b5c2aa956aaabba086e78e966273ad7e7ee7b0fe07'
SOURCE_URL = ('https://pmc-oa-opendata.s3.amazonaws.com/PMC5893484.1/'
              'PMC5893484.1.pdf?md5=ba4dd5a19b9cd29f16301f30bb1b68ef')
DPI = 300
FIGURES = (
    dict(number=1, page=2, names=['/Im1'],
         roi=[225, 50, 550, 260], crop=[964, 224, 2273, 1068],
         filename='spine-functional-unit-kushchayev-fig1-pdf-render.png',
         original='abcs-fig1.png'),
    dict(number=26, page=16, names=['/Im1', '/Im2', '/Im3'],
         roi=[175, 570, 550, 720], crop=[739, 2384, 2273, 2967],
         filename='spine-ligamentum-flavum-kushchayev-fig26-pdf-render.png',
         original='abcs-fig26.png'),
)
IDENTITY = (1, 0, 0, 1, 0, 0)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compose(parent, child):
    a, b, c, d, e, f = parent
    g, h, i, j, k, l = child
    return (a*g+c*h, b*g+d*h, a*i+c*j, b*i+d*j,
            a*k+c*l+e, b*k+d*l+f)


def point(matrix, x, y):
    a, b, c, d, e, f = matrix
    return (a*x+c*y+e, b*x+d*y+f)


def top_left_bounds(points, height):
    xs, ys = zip(*points)
    return [min(xs), height-max(ys), max(xs), height-min(ys)]


def intersects(left, right):
    return (left[0] < right[2] and left[2] > right[0]
            and left[1] < right[3] and left[3] > right[1])


def contains(outer, inner):
    return (outer[0] <= inner[0] and outer[1] <= inner[1]
            and outer[2] >= inner[2] and outer[3] >= inner[3])


def page_objects(reader, page):
    """Record placed rasters and painted vector paths, including nested forms.

    Cubic control points give conservative path bounds. These are an audit of
    vector placement, not a replacement for Poppler's PDF rendering or clipping.
    """
    height = float(page.mediabox.height)
    images, vectors, forms = [], [], []

    def walk(stream, resources, matrix=IDENTITY, prefix='', ancestors=()):
        stack, path = [], []
        objects = resources.get('/XObject', {}).get_object() if resources.get('/XObject') else {}
        for operands, operation in ContentStream(stream, reader).operations:
            if operation == b'q':
                stack.append(matrix)
            elif operation == b'Q':
                matrix = stack.pop()
            elif operation == b'cm':
                matrix = compose(matrix, tuple(float(n) for n in operands))
            elif operation == b'm':
                # PDF paths may have multiple subpaths before one paint operation.
                path.append(point(matrix, float(operands[0]), float(operands[1])))
            elif operation == b'l':
                path.append(point(matrix, float(operands[0]), float(operands[1])))
            elif operation in (b'c', b'v', b'y'):
                path.extend(point(matrix, float(operands[n]), float(operands[n+1]))
                            for n in range(0, len(operands), 2))
            elif operation == b're':
                x, y, w, h = map(float, operands)
                path.extend(point(matrix, px, py)
                            for px, py in ((x, y), (x+w, y), (x+w, y+h), (x, y+h)))
            elif operation in (b'S', b's', b'f', b'F', b'f*', b'B', b'B*', b'b', b'b*'):
                if path:
                    vectors.append({'operator': operation.decode(),
                                    'bounds_points_top_left': top_left_bounds(path, height),
                                    'resource_path': prefix or '/page'})
                path = []
            elif operation == b'n':
                path = []
            elif operation == b'Do':
                name = str(operands[0])
                reference = objects[operands[0]]
                obj = reference.get_object()
                object_id = getattr(obj.indirect_reference, 'idnum', None)
                resource_path = prefix + name
                if obj.get('/Subtype') == '/Image':
                    corners = [point(matrix, x, y) for x, y in ((0, 0), (1, 0), (1, 1), (0, 1))]
                    displayed_width = math.hypot(matrix[0], matrix[1])
                    displayed_height = math.hypot(matrix[2], matrix[3])
                    width, image_height = int(obj['/Width']), int(obj['/Height'])
                    ppi = [width*72/displayed_width, image_height*72/displayed_height]
                    images.append(dict(resource_path=resource_path, object_id=object_id,
                        native_pixels=[width, image_height], matrix=list(matrix),
                        bounds_points_top_left=top_left_bounds(corners, height),
                        native_effective_ppi=ppi,
                        rendered_pixels_per_source_pixel=[DPI/v for v in ppi],
                        filter=str(obj.get('/Filter')),
                        raw_stream_sha256=digest(obj._data),
                        decode_array=obj.get('/Decode'),
                        has_soft_mask='/SMask' in obj, has_mask='/Mask' in obj))
                elif obj.get('/Subtype') == '/Form':
                    if object_id in ancestors:
                        raise ValueError('Recursive PDF form')
                    forms.append(resource_path)
                    form_matrix = tuple(float(n) for n in obj.get('/Matrix', IDENTITY))
                    walk(obj, obj.get('/Resources', resources), compose(matrix, form_matrix),
                         resource_path+'/', ancestors+(object_id,))

    walk(page.get_contents(), page['/Resources'])
    return images, vectors, forms


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pdf', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--publisher-originals-dir', required=True, type=Path,
                        help='Directory containing unchanged abcs-fig1.png and abcs-fig26.png')
    args = parser.parse_args()
    source = args.source_pdf.resolve()
    if digest(source.read_bytes()) != EXPECTED_PDF_SHA256:
        raise ValueError('Source PDF fingerprint differs; page/figure bounds require re-review')
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    renderer = shutil.which('pdftoppm')
    text_tool = shutil.which('pdftotext')
    if not renderer or not text_tool:
        raise RuntimeError('Poppler pdftoppm and pdftotext are required')
    version = subprocess.run([renderer, '-v'], capture_output=True, text=True, check=True)
    reader = PdfReader(source)
    profile_ref = reader.pages[1]['/Resources']['/XObject']['/Im1']['/ColorSpace'][1]
    profile = profile_ref.get_object().get_data()
    profile_name = ImageCms.getProfileName(ImageCms.ImageCmsProfile(io.BytesIO(profile))).strip()
    if 'sRGB' not in profile_name or profile_ref.get_object().get('/N') != 3:
        raise ValueError('Reviewed source RGB color interpretation has changed')
    profile_path = output/'source-rgb-profile.icc'
    profile_path.write_bytes(profile)
    metadata = dict(source_pdf=str(source), source_url=SOURCE_URL,
        source_pdf_sha256=EXPECTED_PDF_SHA256, rendering_dpi=DPI,
        renderer=renderer, renderer_version=(version.stderr or version.stdout).strip(),
        color_interpretation=dict(profile=profile_name, sha256=digest(profile),
            method='Poppler honors PDF source color and renders into its embedded sRGB profile.'),
        artifact_type='derived complete-figure PDF renders; not original standalone source images',
        post_render_resampling=False, figures=[])
    for figure in FIGURES:
        page = reader.pages[figure['page']-1]
        if page.get('/Rotate', 0) != 0 or float(page.get('/UserUnit', 1)) != 1:
            raise ValueError('Unexpected page transform')
        images, vectors, forms = page_objects(reader, page)
        selected = [im for im in images if im['resource_path'] in figure['names']]
        if len(selected) != len(figure['names']):
            raise ValueError('Source image objects no longer match the reviewed figure')
        if any(ppi > DPI for im in selected for ppi in im['native_effective_ppi']):
            raise ValueError('Rendering would undersample embedded source detail')
        # Source placement rounding is <0.04%; do not pass off a larger raster
        # than this as newly created MRI resolution or a super-resolution image.
        if any(abs(scale-1) > 0.001 for im in selected for scale in im['rendered_pixels_per_source_pixel']):
            raise ValueError('Sampling departs from reviewed near-1:1 source placement')
        prefix = output/f'page-{figure["page"]:02d}-full-300dpi'
        command = [renderer, '-f', str(figure['page']), '-l', str(figure['page']),
                   '-singlefile', '-r', str(DPI), '-png', '-displayprofile', str(profile_path),
                   str(source), str(prefix)]
        subprocess.run(command, check=True, capture_output=True)
        full_path = prefix.with_suffix('.png')
        with Image.open(full_path) as full:
            full.load()
            cropped = full.convert('RGB').crop(tuple(figure['crop']))
            target = output/figure['filename']
            cropped.save(target, dpi=(DPI, DPI), icc_profile=profile)
            with Image.open(target) as saved:
                saved.load()
                if saved.tobytes() != cropped.tobytes():
                    raise ValueError('PNG save altered rendered crop pixels')
            full_dimensions = list(full.size)
        point_bounds = [v*72/DPI for v in figure['crop']]
        drawn = [v for v in vectors if intersects(v['bounds_points_top_left'], figure['roi'])]
        text_boxes_path = output/f'page-{figure["page"]:02d}-words.html'
        subprocess.run([text_tool, '-f', str(figure['page']), '-l', str(figure['page']),
                        '-bbox', '-enc', 'UTF-8', str(source), str(text_boxes_path)],
                       check=True, capture_output=True)
        words = []
        for word in ET.parse(text_boxes_path).findall('.//{http://www.w3.org/1999/xhtml}word'):
            box = [float(word.attrib[key]) for key in ('xMin', 'yMin', 'xMax', 'yMax')]
            if intersects(box, figure['roi']):
                words.append({'text': word.text, 'bounds_points_top_left': box})
        for item in selected + drawn + words:
            if not contains(point_bounds, item['bounds_points_top_left']):
                raise ValueError('Figure crop clips a source image, vector mark or text item')
        vector_path = output/f'figure-{figure["number"]}-vector-positions.json'
        vector_path.write_text(json.dumps(drawn, indent=2)+'\n')
        original = args.publisher_originals_dir/figure['original']
        archived_original = output/('publisher-original-'+figure['original'])
        shutil.copyfile(original, archived_original)
        with Image.open(original) as old:
            old.load()
            original_dimensions = list(old.size)
        metadata['figures'].append(dict(figure_number=figure['number'],
            source_pdf_page=figure['page'], source_page_label=254 if figure['page']==2 else 268,
            source_page_size_points=[float(page.mediabox.width), float(page.mediabox.height)],
            layout_search_roi_points_top_left=figure['roi'], crop_bbox_pixels=figure['crop'],
            crop_bbox_points_top_left=point_bounds,
            crop_bbox_points_pdf_bottom_left=[point_bounds[0], float(page.mediabox.height)-point_bounds[3],
                point_bounds[2], float(page.mediabox.height)-point_bounds[1]],
            crop_selection='Reviewed isolated figure content plus 5-pixel white margin; captions/body excluded.',
            embedded_images=selected, nested_form_paths=forms,
            painted_vector_paths_intersecting_figure=len(drawn), vector_positions_file=str(vector_path),
            text_words_in_figure=words, text_positions_file=str(text_boxes_path),
            source_image_vector_and_text_bounds_contained=True,
            full_page_render=dict(path=str(full_path), pixels=full_dimensions, sha256=digest(full_path.read_bytes())),
            rendered_figure=dict(path=str(target), pixels=list(cropped.size), sha256=digest(target.read_bytes()),
                bytes=target.stat().st_size, decoded_pixels_sha256=digest(cropped.tobytes())),
            publisher_original=dict(path=str(archived_original), pixels=original_dimensions,
                sha256=digest(original.read_bytes())), render_command=command))
    (output/'render-metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps([{'figure':f['figure_number'], **f['rendered_figure']} for f in metadata['figures']], indent=2))


if __name__ == '__main__':
    main()
