"""Original curated thoracic surface delivery; no anatomical completeness approval."""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = '/app/anatomy/bp3d-thoracic-4.3/'
REGISTRY = ROOT / 'data/radiology/thoracic-native-inspector.json'
REGISTRY_SHA256 = 'bb50872977be596fc9a98dec24f114e0dfb0c49ae80aefe6f05270d464e37ae0'
AUTHORED = frozenset({'reference.html', 'reference.js', 'manifest.json', 'LICENSE.html'})
PARTS = frozenset({'FJ1451','FJ1451M','FJ1454','FJ1454M','FJ1455','FJ1455M','FJ2420','FJ2421','FJ2432','FJ2433','FJ2436','FJ3131'})


@lru_cache(maxsize=1)
def registry():
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError('Thoracic source registry changed')
    data = json.loads(raw)
    expected = set(AUTHORED) | {f'{folder}/{part}.{suffix}.gz' for part in PARTS
                                for folder, suffix in [('transport', 'bin'), ('originals', 'obj')]}
    if (data.get('schema_version') != 1 or set(data.get('files', {})) != expected
            or set(data.get('parts', [])) != PARTS or data.get('total_source_faces') != 649480
            or data.get('bindings') != {'ra.thoracic-ultrasound': ['bp3d-thoracic-original-surfaces']}
            or set(data.get('inspectors', {})) != {'bp3d-thoracic-original-surfaces'}):
        raise ValueError('Thoracic source scope differs')
    return data


def validate_file(asset):
    data = registry()
    if asset not in data['files']:
        raise ValueError('Unknown thoracic source asset')
    row = data['files'][asset]
    path = ROOT / 'web/anatomy/bp3d-thoracic-4.3' / asset
    if path.is_file():
        raw = path.read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Original thoracic source bytes changed')
    elif asset in AUTHORED or not os.environ.get('VERCEL'):
        raise ValueError('Thoracic source asset missing')
    return path


@lru_cache(maxsize=1)
def references():
    data = registry()
    for asset in data['files']:
        validate_file(asset)
    item = data['inspectors']['bp3d-thoracic-original-surfaces']
    if (item.get('modality') != 'Curated 3D anatomy' or item.get('src') != PREFIX+'reference.html'
            or item.get('manifest_url') != PREFIX+'manifest.json'
            or item.get('bound_source_ids') != ['bp3d-thoracic-original-surfaces']
            or any(item.get(flag) is not False for flag in ['clinical_approval','fine_anatomical_approval',
                                                           'current_patient_registration','complete_reporting_anatomy_approved'])):
        raise ValueError('Thoracic source label, binding or approval differs')
    manifest = json.loads(validate_file('manifest.json').read_text())
    if (set(part['id'] for part in manifest['parts']) != PARTS
            or sum(part['faces'] for part in manifest['parts']) != 649480
            or any(manifest.get(flag) is not False for flag in ['clinical_approval','current_patient_registration','source_acquisition_resolution_verified'])):
        raise ValueError('Thoracic source manifest scope or approval differs')
    for part in manifest['parts']:
        if (part['file'] != 'transport/'+part['id']+'.bin.gz'
                or part['source_obj'] != 'originals/'+part['id']+'.obj.gz'
                or part['transport_sha256'] != data['files'][part['file']]['sha256']
                or part['all_face_indices_preserved_in_order'] is not True
                or part['original_authored_normals_retained'] is not True):
            raise ValueError('Thoracic source transport differs')
    return {'ra.thoracic-ultrasound': [item]}
