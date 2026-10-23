"""Pinned population-template reference; never a patient or clinical approval."""
from functools import lru_cache
from pathlib import Path
import gzip
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'holiatlas'
IDENTIFIER = 'holiatlas-source-template-reference'
PREFIX = '/app/anatomy/holiatlas/'
REGISTRY = ROOT / 'data/radiology/holiatlas-reference.json'
REGISTRY_SHA256 = 'f7f6a1fc08c0599ff75b7822488d7a56e52e53dba47ef0f31953e30a89daa176'
AUTHORED = frozenset({'index.html', 'viewer.js', 'viewer.css', 'config.json',
                      'manifest.json', 'labels.json', 'ATTRIBUTION.txt', 'LICENSE.txt'})
FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'current_patient_registration',
         'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@lru_cache(maxsize=1)
def registry():
    raw = REGISTRY.read_bytes()
    if sha(raw) != REGISTRY_SHA256:
        raise ValueError('holiAtlas registry changed')
    data = json.loads(raw)
    if (data.get('schema_version') != 1 or data.get('atlas') != ATLAS
            or data.get('source_record') != 'https://zenodo.org/records/15690524'
            or data.get('source_archive_sha256') != '6932bc8063568f0037627d5b85199ff6142b4457413f8fef8817871a3ffa1ee5'
            or data.get('bindings') != {'ra.brain-anatomy': [IDENTIFIER]}
            or set(data.get('inspectors', {})) != {IDENTIFIER}
            or len(data.get('files', {})) != 687 or not AUTHORED <= set(data['files'])
            or any(data.get(flag) is not False for flag in FLAGS)
            or [data.get(k) for k in ('present_source_classes', 'missing_named_classes',
                'components26', 'triangles', 'plane_count')] != [332, 18, 868, 11650276, 4632]):
        raise ValueError('holiAtlas source scope differs')
    return data


@lru_cache(maxsize=2)
def metadata_bytes(name):
    if name not in {'manifest.json', 'labels.json'}:
        raise ValueError('Unknown holiAtlas metadata')
    row = registry()['runtime_metadata'][name]
    expected_path = 'data/radiology/holiatlas-' + name + '.gz'
    if row['path'] != expected_path:
        raise ValueError('holiAtlas metadata path differs')
    file = ROOT / expected_path
    if not file.is_file() or file.is_symlink():
        raise ValueError('holiAtlas metadata must be a regular file')
    packed = file.read_bytes()
    if len(packed) != row['bytes'] or sha(packed) != row['sha256']:
        raise ValueError('holiAtlas metadata transport changed')
    raw = gzip.decompress(packed)
    expected = registry()['files'][name]
    if (len(raw) != row['decoded_bytes'] or sha(raw) != row['decoded_sha256']
            or len(raw) != expected['bytes'] or sha(raw) != expected['sha256']):
        raise ValueError('holiAtlas decoded metadata changed')
    return raw


@lru_cache(maxsize=2048)
def _check_file(path, size, mtime, expected_sha):
    raw = Path(path).read_bytes()
    if len(raw) != size or sha(raw) != expected_sha:
        raise ValueError('holiAtlas asset bytes changed')


def validate_file(asset):
    files = registry()['files']
    if asset not in files:
        raise ValueError('Unknown holiAtlas asset')
    file = ROOT / 'web/anatomy' / ATLAS / asset
    if any(p.is_symlink() for p in [file, *file.parents] if p == ROOT or ROOT in p.parents):
        raise ValueError('holiAtlas asset cannot use a symlink')
    if file.exists():
        if not file.is_file():
            raise ValueError('holiAtlas asset must be a regular file')
        stat = file.stat()
        if stat.st_size != files[asset]['bytes']:
            raise ValueError('holiAtlas asset length changed')
        _check_file(str(file), stat.st_size, stat.st_mtime_ns, files[asset]['sha256'])
    elif asset in {'manifest.json', 'labels.json'} and os.environ.get('VERCEL'):
        metadata_bytes(asset)
    elif asset in AUTHORED or not os.environ.get('VERCEL'):
        raise ValueError('holiAtlas asset missing')
    return file


@lru_cache(maxsize=1)
def references():
    data = registry()
    for name in data['files']:
        validate_file(name)
    manifest = json.loads(metadata_bytes('manifest.json'))
    labels = json.loads(metadata_bytes('labels.json'))
    config = json.loads(validate_file('config.json').read_bytes())
    if (manifest.get('clinicalApproval') is not False or manifest.get('currentPatientRegistration') is not False
            or manifest.get('sourceGridIsAcquisitionResolution') is not False
            or manifest.get('sulcalLabelsAreCSFTerritories') is not True
            or labels.get('clinicalApproval') is not False
            or [labels.get(k) for k in ('presentClasses', 'missingNamedClasses', 'components26')] != [332, 18, 868]
            or set(manifest.get('volumes', {})) != {'labels', 'T1', 'T2', 'WMn'}
            or len(manifest.get('packs', {})) != 15):
        raise ValueError('holiAtlas source interpretation differs')
    for name in ['manifest.json', 'labels.json']:
        key = 'manifestSHA256' if name == 'manifest.json' else 'labelsSHA256'
        if config[key] != data['files'][name]['sha256']:
            raise ValueError('holiAtlas viewer metadata identity differs')
    for name, row in manifest['packs'].items():
        if data['files'][name] != {'bytes': row['bytes'], 'sha256': row['sha256']}:
            raise ValueError('holiAtlas range pack identity differs')
    classes = labels['sourceClasses']
    if (len(classes) != 350 or len({row['code'] for row in classes}) != 350
            or sum(bool(row['voxels']) for row in classes) != 332
            or sum(len(row['components26']) for row in classes) != 868):
        raise ValueError('holiAtlas label inventory differs')
    for row in classes:
        if row['voxels']:
            mesh = row['mesh']
            if data['files'][mesh['file']] != {'bytes': mesh['gzipBytes'], 'sha256': mesh['gzipSHA256']}:
                raise ValueError('holiAtlas mesh identity differs')
            if sum(c['voxels'] for c in row['components26']) != row['voxels']:
                raise ValueError('holiAtlas components differ')
        elif not row.get('missingSourceLabel') or row['components26']:
            raise ValueError('holiAtlas missing class was fabricated')
    item = data['inspectors'][IDENTIFIER]
    if (item['id'] != IDENTIFIER or item['src'] != PREFIX + 'index.html'
            or item['manifest_url'] != PREFIX + 'manifest.json'
            or item['sha256'] != data['files']['index.html']['sha256']
            or item['manifest_sha256'] != data['files']['manifest.json']['sha256']
            or item['bound_source_ids'] != [IDENTIFIER]
            or any(item.get(flag) is not False for flag in FLAGS)
            or item['source_grain']['WMn_like_contrast_synthesized'] is not True
            or item['source_grain']['sulcal_classes_are_CSF_territories'] is not True):
        raise ValueError('holiAtlas inspector interpretation differs')
    return {'ra.brain-anatomy': [item]}
