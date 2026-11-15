#!/usr/bin/env python3
"""Identify re-encoded whole-figure JPEGs without modifying runtime assets."""
import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageCms
from pypdf import PdfReader


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def image_objects(resources, prefix='', depth=0):
    if depth > 8:
        raise ValueError('Unexpected nested PDF form depth')
    for name, ref in resources.get('/XObject', {}).items():
        obj = ref.get_object()
        identifier = prefix + str(name)
        if obj.get('/Subtype') == '/Image':
            yield identifier, obj
        elif obj.get('/Subtype') == '/Form':
            yield from image_objects(obj.get('/Resources', {}), identifier, depth + 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-map', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sources = json.loads(args.source_map.read_text())
    catalog = json.loads((root/'data/radiology/msk-open-images.json').read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    readers = {}
    for images in catalog.values():
        for item in images:
            url = item.get('asset_source_url','').split('?')[0]
            if (url not in sources or not item.get('source_pdf_page')
                    or item.get('source_panel') or not item['src'].endswith('.jpg')):
                continue
            path = Path(sources[url])
            if path not in readers:
                readers[path] = PdfReader(path)
            page = readers[path].pages[item['source_pdf_page']-1]
            matches = []
            for name, obj in image_objects(page['/Resources']):
                if (obj.get('/Subtype') == '/Image' and obj.get('/Width') == item['width']
                        and obj.get('/Height') == item['height'] and obj.get('/Filter') == '/DCTDecode'):
                    matches.append((name,obj))
            row = {'id':item['id'], 'source_url':url, 'source_pdf_sha256':sha(path.read_bytes()),
                   'page':item['source_pdf_page'], 'current_sha256':item['sha256']}
            if len(matches) != 1:
                row.update(status='held', reason='No unique dimension-matched direct DCT image', matches=len(matches))
            else:
                name,obj = matches[0]
                raw = obj._data
                color = obj.get('/ColorSpace')
                if hasattr(color, 'get_object'):
                    color = color.get_object()
                row.update(pdf_object=str(name), original_sha256=sha(raw), original_bytes=len(raw),
                           decode=str(obj.get('/Decode')), color_space=str(color[0]) if isinstance(color,list) else str(color),
                           has_mask=bool(obj.get('/SMask') or obj.get('/Mask')))
                current = (root/'web'/item['src'].removeprefix('/app/')).read_bytes()
                if sha(current) != item['sha256']:
                    raise ValueError('Runtime asset already changed: '+item['id'])
                original_image=Image.open(io.BytesIO(raw)); current_image=Image.open(io.BytesIO(current))
                color_known = color in ('/DeviceGray', '/DeviceRGB')
                if isinstance(color,list) and color[0] == '/ICCBased':
                    profile = color[1].get_object().get_data()
                    row['pdf_icc_profile_sha256'] = sha(profile)
                    row['pdf_icc_profile_name'] = ImageCms.getProfileName(ImageCms.ImageCmsProfile(io.BytesIO(profile))).strip()
                    row['embedded_icc_matches_pdf'] = original_image.info.get('icc_profile') == profile
                    # This exact profile was independently inspected as the
                    # standard IEC 61966-2.1 sRGB profile in the source PDFs.
                    color_known = row['embedded_icc_matches_pdf'] or sha(profile) == '2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e'
                difference=ImageChops.difference(original_image.convert('RGB'),current_image.convert('RGB'))
                row['decoded_pixels_equal']=difference.getbbox() is None
                row['max_channel_difference']=max(high for low,high in difference.getextrema())
                if obj.get('/Decode') or row['has_mask'] or original_image.mode not in ('L','RGB') or not color_known:
                    row.update(status='held',reason='PDF display semantics need separate review')
                elif raw == current:
                    row['status']='already_original'
                else:
                    row['status']='original_candidate_requires_visual_match'
                    target=args.output/(item['id']+'.jpg');target.write_bytes(raw)
                    row['candidate_file']=str(target)
            results.append(row)
            print(row['id'],row['status'],row.get('max_channel_difference'),flush=True)
    (args.output/'audit.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__ == '__main__':
    main()
