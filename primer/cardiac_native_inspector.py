"""Original v1 cardiac CT and mask interfaces; no wall/function approval extension."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'totalseg-v1-s0028-cardiac'
IDENTIFIER = 'totalseg-v1-s0028-cardiac-native'
PREFIX = '/app/anatomy/' + ATLAS + '/'
REGISTRY = ROOT / 'data/radiology/cardiac-native-inspector.json'
REGISTRY_SHA256 = '4a0c1629a1d4b0cbf25e8606b654f03cf16a6b1fac1028797d2ed683973d2af8'
AUTHORED = frozenset({'index.html', 'viewer.css', 'volume-review.js', 'surface-review.js', 'mask-storage.js', 'viewer-manifest.json'})
LABELS = frozenset({'heart_myocardium', 'heart_atrium_left', 'heart_ventricle_left', 'heart_atrium_right', 'heart_ventricle_right'})
BINDINGS = frozenset({'ra.thoracic-ultrasound', 'ra.mri-cardiomyopathy', 'ra.ct-coronary', 'ra.cardiac-masses'})
APPROVAL_FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'current_patient_registration',
                  'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved')


@lru_cache(maxsize=1)
def registry():
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError('Cardiac source registry changed')
    data = json.loads(raw)
    expected = set(AUTHORED) | {'originals/ct.nii.gz'} | {'originals/' + label + '.nii.gz' for label in LABELS} | {'surfaces/' + label + '-review-buffer.bin.gz' for label in LABELS}
    if (data.get('schema_version') != 1 or data.get('source_case') != 's0028'
            or data.get('source_version') != '1.0' or data.get('source_doi') != '10.5281/zenodo.6802614'
            or set(data.get('files', {})) != expected or data.get('source_triangles') != 86072
            or data.get('bindings') != {key: [IDENTIFIER] for key in BINDINGS}
            or set(data.get('inspectors', {})) != {IDENTIFIER}):
        raise ValueError('Cardiac source scope differs')
    return data


def validate_file(asset):
    data = registry()
    if asset not in data['files']:
        raise ValueError('Unknown cardiac source asset')
    base = ROOT / 'web/anatomy' / ATLAS
    path = base / asset
    within_root = [path, *(parent for parent in path.parents if parent == ROOT or ROOT in parent.parents)]
    if any(part.is_symlink() for part in within_root) or (path.exists() and not path.is_file()):
        raise ValueError('Cardiac source must be a regular file')
    row = data['files'][asset]
    if path.is_file():
        raw = path.read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Cardiac source bytes changed')
    elif asset in AUTHORED or not os.environ.get('VERCEL'):
        raise ValueError('Cardiac source file missing')
    return path


@lru_cache(maxsize=1)
def references():
    data = registry()
    for asset in data['files']:
        validate_file(asset)
    item = data['inspectors'][IDENTIFIER]
    if (item.get('id') != IDENTIFIER or item.get('src') != PREFIX + 'index.html'
            or item.get('manifest_url') != PREFIX + 'viewer-manifest.json' or item.get('modality') != 'CT'
            or item.get('bound_source_ids') != [IDENTIFIER]
            or any(item.get(flag) is not False for flag in APPROVAL_FLAGS)
            or item.get('sha256') != data['files']['index.html']['sha256']
            or item.get('manifest_sha256') != data['files']['viewer-manifest.json']['sha256']):
        raise ValueError('Cardiac source identity or approval differs')
    manifest = json.loads(validate_file('viewer-manifest.json').read_bytes())
    if (manifest.get('case') != 's0028' or manifest.get('source_version') != '1.0'
            or manifest.get('source_doi') != '10.5281/zenodo.6802614'
            or manifest.get('shape') != [299, 299, 394] or manifest.get('spacing') != [1.5, 1.5, 1.5]
            or manifest.get('ct_sample_kind') != 'signed_int32' or manifest.get('ct_sample_bytes') != 4
            or manifest.get('ct_datatype_code') != 8 or manifest.get('source_xyzt_units') != 0
            or {part['id'] for part in manifest['parts']} != LABELS
            or sum(part['triangles'] for part in manifest['parts']) != 86072
            or any(manifest.get(flag) is not False for flag in ['clinical_approval', 'normal_anatomical_atlas_approval', 'current_patient_registration', 'verified_structure_coverage_granted'])):
        raise ValueError('Original v1 cardiac source manifest differs')
    if manifest['ct_file'] != 'originals/ct.nii.gz' or manifest['ct_file_sha256'] != data['files']['originals/ct.nii.gz']['sha256']:
        raise ValueError('Original v1 CT binding differs')
    for part in manifest['parts']:
        if (part['mask_file'] != 'originals/' + part['id'] + '.nii.gz'
                or part['buffer_file'] != 'surfaces/' + part['id'] + '-review-buffer.bin.gz'
                or part['mask_file_sha256'] != data['files'][part['mask_file']]['sha256']
                or part['buffer_sha256'] != data['files'][part['buffer_file']]['sha256']
                or part['max_centered_float32_position_error_source_coordinates'] != 0):
            raise ValueError('Cardiac source array/interface binding differs')
    return {key: [item] for key in BINDINGS}
