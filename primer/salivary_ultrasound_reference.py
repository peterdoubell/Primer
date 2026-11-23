"""Publisher salivary ultrasound photographs, with no inferred side or volume."""
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import struct

from .source_raster_integrity import verified_raster_header

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/radiology/salivary-ultrasound-figures.json'
PIN = '75928af719d06d5cfa8ecdecbcafb763ade72254acca8fd56c3173b9d71c5a39'
NECK = 'us.soft-tissue-neck'
IDENTIFIER = 'salivary-us-2025'
SRC = '/app/reference-media/radiology-open/salivary-ultrasound-2025-figure3.png'


@lru_cache(maxsize=1)
def figures():
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Salivary source figure registry changed')
    data = json.loads(raw)
    if (data['case_id'] != IDENTIFIER or data['reporting_id'] != NECK
            or data['source_doi'] != '10.1007/s11926-025-01186-9' or len(data['figures']) != 1):
        raise ValueError('Salivary source scope changed')
    figure, = data['figures']
    context = figure['source_context']
    panels = context['panels']
    if (figure['src'] != SRC or figure['modality'] != 'Ultrasound'
            or (figure['width'], figure['height']) != (2056, 685)
            or figure['license'] != 'CC BY 4.0'
            or figure['license_url'] != 'https://creativecommons.org/licenses/by/4.0/'
            or any(figure.get(flag) is not False for flag in
                   ['clinical_approval', 'fine_anatomical_approval', 'structure_coverage_granted'])
            or [row['id'] for row in panels] != ['A', 'A_prime', 'A_double_prime', 'B', 'B_prime', 'B_double_prime']
            or [row['gland'] for row in panels] != ['parotid'] * 3 + ['submandibular'] * 3
            or [row['id'] for row in panels if row['source_state'] == 'healthy-subject example'] != ['A', 'B']
            or any(row['side'] != 'not reported' or row['acquisition_plane'] != 'not reported' for row in panels)
            or any(context.get(flag) is not False for flag in
                   ['source_case_pairing_verified', 'source_time_series', 'native_coordinates_available', 'source_pixel_calibration_available'])):
        raise ValueError('Salivary source identity or interpretation changed')
    path = ROOT / 'web/reference-media/radiology-open' / SRC.rsplit('/', 1)[1]
    if any(p.is_symlink() for p in [path, *path.parents] if p == ROOT or ROOT in p.parents):
        raise ValueError('Salivary source must be a regular file')
    header = verified_raster_header(figure, path.parent, ROOT / 'data/radiology')
    if header[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', header[16:24]) != (2056, 685):
        raise ValueError('Salivary source dimensions changed')
    from .radiology_catalog import _validate_source_panel_roles
    _validate_source_panel_roles(figure)
    return data['figures']


def references():
    photos = deepcopy(figures())
    figure, = photos
    return {NECK: [{
        'id': IDENTIFIER, 'modality': 'Ultrasound photographs',
        'title': 'Healthy-subject salivary gland ultrasound examples',
        'src': SRC,
        'caption': ('Compare the publisher’s healthy-subject parotid and submandibular examples '
                    'with separate Sjögren disease panels. Side and acquisition plane are not reported. '
                    'These are static publication images, separate from the tracked thyroid study.'),
        'source_url': figure['source_url'], 'publication_url': figure['source_url'],
        'source_label': 'Original salivary ultrasound publication',
        'license': figure['license'], 'license_url': figure['license_url'],
        'attribution': figure['attribution'], 'photographic_figures': photos,
        'clinical_approval': False, 'fine_anatomical_approval': False,
        'current_patient_registration': False, 'normal_anatomical_atlas_approval': False,
        'complete_reporting_anatomy_approved': False,
        'structure_ids': [], 'requirement_coverage': [],
    }]}
