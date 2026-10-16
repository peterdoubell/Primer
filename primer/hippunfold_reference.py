"""Published registered hippocampal training reference with bounded source meaning."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'hippunfold-hcp101006-registered'
IDENTIFIER = 'hippunfold-hcp101006-registered-reference'
PREFIX = '/app/anatomy/' + ATLAS + '/'
REGISTRY = ROOT / 'data/radiology/hippunfold-reference.json'
REGISTRY_SHA256 = '5173fde12f1a96842f23b9e34b839d4103e4bf3704b02423850c2f83d44c8773'
AUTHORED = frozenset({'index.html', 'viewer.css', 'viewer.js', 'payload.js', 'manifest.json'})
BINDINGS = frozenset({'ra.mri-epilepsy', 'ra.mri-dementia'})
APPROVAL_FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'current_patient_registration',
                  'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved')


@lru_cache(maxsize=1)
def registry():
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError('Hippocampal reference registry changed')
    data = json.loads(raw)
    expected = set(AUTHORED) | {side + '-' + kind + '.bin.gz' for side in ['L', 'R'] for kind in ['T2w', 'lbl']}
    expected |= {f'101006-{side}-label-{label}.mesh.gz' for side in ['L', 'R'] for label in range(1, 9)}
    if (data.get('schema_version') != 1 or data.get('source_case') != '101006'
            or data.get('source_version') != 'v1.0.0' or data.get('source_doi') != '10.5281/zenodo.7007362'
            or set(data.get('files', {})) != expected
            or data.get('bindings') != {key: [IDENTIFIER] for key in BINDINGS}
            or set(data.get('inspectors', {})) != {IDENTIFIER}):
        raise ValueError('Hippocampal reference source scope differs')
    return data


def validate_file(asset):
    data = registry()
    if asset not in data['files']:
        raise ValueError('Unknown hippocampal reference asset')
    path = ROOT / 'web/anatomy' / ATLAS / asset
    within_root = [path, *(parent for parent in path.parents if parent == ROOT or ROOT in parent.parents)]
    if any(part.is_symlink() for part in within_root) or (path.exists() and not path.is_file()):
        raise ValueError('Hippocampal reference must be a regular file')
    row = data['files'][asset]
    if path.is_file():
        raw = path.read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Hippocampal reference bytes changed')
    elif asset in AUTHORED or not os.environ.get('VERCEL'):
        raise ValueError('Hippocampal reference file missing')
    return path


@lru_cache(maxsize=1)
def references():
    data = registry()
    for asset in data['files']:
        validate_file(asset)
    item = data['inspectors'][IDENTIFIER]
    if (item.get('id') != IDENTIFIER or item.get('src') != PREFIX + 'index.html'
            or item.get('manifest_url') != PREFIX + 'manifest.json'
            or item.get('modality') != 'Registered T2 MRI and categorical surfaces'
            or item.get('coordinate_context') != 'published-registered-training-grid'
            or item.get('bound_source_ids') != [IDENTIFIER]
            or any(item.get(flag) is not False for flag in APPROVAL_FLAGS)
            or item.get('sha256') != data['files']['index.html']['sha256']
            or item.get('manifest_sha256') != data['files']['manifest.json']['sha256']):
        raise ValueError('Hippocampal reference identity or approval differs')
    manifest = json.loads(validate_file('manifest.json').read_bytes())
    if (manifest.get('case') != '101006' or manifest.get('sourceVersion') != 'v1.0.0'
            or manifest.get('sourceRecord') != 'https://zenodo.org/records/7007362'
            or manifest.get('shape') != [128, 256, 128] or manifest.get('storageOrder') != 'F'
            or {h['name'] for h in manifest['hemispheres']} != {'L', 'R'}
            or {(m['sourceHemisphereName'], m['label']) for m in manifest['meshes']}
               != {(side, label) for side in ['L', 'R'] for label in range(1, 9)}
            or sum(m['triangleCount'] for m in manifest['meshes']) != 472392):
        raise ValueError('Hippocampal reference array or surface scope differs')
    arrays = [row for hemisphere in manifest['hemispheres'] for row in hemisphere['arrays']]
    payloads = [*arrays, *manifest['meshes']]
    if {r['file'] for r in payloads} != set(data['files']) - AUTHORED:
        raise ValueError('Hippocampal reference payload inventory differs')
    for row in payloads:
        if row['gzipSHA256'] != data['files'][row['file']]['sha256'] or row['byteLength'] <= 0:
            raise ValueError('Hippocampal reference payload identity differs')
    for hemisphere in manifest['hemispheres']:
        if {(r['modality'], r['dtype'], r['byteLength']) for r in hemisphere['arrays']} != {
                ('T2w', '<f4', 16777216), ('lbl', 'u1', 4194304)}:
            raise ValueError('Hippocampal reference sample interpretation differs')
        if any(m['sourceAffine'] != hemisphere['affine'] for m in manifest['meshes']
               if m['sourceHemisphereName'] == hemisphere['name']):
            raise ValueError('Hippocampal surface and image coordinate frames differ')
    return {key: [item] for key in BINDINGS}
