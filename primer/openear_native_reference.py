"""Verified OpenEar source CBCT and independent masks; no clinical approval inferred."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
ATLAS = 'openear-zeta-native'
PREFIX = '/app/anatomy/' + ATLAS + '/'
IDENTIFIER = 'openear-zeta-native-reference'
BLOB_HOST = 'https://ja2lsnp9uca4bivw.public.blob.vercel-storage.com'
BLOB_PREFIX = BLOB_HOST + '/radiology-native/openear-zeta-1473724/'
REGISTRY = ROOT / 'web/anatomy' / ATLAS / 'registry.json'
REGISTRY_SHA256 = '3e54cca417c3d04e456b370ebb5c0e9fab535e85d1fc252d7bd5108a3bae7730'
AUTHORED = frozenset({'index.html', 'viewer.js', 'transport.js', 'viewer.css',
                      'config.json', 'manifest.json', 'ATTRIBUTION.txt'})
FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'current_patient_registration',
         'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved')
BINDINGS = ('ra.ct-temporal-bone', 'ra.tinnitus')
MANIFEST_SHA256 = '4337a7bf103fc6d53cb438338aa12c7eeca468091122f95fe0eda7314c680cc9'
SOURCE_HASHES = {'CBCT_Embedded.nrrd': 'e6489c3e3df2ffc5e2bab3b4a1be8eee2b55f8c23f8fd980d1edf05e8d14cdda', 'CBCT_Unembedded.nrrd': 'fa41f82bcc5038a592bb7fc3bfd9d75de5f498ed912990c8021363c3bc419550', 'Segmentation.seg.nrrd': '623e4a93c002200a322ffe8550dd4e8d9d2c7830085642c8685426056167f48a', 'Bone.nrrd': '90f7567b9cd596c4d685e14575d997a0cb2e99d805ac9098e5859d87c0992fd1', 'source-mesh-0.ply': '98af05f86d72ec8333e943f49b1e46a1a6994f4e1fa84237d748c9b9648d6057', 'source-mesh-1.ply': 'bfc2675fde44dc5aa3701a2e6cd6937cf376731980de2b2a22848374492e2610', 'source-mesh-2.ply': '52e00f6afe6946e8adf6e2514acbf072950e62dac4d39ca8edc0d87b2ffb1cc2', 'source-mesh-3.ply': 'f967dd6b0fc5f195fe76a3605f8a5acfaf522c62667d0acf194637574c2049ee', 'source-mesh-4.ply': '91da300f4245514218410d33a371be2470e53b30c4197001ebf9879988bb3364', 'source-mesh-5.ply': 'eac4659a931547f7076268916a0764aee68d4fa8b608f705152f83e24e451003', 'source-mesh-6.ply': '8ff2794c19781737d95f1727e432cca894b0a0e415fb314bc4409469fec35dd1', 'source-mesh-7.ply': 'c18b95a8c6969bcc1af9ec3043219cca199e618b61ed0234e34a5e442cba5f8a', 'source-mesh-8.ply': '1c4e249ccd92245b310c0f90faa7f8b3f314fd36595edb008d82ec9fcc96ca8d', 'source-mesh-9.ply': 'a147fe221fbbd4049997c8e25a7ee39e4b2bdf5e41f99df26fbb69a5ea6967f4', 'source-mesh-10.ply': 'fad44c122c79d2d3fa9cc662795dea8c735d6db03c3e469dca44834c371df4fe', 'source-mesh-11.ply': 'cbe91185a03494fa05d0cb27fcb00bcce30a39cdf57dd1976f2060832cb2d0c5', 'source-mesh-12.ply': '380e7ab49bbcb57ac62bd1fd0a1670391c648a7021186ee514d7fe68a67a4573'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def regular(path):
    if any(p.is_symlink() for p in [path, *path.parents] if p == ROOT or ROOT in p.parents):
        raise ValueError('OpenEar reference cannot use a symlink')
    if not path.is_file():
        raise ValueError('OpenEar reference file is missing')


@lru_cache(maxsize=1)
def registry():
    regular(REGISTRY)
    raw = REGISTRY.read_bytes()
    if sha(raw) != REGISTRY_SHA256:
        raise ValueError('OpenEar reference registry changed')
    data = json.loads(raw)
    if (data.get('schema_version') != 1 or data.get('record') != 1473724
            or data.get('bindings') != list(BINDINGS)
            or set(data.get('files', {})) != AUTHORED
            or any(data.get(key) is not False for key in FLAGS)
            or data.get('source_original_hashes') != SOURCE_HASHES):
        raise ValueError('OpenEar reference scope changed')
    return data


@lru_cache(maxsize=32)
def _check(path, size, modified, digest):
    raw = Path(path).read_bytes()
    if len(raw) != size or sha(raw) != digest:
        raise ValueError('OpenEar reference source bytes changed')


def validate_file(name):
    if name not in AUTHORED:
        raise ValueError('Unknown OpenEar reference file')
    path = ROOT / 'web/anatomy' / ATLAS / name
    regular(path)
    stat = path.stat()
    row = registry()['files'][name]
    if stat.st_size != row['bytes']:
        raise ValueError('OpenEar reference length changed')
    _check(str(path), stat.st_size, stat.st_mtime_ns, row['sha256'])
    return path


@lru_cache(maxsize=1)
def references():
    data = registry()
    for name in AUTHORED:
        validate_file(name)
    manifest = json.loads(validate_file('manifest.json').read_bytes())
    config = json.loads(validate_file('config.json').read_bytes())
    if (manifest.get('schemaVersion') != 1 or manifest.get('record') != 1473724
            or manifest.get('dataset') != 'OpenEar ZETA' or manifest.get('license') != 'CC BY 4.0'
            or any(manifest.get(k) is not False for k in ('clinicalApproval', 'patientLateralityApproved',
                'patientOrientationApproved', 'intensityCalibrationHUApproved', 'effectiveSpatialResolutionEstablished'))
            or manifest.get('registeredSpacingEqualsReportedAcquisitionVoxelSize') != {'embedded': True, 'unembedded': False}
            or 'registeredSamplingIsAcquisitionResolution' in manifest
            or manifest.get('originalAcquisitionVoxelMm') != {'embedded': .125, 'unembedded': .25}
            or manifest.get('planeCount') != 5640 or len(manifest.get('packs', {})) != 79
            or set(manifest.get('volumes', {})) != {'embedded', 'unembedded', 'masks'}
            or len(manifest.get('meshes', {})) != 13
            or sum(m['triangles'] for m in manifest['meshes'].values()) != 7349910
            or [s['code'] for s in manifest.get('selections', [])] != list(range(14))
            or sum(len(s['components26']) for s in manifest['selections']) != 57
            or manifest['overlap']['originalIndependentBinaryChannels'] != 13
            or manifest['overlap']['additionalSeparateFullBoneChannel'] != 13
            or manifest['overlap']['overlappingOriginalChannelPositions'] != 773
            or manifest['annotationCrop']['offsetXYZ'] != [20, 3, 13]
            or manifest['annotationCrop']['shapeXYZ'] != [641, 579, 475]):
        raise ValueError('OpenEar source interpretation changed')
    if data['files']['manifest.json']['sha256'] != MANIFEST_SHA256:
        raise ValueError('OpenEar fixed source manifest changed')
    if config != {'manifestSHA256': MANIFEST_SHA256,
                  'blobPrefix': BLOB_PREFIX + 'runtime/'}:
        raise ValueError('OpenEar transport configuration changed')
    expected = dict(manifest['packs'])
    for mesh in manifest['meshes'].values():
        for group in mesh['parts'].values():
            offset = 0
            for chunk in group['chunks']:
                if chunk['offset'] != offset or not 0 < chunk['bytes'] <= 4194304 or chunk['bytes'] % 4:
                    raise ValueError('OpenEar bounded geometry changed')
                offset += chunk['bytes']
                expected[chunk['file']] = {'bytes': chunk['gzipBytes'], 'sha256': chunk['gzipSHA256']}
            if offset != group['bytes']:
                raise ValueError('OpenEar geometry is incomplete')
    delivery = data['delivery']
    if (delivery.get('allRemoteHashesMatch') is not True
            or delivery.get('manifestSHA256') != config['manifestSHA256']
            or set(delivery['files']) != set(expected) or len(expected) != 135
            or len(delivery.get('originals', {})) != 17):
        raise ValueError('OpenEar verified delivery is incomplete')
    for name, row in expected.items():
        if delivery['files'][name] != dict(row, url=BLOB_PREFIX+'runtime/'+row['sha256']+'/'+name,
                                          remoteHashVerified=True):
            raise ValueError('OpenEar payload identity changed')
    for name, row in delivery['originals'].items():
        if (row.get('remoteHashVerified') is not True or row.get('bytes', 0) <= 0
                or row.get('url') != BLOB_PREFIX+'originals/'+row['sha256']+'/'+name):
            raise ValueError('OpenEar original delivery changed')
    if {name: delivery['originals'][name]['sha256'] for name in SOURCE_HASHES} != SOURCE_HASHES:
        raise ValueError('OpenEar original volume identities changed')
    names = {r['name'].split(' · ', 1)[0].casefold(): key for key, r in manifest['meshes'].items()}
    for selection in manifest['selections']:
        if selection['bit'] != selection['code']:
            raise ValueError('OpenEar independent mask bit changed')
        name = selection['name'].split(' · ', 1)[0].casefold()
        if selection['meshId'] != names[name]:
            raise ValueError('OpenEar source name/mesh association changed')
    item = data['inspector']
    if (item['id'] != IDENTIFIER or item['src'] != PREFIX+'index.html'
            or item['sha256'] != data['files']['index.html']['sha256']
            or item['manifest_sha256'] != config['manifestSHA256']
            or item['bound_source_ids'] != [IDENTIFIER] or item['license'] != 'CC BY 4.0'
            or item['source_url'] != 'https://zenodo.org/records/1473724'
            or any(item.get(key) is not False for key in FLAGS)):
        raise ValueError('OpenEar source descriptor changed')
    return {key: [item] for key in BINDINGS}
