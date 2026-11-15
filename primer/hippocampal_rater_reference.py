"""Verified paired hippocampal source annotations; no clinical approval inferred."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'dryad-hippocampal-case10'
PREFIX = '/app/anatomy/' + ATLAS + '/'
IDENTIFIER = 'dryad-hippocampal-case10-rater-reference'
BLOB_HOST = 'https://ja2lsnp9uca4bivw.public.blob.vercel-storage.com'
BLOB_PREFIX = BLOB_HOST + '/radiology-native/dryad-hippocampal-case10-v7/'
REGISTRY = ROOT / 'web/anatomy' / ATLAS / 'registry.json'
REGISTRY_SHA256 = 'f76c652f36cca038e68986e80000f0fa96ac71be01b0e195427c3f461ded8c72'
AUTHORED = frozenset({'index.html', 'viewer.js', 'transport.js', 'viewer.css',
                      'config.json', 'manifest.json', 'ATTRIBUTION.txt'})
FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'current_patient_registration',
         'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved')
BINDINGS = ('ra.mri-epilepsy',)
MANIFEST_SHA256 = '2df71533dd1e3d08c416dc929b3a00cd62d7af449f00b5ae96f88823ea557608'
SOURCE_HASHES = {'anon_sMT04294-0008-00001-000001-01.nii': '19b9592560a03c730c32efce4a722b3a115b2b7c6d3a8ecaf5292024a57c3525', 'anon_meansMT04294-0008-00001-000001-01_denoised_prinlm_b2.0.nii': '8757ead3ca70dd77ea7dcab0ebe686416b3be44ae1455a0ede5475efc036027e', 'anon_sMT04294-0010-00001-000001-01.nii': 'f10ced100426a605077035ec280cb73289fe1ca40cfa48e01d861d392ca9c684', 'anon_sMT04294-0009-00001-000001-01.nii': 'f10ced100426a605077035ec280cb73289fe1ca40cfa48e01d861d392ca9c684', 'DICE_Hippocampal_Segmentation.nii': '9f09d86343604e0a28ae495e232d6297400c5c9515b2c33cd68c1316c2fd9b2a', 'Hippocampal_Subfield_Segmentation_Labels.txt': '46e7ec695eb1ebdfff9d10e27ed21b3a04c4461c9d014e6786415ed9f83943a1', 'Hippocampal_Segmentation.nii': '5fd0926857e34e9db286b79f9398c8eee133fda03bf84a572569a0bc597b8898', 'README.md': '09b237189f7ef964a8be3eb2c7a4da1619266b9620e2adbf16b37eefc1240b65'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def regular(path):
    if any(p.is_symlink() for p in [path, *path.parents] if p == ROOT or ROOT in p.parents):
        raise ValueError('Hippocampal reference cannot use a symlink')
    if not path.is_file():
        raise ValueError('Hippocampal reference file is missing')


@lru_cache(maxsize=1)
def registry():
    regular(REGISTRY)
    raw = REGISTRY.read_bytes()
    if sha(raw) != REGISTRY_SHA256:
        raise ValueError('Hippocampal reference registry changed')
    data = json.loads(raw)
    if (data.get('schema_version') != 1 or data.get('dataset_doi') != '10.5061/dryad.2v6wwpzt3' or data.get('version') != 7 or data.get('source_case') != '10'
            or data.get('bindings') != list(BINDINGS)
            or set(data.get('files', {})) != AUTHORED
            or any(data.get(key) is not False for key in FLAGS)
            or data.get('source_original_hashes') != SOURCE_HASHES):
        raise ValueError('Hippocampal reference scope changed')
    return data


@lru_cache(maxsize=32)
def _check(path, size, modified, digest):
    raw = Path(path).read_bytes()
    if len(raw) != size or sha(raw) != digest:
        raise ValueError('Hippocampal reference source bytes changed')


def validate_file(name):
    if name not in AUTHORED:
        raise ValueError('Unknown Hippocampal reference file')
    path = ROOT / 'web/anatomy' / ATLAS / name
    regular(path)
    stat = path.stat()
    row = registry()['files'][name]
    if stat.st_size != row['bytes']:
        raise ValueError('Hippocampal reference length changed')
    _check(str(path), stat.st_size, stat.st_mtime_ns, row['sha256'])
    return path


@lru_cache(maxsize=1)
def references():
    data = registry()
    for name in AUTHORED:
        validate_file(name)
    manifest = json.loads(validate_file('manifest.json').read_bytes())
    config = json.loads(validate_file('config.json').read_bytes())
    if (data['files']['manifest.json']['sha256'] != MANIFEST_SHA256
            or config != {'manifestSHA256': MANIFEST_SHA256, 'blobPrefix': BLOB_PREFIX + 'runtime/'}
            or manifest.get('sourceDOI') != '10.5061/dryad.2v6wwpzt3'
            or manifest.get('sourceVersion') != 7 or manifest.get('license') != 'CC0-1.0'
            or manifest.get('fullArchiveVerificationPending') is not False
            or manifest.get('clinicalApproval') is not False
            or manifest.get('annotationReferenceVolume') != 'mean'
            or manifest.get('rawRepetitionAnatomicalRegistrationVerified') is not False
            or manifest.get('planeCount') != 4944 or len(manifest.get('packs', {})) != 21
            or len(manifest.get('meshes', {})) != 13
            or sum(row['triangles'] for row in manifest['meshes'].values()) != 167796
            or set(manifest.get('volumes', {})) != {'mean', 'repeat0008', 'repeat0009', 'repeat0010', 'primary', 'second'}):
        raise ValueError('Hippocampal source interpretation changed')
    authentication = manifest.get('sourceArchiveAuthentication', {})
    if (authentication != data['sourceAuthentication']
            or authentication.get('archiveSHA256') != 'e76586274bba73f64f2355b093da3ae671fb8e77bb62c13528cfac9d4893ba2e'
            or authentication.get('archiveBytes') != 13046575553
            or authentication.get('selectedRangesVerified') != 19
            or authentication.get('acquisitionReceiptSHA256') != 'dfab764bc92a28f6366c926cb90eae0201a20acd2c23db00bfb47893ddb5f63b'):
        raise ValueError('Hippocampal publisher authentication changed')
    expected = dict(manifest['packs'])
    for mesh in manifest['meshes'].values():
        expected[mesh['file']] = {'bytes': mesh['compressedBytes'], 'sha256': mesh['compressedSHA256']}
    delivery = data['delivery']
    if (delivery.get('allRemoteHashesMatch') is not True
            or delivery.get('manifestSHA256') != MANIFEST_SHA256
            or set(delivery.get('files', {})) != set(expected)
            or len(expected) != 34 or set(delivery.get('originals', {})) != set(SOURCE_HASHES)):
        raise ValueError('Hippocampal verified delivery is incomplete')
    for name, row in expected.items():
        if delivery['files'][name] != dict(row, url=BLOB_PREFIX+'runtime/'+row['sha256']+'/'+name, remoteHashVerified=True):
            raise ValueError('Hippocampal payload identity changed')
    for name, digest in SOURCE_HASHES.items():
        row = delivery['originals'][name]
        if (row.get('remoteHashVerified') is not True or row.get('sha256') != digest
                or row.get('bytes', 0) <= 0
                or row.get('url') != BLOB_PREFIX+'originals/'+digest+'/'+name):
            raise ValueError('Hippocampal original identity changed')
    for volume in manifest['volumes'].values():
        if volume['shape'] != [328, 384, 112] or volume['sourceFileSHA256'] != SOURCE_HASHES[volume['sourceFile']]:
            raise ValueError('Hippocampal source grid changed')
    if (manifest['volumes']['mean']['dtype'] != '<i2'
            or manifest['volumes']['mean']['slope'] != 0.010997800156474113
            or manifest['volumes']['repeat0009']['sourceFileSHA256'] != manifest['volumes']['repeat0010']['sourceFileSHA256']
            or sum(len(v) for key in ['primary', 'second'] for v in manifest['volumes'][key]['components'].values()) != 29):
        raise ValueError('Hippocampal source scaling or components changed')
    item = data['inspector']
    if (item['id'] != IDENTIFIER or item['src'] != PREFIX+'index.html'
            or item['sha256'] != data['files']['index.html']['sha256']
            or item['manifest_sha256'] != MANIFEST_SHA256
            or item['bound_source_ids'] != [IDENTIFIER] or item['license'] != 'CC0-1.0'
            or item['source_url'] != 'https://doi.org/10.5061/dryad.2v6wwpzt3'
            or any(item.get(key) is not False for key in FLAGS)):
        raise ValueError('Hippocampal source descriptor changed')
    return {key: [item] for key in BINDINGS}
