"""One reviewed SOOP source case, with complete arrays and three separate mask boundaries."""
import hashlib
import json
import math
import re
from functools import lru_cache
from pathlib import Path

from .stroke_source_delivery import NATIVE_PREFIX, SOOP_REVIEW_SHA256, delivery, _no_approval

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/radiology/soop-native-inspector.json'
REGISTRY_SHA256 = '449ac4b15f9b9104bb35da36e2441571bca458a8947b874eeb1b87034b39c13e'
PROPOSAL_SHA256 = '640b646f74ba254aa4e4f864e643bd9462b52429ee79849be22ffe131cd1cd2d'
SOURCE_URL = 'https://doi.org/10.18112/openneuro.ds004889.v1.1.2'
ARRAYS = {'trace', 'adc', 't1', 'flair', 'acute', 'chronic', 'combined'}
MASKS = {'acute', 'chronic', 'combined'}
ORIGINAL_NAMES = {'sub-342_rec-TRACE_dwi.nii.gz', 'sub-342_rec-TRACE_dwi.json',
                  'sub-342_rec-ADC_dwi.nii.gz', 'sub-342_rec-ADC_dwi.json',
                  'sub-342_T1w.nii.gz', 'sub-342_T1w.json', 'sub-342_FLAIR.nii.gz', 'sub-342_FLAIR.json',
                  'sub-342_space-TRACE_desc-lesionAcute_mask.nii.gz',
                  'sub-342_space-TRACE_desc-lesionChronic_mask.nii.gz',
                  'sub-342_space-TRACE_desc-lesion_mask.nii.gz'}
ORIGINAL_BY_ARRAY = {'trace': 'sub-342_rec-TRACE_dwi.nii.gz', 'adc': 'sub-342_rec-ADC_dwi.nii.gz',
                     't1': 'sub-342_T1w.nii.gz', 'flair': 'sub-342_FLAIR.nii.gz',
                     'acute': 'sub-342_space-TRACE_desc-lesionAcute_mask.nii.gz',
                     'chronic': 'sub-342_space-TRACE_desc-lesionChronic_mask.nii.gz',
                     'combined': 'sub-342_space-TRACE_desc-lesion_mask.nii.gz'}


def _identity(row, published, expected_src, role):
    source = published.get(expected_src)
    if (not source or source['role'] != role or row.get('file') != expected_src
            or (row.get('sha256'), row.get('bytes')) != (source['sha256'], source['bytes'])):
        raise ValueError('Native stroke manifest differs from its reviewed delivery identity')


@lru_cache(maxsize=1)
def references():
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError('Native stroke inspector differs from reviewed fingerprint')
    data = json.loads(raw)
    if (data.get('schema_version') != 1 or data.get('bindings') != {'ra.acute-stroke': ['soop-stroke-sub342-native']}
            or set(data.get('inspectors', {})) != {'soop-stroke-sub342-native'}
            or data.get('source_proposal_sha256') != PROPOSAL_SHA256
            or data.get('independent_source_review_sha256') != SOOP_REVIEW_SHA256):
        raise ValueError('Unexpected stroke native inspector scope or source')
    item = data['inspectors']['soop-stroke-sub342-native']
    _no_approval(item)
    if (item.get('id') != 'soop-stroke-sub342-native' or item.get('src') != NATIVE_PREFIX + 'reference.html'
            or item.get('manifest_url') != NATIVE_PREFIX + 'manifest.json'
            or item.get('module_id') != 'rad.4.stroke' or item.get('investigation_id') != 'ra.acute-stroke'
            or item.get('source_url') != SOURCE_URL or item.get('license') != 'CC0'
            or item.get('license_url') != 'https://creativecommons.org/publicdomain/zero/1.0/'
            or item.get('bound_source_ids') != ['soop-stroke-sub342']
            or item.get('independent_source_review_sha256') != SOOP_REVIEW_SHA256):
        raise ValueError('Native stroke case, provenance, path or approval changed')
    for field, filename in [('sha256', 'reference.html'), ('script_sha256', 'reference.js'), ('manifest_sha256', 'manifest.json')]:
        if hashlib.sha256((ROOT / 'web/anatomy/soop-stroke-sub342' / filename).read_bytes()).hexdigest() != item.get(field):
            raise ValueError('Native stroke inspector code or metadata changed')
    for field in ('title', 'caption', 'attribution'):
        if not isinstance(item.get(field), str) or not item[field].strip():
            raise ValueError('Native stroke inspector lacks source limits or attribution')
    manifest = json.loads((ROOT / 'web/anatomy/soop-stroke-sub342/manifest.json').read_text())
    if (manifest.get('schema_version') != 1 or manifest.get('id') != 'soop-stroke-sub342'
            or manifest.get('source_case') != 'sub-342' or manifest.get('dataset') != 'ds004889'
            or manifest.get('version') != '1.1.2' or manifest.get('license') != 'CC0'
            or manifest.get('source_url') != SOURCE_URL
            or manifest.get('pinned_root_tree') != 'a62344db73f18f384a95b452f4a1a423087e059b'
            or set(manifest.get('arrays', {})) != ARRAYS or set(manifest.get('meshes', {})) != MASKS):
        raise ValueError('Native stroke source manifest scope changed')
    for flag in ('clinical_approval', 'fine_anatomical_approval', 'structure_coverage_granted',
                 'current_patient_registration', 'T1_registered_to_diffusion', 'FLAIR_registered_to_diffusion',
                 'T1_registered_to_FLAIR', 'ADC_physical_units_verified', 'timing_or_pretreatment_state_known',
                 'source_resampling', 'source_sample_changes', 'source_mask_union_performed'):
        if manifest.get(flag) is not False:
            raise ValueError('Native source cannot promote registration, calibration, timing or clinical approval')
    if manifest.get('complete_arrays_no_crop') is not True or manifest.get('masks_are_separate_original_files') is not True:
        raise ValueError('Native stroke arrays must retain complete, separate source selections')
    published = {src: row for src, row in delivery()['files'].items() if src.startswith(NATIVE_PREFIX)}
    original_names = {src.removeprefix(NATIVE_PREFIX) for src, row in published.items() if row['role'] == 'source_original'}
    if original_names != ORIGINAL_NAMES:
        raise ValueError('Native stroke original source files are incomplete or from another case')
    for key, row in manifest['arrays'].items():
        _identity(row, published, NATIVE_PREFIX + key + '.native.gz', 'complete_native_storage_array')
        original = published[NATIVE_PREFIX + ORIGINAL_BY_ARRAY[key]]
        if (row.get('source_file') != NATIVE_PREFIX + ORIGINAL_BY_ARRAY[key]
                or (row.get('source_file_sha256'), row.get('source_file_bytes')) != (original['sha256'], original['bytes'])
                or row.get('source_sample_changes') is not False or row.get('codec') != 'gzip'
                or type(row.get('decoded_bytes')) is not int or row['decoded_bytes'] <= 0
                or not isinstance(row.get('shape'), list) or len(row['shape']) not in {3, 4}
                or any(type(v) is not int or v <= 0 for v in row['shape'])
                or row.get('spatial_shape') != row['shape'][:3]
                or row.get('frames') != (row['shape'][3] if len(row['shape']) == 4 else 1)):
            raise ValueError('Native stroke source array or original binding changed')
        expected_dtype = '<u1' if key in MASKS else '<i2'
        if (row.get('dtype') != expected_dtype
                or row['decoded_bytes'] != math.prod(row['shape']) * (1 if key in MASKS else 2)
                or not re.fullmatch(r'[a-f0-9]{64}', row.get('decoded_sha256', ''))):
            raise ValueError('Native stroke storage precision or complete decoded array size changed')
        affine = row.get('affine')
        if (not isinstance(affine, list) or len(affine) != 4
                or any(not isinstance(axis, list) or len(axis) != 4 for axis in affine)
                or any(type(v) not in {int, float} or not math.isfinite(v) for axis in affine for v in axis)
                or affine[3] != [0.0, 0.0, 0.0, 1.0]):
            raise ValueError('Native stroke spatial transform is invalid')
    for key, row in manifest['meshes'].items():
        _identity(row, published, NATIVE_PREFIX + key + '-cell-boundary.native.gz', 'source_mask_cell_geometry')
        if (row.get('source_mask_role') != key or row.get('source_sample_changes') is not False
                or row.get('source_mask_sha256') != manifest['arrays'][key]['source_file_sha256']
                or row.get('label_volume_is_pretreatment_core_or_irreversible_tissue') is not False
                or row.get('clinical_or_named_anatomical_boundary_approval') is not False
                or row.get('positions_dtype') != '<f8' or row.get('indices_dtype') != '<u4'
                or row.get('world_coordinate_convention') != 'RAS millimetres from exact selected source affine'):
            raise ValueError('Native stroke mask geometry changed source or grants unsupported approval')
    return {'ra.acute-stroke': [item]}
