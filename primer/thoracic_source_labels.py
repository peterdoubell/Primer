"""Pinned publisher-image locators; no tissue segmentation or clinical approval."""
import hashlib
import copy
import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
PREFIX = '/app/source-labels/thoracic/'
REGISTRY_SHA = 'a477565e10641bc50ecb29d5777b7921316c9ba0f26f06996af17eed22f07418'


@lru_cache(maxsize=1)
def registry():
    raw = (ROOT / 'data/radiology/thoracic-source-label-delivery.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA:
        raise ValueError('Source-label delivery registry changed')
    data = json.loads(raw)
    if data.get('schema_version') != 1 or len(data.get('files', {})) != 9:
        raise ValueError('Source-label delivery scope changed')
    return data


def validate_file(asset):
    row = registry()['files'].get(asset)
    if row is None:
        raise ValueError('Unknown source-label asset')
    path = ROOT / 'web/source-labels/thoracic' / asset
    if path.is_symlink() or not path.is_file():
        raise ValueError('Original source-label file missing or irregular')
    raw = path.read_bytes()
    if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise ValueError('Original source-label file changed')
    return path


@lru_cache(maxsize=1)
def references():
    for asset in registry()['files']:
        validate_file(asset)
    manifest = json.loads(validate_file('manifest.json').read_text())
    if (manifest.get('investigation_id') != 'ra.thoracic-ultrasound'
            or len(manifest.get('images', [])) != 6
            or sum(len(r['locations']) for r in manifest['images']) != 27
            or any(manifest.get(k) is not False for k in ['clinical_approval', 'structure_coverage_granted',
                                                        'three_dimensional_registration', 'original_images_modified'])):
        raise ValueError('Source-label correspondence scope changed')
    result = {}
    for row in manifest['images']:
        if (row['file'] != 'assets/' + row['id']
                or row['sha256'] != registry()['files'][row['file']]['sha256']):
            raise ValueError('Source-label figure identity changed')
        for loc in row['locations']:
            x, y, w, h = loc['rect']
            if (not all(type(v) is int for v in [x, y, w, h]) or min(x, y) < 0
                    or min(w, h) <= 0 or x+w > row['dimensions'][0] or y+h > row['dimensions'][1]
                    or loc['segmented_tissue_boundary'] is not False):
                raise ValueError('Source locator leaves its original pixel grid')
        result['/app/reference-media/radiology-open/thoracic-us-' + row['id']] = {
            'src': PREFIX + 'index.html?' + urlencode({'figure': row['id']}),
            'figure_id': row['id'], 'figure_sha256': row['sha256'],
            'dimensions': row['dimensions'], 'locator_count': len(row['locations']),
            'clinical_approval': False, 'tissue_segmentation': False, 'three_dimensional_registration': False,
        }
    return result


def bind_images(investigation, images):
    if investigation != 'ra.thoracic-ultrasound':
        return
    refs = references()
    matched = 0
    for image in images:
        ref = refs.get(image['src'])
        if ref is None:
            continue
        if image['sha256'] != ref['figure_sha256'] or [image['width'], image['height']] != ref['dimensions']:
            raise ValueError('Locator does not match this original source figure')
        image['source_label_locator'] = copy.deepcopy(ref)
        matched += 1
    if matched != 6:
        raise ValueError('A source-label figure binding is missing')
