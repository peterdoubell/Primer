"""Acquired CT and the original LNQ mediastinal annotation."""
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import re

ATLAS = 'lnq-case-0571'
DIRECTORY = Path(__file__).resolve().parents[1] / 'web' / 'anatomy' / ATLAS
SOURCE_URL = 'https://doi.org/10.7937/QVAZ-JA09'
LICENSE = 'https://creativecommons.org/licenses/by/4.0/'
SOURCE_SHA256 = 'c9308f6d835d40d95d20eca75998dd99e13f500a068426a44a4ca62f534babf9'
FILES = frozenset({
    'index.html', 'surfaces.html', 'source.json', 'surfaces.json',
    'ct-int16.gz', 'labels-int16.gz', *(f'component-{i}.mesh.gz' for i in range(1, 6)),
})


@lru_cache(maxsize=1)
def delivery():
    files = json.loads((DIRECTORY / 'delivery.json').read_bytes())['files']
    if set(files) != FILES or files['source.json']['sha256'] != SOURCE_SHA256:
        raise ValueError('Unexpected LNQ source inventory')
    for asset, record in files.items():
        if (type(record.get('bytes')) is not int or record['bytes'] <= 0
                or not re.fullmatch(r'[a-f0-9]{64}', record.get('sha256', ''))):
            raise ValueError('Invalid LNQ asset identity')
        path = DIRECTORY / asset
        if path.is_file():
            raw = path.read_bytes()
            if len(raw) != record['bytes'] or sha256(raw).hexdigest() != record['sha256']:
                raise ValueError('LNQ source asset differs')
        elif not asset.endswith('.gz') or not os.environ.get('VERCEL'):
            raise ValueError('LNQ source asset missing')
    source = json.loads((DIRECTORY / 'source.json').read_bytes())
    if source['surfaceManifestSHA256'] != files['surfaces.json']['sha256']:
        raise ValueError('LNQ surface manifest differs')
    for label, asset in (('ct', 'ct-int16.gz'), ('labels', 'labels-int16.gz')):
        volume = source['volumes'][label]
        entry = files[asset]
        if (volume['file'], volume['bytes'], volume['compressedSHA256']) != (asset, entry['bytes'], entry['sha256']):
            raise ValueError('LNQ volume manifest differs')
    return files


def references():
    files = delivery()
    prefix = f'/app/anatomy/{ATLAS}/'
    item = {
        'id': ATLAS,
        'title': 'Mediastinal lymph node annotation on source CT',
        'caption': ('Inspect the publisher’s original LNQ annotation on the acquired mediastinal CT of '
                    'case 0571. Toggle its five connected components on unmarked images and isolate '
                    'their sampled boundaries in 3D. The source records non-small-cell lung cancer as '
                    'the primary condition. The components retain the publisher’s single lymph-node label.'),
        'src': prefix + 'index.html',
        'manifest_url': prefix + 'source.json',
        'sha256': files['index.html']['sha256'],
        'manifest_sha256': SOURCE_SHA256,
        'modality': 'CT',
        'source_url': SOURCE_URL,
        'publication_url': 'https://lnqproject.org/datasets/#methodology',
        'license': 'CC BY 4.0',
        'license_url': LICENSE,
        'attribution': ('Idris and colleagues, Mediastinal Lymph Node Quantification (LNQ), '
                        'The Cancer Imaging Archive. Primer presents the lossless source CT band and '
                        'manual SEG with separable display components.'),
        'clinical_approval': False,
        'fine_anatomical_approval': False,
        'current_patient_registration': False,
        'normal_anatomical_atlas_approval': False,
        'complete_reporting_anatomy_approved': False,
    }
    return {identifier: [dict(item)] for identifier in ('ra.ct-mediastinum', 'ra.ct-lung-cancer')}
