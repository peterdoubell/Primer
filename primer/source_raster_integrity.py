"""Verify local rasters or build-verified hosted static metadata, without anatomical approval."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
PREFIX = '/app/reference-media/radiology-open/'

@lru_cache(maxsize=1)
def _inventory(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not isinstance(data.get('files'), dict):
        raise ValueError('Invalid verified static raster inventory')
    return data['files']

def verified_raster_header(image, root, data_dir):
    """Return actual original header bytes; hosted inventory is checked against files in release QA."""
    root = Path(root).resolve()
    src = image['src']
    prefix = '/app/reference-media/' + root.name + '/'
    if not isinstance(src, str) or not src.startswith(prefix):
        raise ValueError('Source raster must use its reviewed directory')
    path = (root / src.removeprefix(prefix)).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Source raster leaves its reviewed directory')
    if path.is_file():
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != image['sha256']:
            raise ValueError('Source raster changed after source review')
        if 'source_bytes_md5' in image and hashlib.md5(raw).hexdigest() != image['source_bytes_md5']:
            raise ValueError('Source raster MD5 changed after source review')
        return raw[:24]
    # Only the configured radiology raster CDN can use this release inventory.
    # Provenance JSON and all other source directories still require local bytes.
    if not os.environ.get('VERCEL') or prefix != PREFIX:
        raise ValueError('Source raster is missing from its reviewed directory')
    entry = _inventory(str(Path(data_dir) / 'radiology-static-rasters.json')).get(src)
    if (not isinstance(entry, dict) or entry.get('sha256') != image.get('sha256')
            or entry.get('width') != image.get('width')
            or entry.get('height') != image.get('height')
            or ('source_bytes_md5' in image and entry.get('md5') != image['source_bytes_md5'])
            or type(entry.get('bytes')) is not int or entry['bytes'] < 24):
        raise ValueError('Hosted source raster metadata differs from verified release inventory')
    try:
        header = bytes.fromhex(entry['header_hex'])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Hosted source raster header is invalid') from exc
    if len(header) != 24:
        raise ValueError('Hosted source raster header length differs')
    return header
