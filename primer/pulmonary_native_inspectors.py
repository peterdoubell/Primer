"""One complete, source-linked LIDC CT study and eight separate annotation objects."""
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re

from .pulmonary_source_delivery import (ANNOTATIONS, ANNOTATION_SOURCE_URL, LICENSE_URL,
    MANIFEST_SHA256, PREFIX, PROPOSAL_SHA256, REVIEW_SHA256, SOURCE_URL, delivery, no_approval)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/radiology/pulmonary-native-inspector.json'
REGISTRY_SHA256 = '8d91c6a85768209f66e0798074a33cda0f44a25948cb1972101b6843a5a4d44a'
AUTHORED_SHA256 = {
    'reference.html': '966b4376280e12105d48a65b1c2c65f656b065247b14353a4b97247ff680d166',
    'reference.js': 'dcdd38c3eb1234b70c233b1cd739beaa9e6b4752c4576ee1671c6f4b2c8d3da5',
    'manifest.json': MANIFEST_SHA256,
}


def _identity(row, files, name, role):
    source = files.get(PREFIX + name)
    if (not source or source['role'] != role or row.get('file') != name
            or (row.get('sha256'), row.get('bytes')) != (source['sha256'], source['bytes'])):
        raise ValueError('Native pulmonary manifest differs from exact delivery identity')


def _finite_vector(value, length):
    return (isinstance(value, list) and len(value) == length
            and all(type(v) in {int, float} and math.isfinite(v) for v in value))


def _transport(row):
    if (row.get('codec') != 'gzip' or type(row.get('decoded_bytes')) is not int
            or row['decoded_bytes'] <= 0 or not re.fullmatch(r'[a-f0-9]{64}', row.get('decoded_sha256', ''))):
        raise ValueError('Native pulmonary transport or decoded source identity changed')


@lru_cache(maxsize=1)
def references():
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError('Native pulmonary inspector differs from reviewed fingerprint')
    data = json.loads(raw)
    if (data.get('schema_version') != 1
            or data.get('bindings') != {'ra.ct-pulmonary-nodules': ['lidc-idri-0525-native']}
            or set(data.get('inspectors', {})) != {'lidc-idri-0525-native'}
            or data.get('source_proposal_sha256') != PROPOSAL_SHA256
            or data.get('independent_source_review_sha256') != REVIEW_SHA256):
        raise ValueError('Unexpected native pulmonary source or scope')
    item = data['inspectors']['lidc-idri-0525-native']
    no_approval(item)
    identity = {'id': 'lidc-idri-0525-native', 'src': PREFIX + 'reference.html',
                'manifest_url': PREFIX + 'manifest.json', 'bound_source_ids': ['lidc-idri-0525'],
                'investigation_id': 'ra.ct-pulmonary-nodules', 'module_id': 'rad.4.pulmonary-nodule',
                'source_url': SOURCE_URL, 'annotation_source_url': ANNOTATION_SOURCE_URL,
                'license': 'CC BY 3.0', 'license_url': LICENSE_URL, 'modality': 'CT',
                'publication_url': 'https://doi.org/10.1002/mp.14445',
                'independent_source_review': 'docs/pulmonary-nodule-independent-review-20261011/independent-review.json',
                'independent_source_review_sha256': REVIEW_SHA256, 'runtime_binding_added': True}
    if any(item.get(key) != value for key, value in identity.items()):
        raise ValueError('Native pulmonary source case, rights, path or approval changed')
    for field in ('title', 'caption', 'attribution'):
        if not isinstance(item.get(field), str) or not item[field].strip():
            raise ValueError('Native pulmonary inspector lacks explicit source limits or attribution')
    directory = ROOT / 'web/anatomy/lidc-idri-0525'
    for field, filename in [('sha256', 'reference.html'), ('script_sha256', 'reference.js'), ('manifest_sha256', 'manifest.json')]:
        if (item.get(field) != AUTHORED_SHA256[filename]
                or hashlib.sha256((directory / filename).read_bytes()).hexdigest() != item[field]):
            raise ValueError('Native pulmonary authored code or frozen manifest changed')
    manifest = json.loads((directory / 'manifest.json').read_bytes())
    if (manifest.get('schema_version') != 1 or manifest.get('id') != 'lidc-idri-0525'
            or manifest.get('case') != 'LIDC-IDRI-0525' or manifest.get('dataset_doi') != SOURCE_URL
            or manifest.get('annotation_doi') != ANNOTATION_SOURCE_URL
            or manifest.get('license') != 'CC BY 3.0' or manifest.get('license_url') != LICENSE_URL):
        raise ValueError('Native pulmonary source manifest scope or license changed')
    for flag in ('clinical_approval', 'fine_anatomical_approval', 'structure_coverage_granted',
                 'current_patient_registration', 'source_sample_changes', 'source_resampling',
                 'source_smoothing', 'histology_verified', 'ct_seg_coordinates_identical',
                 'lobes_or_bronchopulmonary_segments_annotated'):
        if manifest.get(flag) is not False:
            raise ValueError('Native pulmonary source cannot grant anatomy, diagnosis, registration or changed values')
    for flag in ('source_dates_deidentified_not_followup', 'source_ct_full_extent',
                 'source_xml_all_marks', 'source_seg_all_objects'):
        if manifest.get(flag) is not True:
            raise ValueError('Native pulmonary study must retain complete original extent and marks')
    files = delivery()['files']
    originals = manifest.get('original_files', [])
    expected_originals = {src.removeprefix(PREFIX) for src, row in files.items() if row['role'].startswith('unchanged-')}
    if len(originals) != 447 or {row.get('file') for row in originals} != expected_originals:
        raise ValueError('Native pulmonary original file set changed')
    for row in originals:
        name = row['file']
        _identity(row, files, name, files[PREFIX + name]['role'])
    _identity(manifest['archive_license'], files, 'LICENSE', 'source-license-or-attribution')
    ct = manifest.get('ct', {})
    if (ct.get('shape') != [512, 512, 429] or ct.get('dtype') != '<u2'
            or ct.get('source_samples') != 112459776 or ct.get('decoded_bytes') != 224919552
            or ct.get('storage_order') != 'x_fast_then_y_then_z'
            or len(ct.get('chunks', [])) != 7 or len(ct.get('slices', [])) != 429
            or len(ct.get('positions_LPS_mm', [])) != 429
            or not re.fullmatch(r'[a-f0-9]{64}', ct.get('decoded_sha256', ''))):
        raise ValueError('Complete native pulmonary CT storage or per-instance geometry changed')
    next_slice = 0
    for chunk in ct['chunks']:
        stop = min(next_slice + 64, 429)
        _identity(chunk, files, f'ct.native.{next_slice:03d}-{stop - 1:03d}.gz', 'lossless-complete-CT-chunk')
        _transport(chunk)
        if (chunk.get('first_native_slice') != next_slice or chunk.get('stop_native_slice_exclusive') != stop
                or chunk['decoded_bytes'] != (stop - next_slice) * 512 * 512 * 2):
            raise ValueError('Native pulmonary CT chunks omit or reorder original samples')
        next_slice = stop
    if len({row.get('filename') for row in ct['slices']}) != 429:
        raise ValueError('Native pulmonary CT source instances are repeated')
    for i, row in enumerate(ct['slices']):
        source = files.get(PREFIX + 'original-ct/' + row.get('filename', ''))
        if (not source or row.get('ct_slice') != i
                or (row.get('sha256'), row.get('bytes')) != (source['sha256'], source['bytes'])
                or not _finite_vector(row.get('position_LPS_mm'), 3)
                or row['position_LPS_mm'] != ct['positions_LPS_mm'][i]
                or not _finite_vector(row.get('orientation'), 6)
                or not _finite_vector(row.get('pixel_spacing_mm'), 2)
                or type(row.get('slope')) not in {int, float} or not math.isfinite(row['slope'])
                or type(row.get('intercept')) not in {int, float} or not math.isfinite(row['intercept'])):
            raise ValueError('Native pulmonary original instance, HU scaling or geometry changed')
    annotations = manifest.get('annotations', [])
    if len(annotations) != 8 or {row.get('id') for row in annotations} != ANNOTATIONS:
        raise ValueError('Native pulmonary separate original annotation objects changed')
    for annotation in annotations:
        key = annotation['id']
        for field, suffix, role in [('mask', 'mask', 'lossless-complete-released-SEG-array'),
                                    ('mesh', 'mesh', 'literal-native-SEG-boundary'),
                                    ('face_records', 'faces', 'native-SEG-face-oracle')]:
            row = annotation[field]
            _identity(row, files, key + '.' + suffix + '.gz', role)
            _transport(row)
        shape = annotation.get('source_shape')
        if (not isinstance(shape, list) or len(shape) != 3 or shape[:2] != [512, 512]
                or type(shape[2]) is not int or shape[2] <= 0
                or annotation.get('source_samples') != math.prod(shape)
                or annotation['mask']['decoded_bytes'] != math.prod(shape)
                or len(annotation.get('source_CT_slice_indices', [])) != shape[2]
                or len(annotation.get('source_frame_origins_LPS_mm', [])) != shape[2]
                or any(not _finite_vector(position, 3) for position in annotation['source_frame_origins_LPS_mm'])
                or annotation.get('source_archive') not in expected_originals
                or annotation.get('source_SR', {}).get('original_archive') not in expected_originals
                or annotation['mesh'].get('triangles') != 2 * annotation['mesh'].get('complete_exposed_faces', 0)):
            raise ValueError('Native pulmonary mask, geometry or original SEG/SR linkage changed')
    if (sum(row['mesh']['triangles'] for row in annotations) != 12568
            or sum(row['source_samples'] for row in annotations) != 19136512
            or len(manifest.get('xml_marks', [])) != 33
            or {row.get('session_index') for row in manifest['xml_marks']} != {0, 1, 2, 3}):
        raise ValueError('Native pulmonary complete cell boundaries, XML sessions or marks changed')
    return {'ra.ct-pulmonary-nodules': [item]}
