"""Separate original cardiac source contexts; no anatomical/clinical approval transfer."""
import hashlib
import gzip
import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/radiology/cardiac-wall-context.json'
REGISTRY_SHA256 = '1c29f2a086ffc16155c1cf3ce78ea18d78764a386ac12372abb81b64086e0c16'
PACKED_REGISTRY = ROOT / 'data/radiology/cardiac-wall-context.json.gz'
PACKED_REGISTRY_SHA256 = 'f289c8f640e47e01cc5d4c582bb5f211471e81a7297306bbd1ead59fe6a30ae5'
CURATED = 'bp3d-cardiac-original-context'
COMPARISONS = 'baskaran-2020-cardiac-comparisons'
GROUPS = {CURATED, COMPARISONS}
BINDINGS = {'ra.thoracic-ultrasound', 'ra.mri-cardiomyopathy', 'ra.ct-coronary', 'ra.cardiac-masses'}
FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'current_patient_registration',
         'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved')


@lru_cache(maxsize=1)
def registry():
    packed = PACKED_REGISTRY.read_bytes()
    if hashlib.sha256(packed).hexdigest() != PACKED_REGISTRY_SHA256:
        raise ValueError('Packed cardiac registry changed')
    raw = gzip.decompress(packed)
    if REGISTRY.exists() and REGISTRY.read_bytes() != raw:
        raise ValueError('Original and packed cardiac registries differ')
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError('Cardiac wall context registry changed')
    data = json.loads(raw)
    if (data.get('schema_version') != 1 or set(data.get('groups', {})) != GROUPS
            or data.get('bindings') != {key: [CURATED, COMPARISONS] for key in BINDINGS}
            or data.get('clinical_approval') is not False or data.get('whole_goal_complete') is not False):
        raise ValueError('Cardiac wall context scope differs')
    for identifier, row in data['groups'].items():
        if identifier == CURATED:
            expected = ('web/anatomy/bp3d-cardiac-4.3', '/app/anatomy/bp3d-cardiac-4.3/',
                        {'index.html', 'reference.js', 'manifest.json'}, 31)
        else:
            expected = ('web/reference-media/cardiac-comparisons-2020', '/app/reference-media/cardiac-comparisons-2020/',
                        {'index.html', 'image-inventory.json.gz', 'gallery.js'}, 6064)
        if (row['directory'], row['prefix'], set(row['authored']), len(row['files'])) != expected:
            raise ValueError('Cardiac wall context resource scope differs')
    return data


def validate_file(identifier, asset):
    group = registry()['groups'].get(identifier)
    if group is None or asset not in group['files']:
        raise ValueError('Unknown cardiac wall context resource')
    path = ROOT / group['directory'] / asset
    ancestors = [path, *(p for p in path.parents if p == ROOT or ROOT in p.parents)]
    if any(p.is_symlink() for p in ancestors) or (path.exists() and not path.is_file()):
        raise ValueError('Cardiac wall source must be a regular file')
    if path.is_file():
        raw = path.read_bytes()
        expected = group['files'][asset]
        if len(raw) != expected['bytes'] or hashlib.sha256(raw).hexdigest() != expected['sha256']:
            raise ValueError('Cardiac wall context bytes changed')
    elif asset in group['authored'] or not os.environ.get('VERCEL'):
        raise ValueError('Cardiac wall context resource missing')
    return path


@lru_cache(maxsize=1)
def references():
    data = registry()
    for identifier, group in data['groups'].items():
        for asset in group['files']:
            validate_file(identifier, asset)
        item = group['inspector']
        manifest_name = 'manifest.json' if identifier == CURATED else 'image-inventory.json.gz'
        if (item.get('id') != identifier or item.get('src') != group['prefix'] + 'index.html'
                or item.get('manifest_url') != group['prefix'] + manifest_name
                or item.get('bound_source_ids') != [identifier]
                or item.get('supplementary_anatomy_context') is not True
                or item.get('sha256') != group['files']['index.html']['sha256']
                or item.get('manifest_sha256') != group['files'][manifest_name]['sha256']
                or any(item.get(flag) is not False for flag in FLAGS)):
            raise ValueError('Cardiac wall context identity/approval differs')
        manifest_raw = validate_file(identifier, manifest_name).read_bytes()
        manifest = json.loads(gzip.decompress(manifest_raw) if manifest_name.endswith('.gz') else manifest_raw)
        if identifier == CURATED:
            if (len(manifest['parts']) != 14 or sum(p['faces'] for p in manifest['parts']) != 72572
                    or manifest['clinical_approval'] is not False
                    or manifest['current_patient_registration'] is not False):
                raise ValueError('Curated cardiac source scope differs')
        else:
            if (len(manifest['files']) != 6061 or len(manifest['categories']) != 8
                    or set(manifest['categories']) != set(manifest['paper_defined_categories'])
                    or manifest['paper_colour_roles'] != {'red': 'model prediction', 'green': 'manual ground-truth annotation'}
                    or manifest['source_native_DICOM_or_NIfTI_present'] is not False
                    or manifest['spatial_spacing_orientation_and_3D_registration_established'] is not False
                    or manifest['clinical_approval'] is not False):
                raise ValueError('Published CT comparison scope differs')
            for row in manifest['files']:
                if (row['member'] != 'images/' + row['sha256'] + '.png'
                        or row['member'] not in group['files']
                        or row['sha256'] != group['files'][row['member']]['sha256']
                        or row['category'] not in manifest['paper_defined_categories']
                        or row['dimensions'] != [512, 256]):
                    raise ValueError('Published comparison file binding differs')
    return {key: [data['groups'][identifier]['inspector'] for identifier in ids]
            for key, ids in data['bindings'].items()}
