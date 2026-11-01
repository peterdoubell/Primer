"""Additional named SPL classes; original surfaces and exact categorical cells."""
from functools import lru_cache
from pathlib import Path
import gzip
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'spl-additional-source'
IDENTIFIER = 'spl-additional-native-source-reference'
PREFIX = '/app/anatomy/' + ATLAS + '/'
REGISTRY = ROOT / 'data/radiology/spl-additional-reference.json'
REGISTRY_SHA256 = '7785753e8f163bdfab550d4effd00b7b1b1a6d70bd55529356b75eec25e22ba7'
BINDINGS = ['ra.brain-anatomy', 'ra.mri-sella', 'ra.mri-neck-spaces']
SOURCE_COMMIT = 'bec24db25aad5f7600e2df3becfb1f883e61ff56'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def regular(path):
    if not path.is_file() or any(p.is_symlink() for p in [path, *path.parents] if p == ROOT or ROOT in p.parents):
        raise ValueError('Additional SPL resource must be a regular file')


@lru_cache(maxsize=1)
def registry():
    regular(REGISTRY)
    raw = REGISTRY.read_bytes()
    if sha(raw) != REGISTRY_SHA256:
        raise ValueError('Additional SPL registry identity differs')
    data = json.loads(raw)
    if (data['schema_version'] != 1 or data['source_commit'] != SOURCE_COMMIT or
            data['bindings'] != BINDINGS or len(data['files']) != 288 or
            data['source_class_count'] != 94 or data['original_and_cell_surface_count'] != 188 or
            data['clinicalApproval'] is not False or data['wholeGoalComplete'] is not False):
        raise ValueError('Additional SPL source scope differs')
    return data


@lru_cache(maxsize=1)
def manifest_bytes():
    row = registry()['runtime_manifest']
    if row['path'] != 'data/radiology/spl-additional-manifest.json.gz':
        raise ValueError('Additional SPL manifest address differs')
    path = ROOT / row['path']
    regular(path)
    packed = path.read_bytes()
    if len(packed) != row['bytes'] or sha(packed) != row['sha256']:
        raise ValueError('Additional SPL manifest transport differs')
    raw = gzip.decompress(packed)
    if len(raw) != row['decodedBytes'] or sha(raw) != row['decodedSHA256']:
        raise ValueError('Additional SPL manifest identity differs')
    return raw


def validate_file(asset):
    if asset not in registry()['files']:
        raise ValueError('Unknown additional SPL resource')
    path = ROOT / 'web/anatomy' / ATLAS / asset
    if any(p.is_symlink() for p in [path,*path.parents] if p == ROOT or ROOT in p.parents):
        raise ValueError('Additional SPL resource must be a regular file')
    if not path.exists() and asset.endswith('.gz') and os.environ.get('VERCEL'):
        return path
    raw = manifest_bytes() if asset == 'manifest.json' else None
    if raw is None:
        regular(path)
        raw = path.read_bytes()
    row = registry()['files'][asset]
    if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
        raise ValueError('Additional SPL resource identity differs')
    return path


@lru_cache(maxsize=1)
def references():
    from . import spl_limbic_reference as shared
    from .spl_reporting_reference import FLAGS
    shared.references()
    data = registry()
    for asset in data['files']:
        validate_file(asset)
    manifest = json.loads(manifest_bytes())
    if (manifest['sourceCommit'] != SOURCE_COMMIT or
            manifest['sharedSourceManifestSHA256'] != data['shared_source_manifest_sha256'] or
            sha(shared.validate_file('manifest.json').read_bytes()) != data['shared_source_manifest_sha256'] or
            len(manifest['labels']) != 94 or len(manifest['labelMeshes']) != 94 or len(manifest['publisherMeshes']) != 94 or
            len({row['code'] for row in manifest['labels']}) != 94 or
            any(manifest[key] is not False for key in ['clinicalApproval', 'completeReportingAnatomyApproved', 'normalPopulationAtlas', 'currentPatientRegistration', 'newFittedTransforms'])):
        raise ValueError('Additional SPL manifest scope differs')
    original = json.loads(shared.validate_file('manifest.json').read_bytes())
    for row, expected in [(manifest['labelVolume'], original['labelVolume']), *[(manifest['volumes'][key], original['volumes'][key]) for key in ['T1', 'T2']]]:
        if row != dict(expected, sharedSource='spl-nac-limbic'):
            raise ValueError('Additional SPL changed a shared native descriptor')
    codes = {row['code'] for row in manifest['labels']}
    for collection in ['labelMeshes', 'publisherMeshes']:
        if {row['code'] for row in manifest[collection]} != codes:
            raise ValueError('Additional SPL surface classes differ')
        for row in manifest[collection]:
            file = validate_file(row['file'])
            if data['files'][row['file']] != {'bytes':row['gzipBytes'],'sha256':row['gzipSHA256']}:
                raise ValueError('Additional SPL transport descriptor differs')
            if (row['coordinateSystem'] != 'RAS' or row['positionsAlreadyRAS'] is not True or row['spaceUnits'] != 'mm' or
                    row['sourceAffine'] != [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]):
                raise ValueError('Additional SPL coordinate convention differs')
            if not file.is_file():
                continue  # Static runtime payloads are independently hashed by the browser and release readbacks.
            packed = file.read_bytes()
            raw = gzip.decompress(packed)
            n = row['vertexCount']
            if (sha(packed) != row['gzipSHA256'] or len(packed) != row['gzipBytes'] or
                    sha(raw) != row['decodedSHA256'] or len(raw) != row['byteLength'] or
                    sha(raw[16:16+n*12]) != row['positionByteSHA256'] or sha(raw[16+n*12:]) != row['indexByteSHA256'] or
                    row['coordinateSystem'] != 'RAS' or row['positionsAlreadyRAS'] is not True or row['spaceUnits'] != 'mm' or
                    row['sourceAffine'] != [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]):
                raise ValueError('Additional SPL geometry identity differs')
    item = data['inspector']
    if (item['id'] != IDENTIFIER or item['bound_source_ids'] != [IDENTIFIER] or item['src'] != PREFIX+'index.html' or
            item['manifest_url'] != PREFIX+'manifest.json' or item['sha256'] != data['files']['index.html']['sha256'] or
            item['manifest_sha256'] != data['files']['manifest.json']['sha256'] or any(item.get(flag) is not False for flag in FLAGS) or
            item['source_grain']['selected_label_classes'] != 94 or item['source_grain']['subject_count'] != 1 or
            item['source_grain']['source_code_4084_correspondence_resolved'] is not False):
        raise ValueError('Additional SPL descriptor scope differs')
    return {identifier: [item] for identifier in BINDINGS}
