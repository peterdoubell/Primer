"""Study-specific CC0 MRI reference; source fidelity does not grant clinical approval."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
PREFIX = '/app/anatomy/nextbrain/'
IDENTIFIER = 'nextbrain-exvivo-reference'
BLOB_HOST = 'https://ja2lsnp9uca4bivw.public.blob.vercel-storage.com'
REGISTRY = ROOT / 'data/radiology/nextbrain-reference.json'
REGISTRY_SHA256 = '769f550bcfdec6fe85532e1f02a5a53df25ce1faecd2744c1a434b9683f91968'
FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'current_patient_registration',
         'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved')
AUTHORED = frozenset({'index.html','viewer.js','transport.js','viewer.css','config.json','manifest.json','labels.json'})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def regular(path):
    if any(p.is_symlink() for p in [path, *path.parents] if p == ROOT or ROOT in p.parents):
        raise ValueError('NextBrain asset cannot use a symlink')
    if not path.is_file():
        raise ValueError('NextBrain asset is missing')


@lru_cache(maxsize=1)
def registry():
    regular(REGISTRY)
    raw = REGISTRY.read_bytes()
    if sha(raw) != REGISTRY_SHA256:
        raise ValueError('NextBrain registry changed')
    data = json.loads(raw)
    if (data.get('schema_version') != 1 or set(data.get('files', {})) != AUTHORED
            or data.get('bindings') != ['ra.brain-anatomy']
            or any(data.get(k) is not False for k in FLAGS)
            or data.get('dataset_revision') != '924a8f3412463457a70e0fb141a88a8b57fc7ba6'):
        raise ValueError('NextBrain reference scope changed')
    return data


@lru_cache(maxsize=32)
def _check(path, size, modified, digest):
    raw = Path(path).read_bytes()
    if len(raw) != size or sha(raw) != digest:
        raise ValueError('NextBrain source bytes changed')


def validate_file(name):
    if name not in AUTHORED:
        raise ValueError('Unknown NextBrain file')
    p = ROOT / 'web/anatomy/nextbrain' / name
    regular(p)
    stat = p.stat()
    row = registry()['files'][name]
    if stat.st_size != row['bytes']:
        raise ValueError('NextBrain source length changed')
    _check(str(p), stat.st_size, stat.st_mtime_ns, row['sha256'])
    return p


@lru_cache(maxsize=1)
def references():
    d = registry()
    for name in AUTHORED:
        validate_file(name)
    m = json.loads(validate_file('manifest.json').read_bytes())
    labels = json.loads(validate_file('labels.json').read_bytes())
    config = json.loads(validate_file('config.json').read_bytes())
    if (m['dataset'] != 'ds005422' or m['version'] != '1.0.1'
            or m['sourceRevision'] != d['dataset_revision'] or m['clinicalApproval'] is not False
            or m['license'] != 'CC0' or m['planeCount'] != 4800
            or set(m['volumes']) != {'MRI','labels'} or len(m['packs']) != 39
            or set(m['meshParts']) != {str(i) for i in range(1,99)}
            or sum(r['triangles'] for r in m['meshParts'].values()) != 33496568
            or [r['code'] for r in labels['classes']] != list(range(1,99))
            or labels['clinicalApproval'] is not False or labels['absentCodes'] != [99,100,101]):
        raise ValueError('NextBrain source inventory changed')
    if config != {'manifestSHA256':d['files']['manifest.json']['sha256'],
                  'labelsSHA256':d['files']['labels.json']['sha256'],
                  'blobPrefix':BLOB_HOST+'/radiology-native/nextbrain-ds005422-v1.0.1/runtime/'}:
        raise ValueError('NextBrain source configuration changed')
    expected = dict(m['packs'])
    for mesh in m['meshParts'].values():
        for group in mesh['parts'].values():
            offset = 0
            for chunk in group['chunks']:
                if chunk['offset'] != offset or not 0 < chunk['bytes'] <= 4194304 or chunk['bytes'] % 4:
                    raise ValueError('NextBrain bounded geometry changed')
                offset += chunk['bytes']
                expected[chunk['file']] = {'bytes':chunk['gzipBytes'],'sha256':chunk['gzipSHA256']}
            if offset != group['bytes']:
                raise ValueError('NextBrain geometry incomplete')
    delivery = d['delivery']
    if (delivery.get('allRemoteHashesMatch') is not True or delivery.get('manifestSHA256') != config['manifestSHA256']
            or len(expected) != 333 or set(delivery['files']) != set(expected)):
        raise ValueError('NextBrain delivery incomplete')
    for name, row in expected.items():
        if delivery['files'][name] != dict(row, url=config['blobPrefix']+row['sha256']+'/'+name, remoteHashVerified=True):
            raise ValueError('NextBrain delivery identity changed')
    item = d['inspector']
    if (item['id'] != IDENTIFIER or item['src'] != PREFIX+'index.html'
            or item['sha256'] != d['files']['index.html']['sha256']
            or item['manifest_sha256'] != config['manifestSHA256']
            or item['bound_source_ids'] != [IDENTIFIER] or item['license'] != 'CC0'
            or any(item.get(k) is not False for k in FLAGS)):
        raise ValueError('NextBrain source interpretation changed')
    return {'ra.brain-anatomy':[item]}
