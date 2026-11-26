"""Publisher-source cervical ultrasound figures for three reporting references."""
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import re
from pathlib import Path
import struct

from .source_raster_integrity import verified_raster_header

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/radiology/cervical-node-ultrasound-figures.json'
PIN = '16f590bae406d77de921be31f1283234bb03f73bec67d58a9677443edafdcc4f'
PREFIX = '/app/reference-media/radiology-open/'


@lru_cache(maxsize=1)
def catalog():
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Cervical ultrasound source registry changed')
    data = json.loads(raw)
    figures = {row['id']: row for row in data['figures']}
    if set(figures) != {key for ids in data['bindings'].values() for key in ids}:
        raise ValueError('Cervical ultrasound source bindings differ')
    directory = ROOT / 'web/reference-media/radiology-open'
    from .radiology_catalog import _validate_source_panel_roles
    for identifier, row in figures.items():
        suffix = Path(row['src']).suffix
        if (not re.fullmatch(r'[a-z0-9-]+', identifier) or suffix not in {'.png', '.webp'}
                or row['src'] != PREFIX + identifier + suffix):
            raise ValueError('Unexpected cervical ultrasound source path')
        raster = directory / (identifier + suffix)
        if any(path.is_symlink() for path in (raster, *raster.parents) if path == ROOT or ROOT in path.parents):
            raise ValueError('Cervical ultrasound source must be a regular file')
        header = verified_raster_header(row, directory, ROOT / 'data/radiology')
        if suffix == '.png' and (header[:8] != b'\x89PNG\r\n\x1a\n'
                or struct.unpack('>II', header[16:24]) != (row['width'], row['height'])):
            raise ValueError('Cervical ultrasound PNG header differs')
        if suffix == '.webp' and (header[:4] != b'RIFF' or header[8:12] != b'WEBP'):
            raise ValueError('Cervical ultrasound WebP header differs')
        _validate_source_panel_roles(row)
    return figures, data['bindings']


@lru_cache(maxsize=1)
def by_url():
    return {row['src']: row for row in catalog()[0].values()}


def references():
    figures, bindings = catalog()
    inspections = {}
    for identifier, figure in figures.items():
        inspections[identifier] = {
            'id': identifier, 'title': figure['title'], 'src': figure['src'],
            'modality': 'Published ultrasound figure', 'caption': figure['limits'],
            'source_url': figure['source_url'], 'publication_url': figure['figure_url'],
            'source_label': 'Original cervical ultrasound publication',
            'license': figure['license'], 'license_url': figure['license_url'],
            'attribution': figure['attribution'], 'photographic_figures': [figure],
            'clinical_approval': False, 'current_patient_registration': False,
            'structure_ids': [], 'requirement_coverage': [],
        }
    return {exam: [deepcopy(inspections[key]) for key in ids] for exam, ids in bindings.items()}
