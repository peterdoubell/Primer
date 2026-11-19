"""LyNoS Pat9 CT, source masks and per-node station descriptions."""
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path

ATLAS = 'lynos-pat9'
DIRECTORY = Path(__file__).resolve().parents[1] / 'web' / 'anatomy' / ATLAS
SOURCE_URL = 'https://zenodo.org/records/10102261'
LICENSE = 'https://creativecommons.org/licenses/by/4.0/'
ARTICLE_URL = 'https://doi.org/10.1080/21681163.2022.2043778'
DELIVERY_SHA256 = '98321690fb9ce983eeb4a607fd087811b096174430764b3d06d8b00cc90e1a04'
ROLES = ('ct', 'nodes', 'azygos', 'brachiocephalic-veins', 'esophagus', 'subclavian-carotid-arteries')
SECTIONS = 241
CHUNK_STARTS = tuple(range(0, SECTIONS, 16))
FILE_GROUPS = {
    'index.html', 'surfaces.html', 'source.json', 'surfaces.json', 'viewer.js',
    'surface-selection.js', 'native-sections.mjs', 'mask-map.mjs', 'mask-map.css',
    *(f'{role}-{first:03d}.gz' for role in ROLES for first in CHUNK_STARTS),
    *(f'node-{index:02d}.mesh.gz' for index in range(1, 45)),
    *(f'{role}.mesh.gz' for role in ROLES[2:]),
}


@lru_cache(maxsize=1)
def delivery():
    raw = (DIRECTORY / 'delivery.json').read_bytes()
    if sha256(raw).hexdigest() != DELIVERY_SHA256:
        raise ValueError('Unexpected LyNoS source delivery inventory')
    files = json.loads(raw)['files']
    if set(files) != FILE_GROUPS:
        raise ValueError('Incomplete LyNoS source delivery inventory')
    for asset, record in files.items():
        path = DIRECTORY / asset
        if path.is_file():
            content = path.read_bytes()
            if len(content) != record['bytes'] or sha256(content).hexdigest() != record['sha256']:
                raise ValueError('LyNoS source asset differs: ' + asset)
        elif not asset.endswith('.gz') or not os.environ.get('VERCEL'):
            raise ValueError('LyNoS source asset missing: ' + asset)
    source = json.loads((DIRECTORY / 'source.json').read_bytes())
    if (source['case'] != 'Pat9' or source['shapeSliceRowColumn'] != [SECTIONS, 512, 512]
            or source['sourceURL'] != SOURCE_URL or source['articleURL'] != ARTICLE_URL
            or source['license'] != LICENSE or set(source['volumes']) != set(ROLES)
            or source['surfaceManifestSHA256'] != files['surfaces.json']['sha256']):
        raise ValueError('LyNoS source metadata differs')
    rows = source['nodalLabels']
    if [row['label'] for row in rows] != list(range(1, 45)):
        raise ValueError('LyNoS source nodes differ')
    for label in ROLES:
        chunks = source['volumes'][label]['chunks']
        if tuple(item['sourceZStart'] for item in chunks) != CHUNK_STARTS:
            raise ValueError('LyNoS native section ranges differ')
        for entry in chunks:
            asset = f"{label}-{entry['sourceZStart']:03d}.gz"
            identity = files[asset]
            if (entry['file'], entry['bytes'], entry['compressedSHA256']) != (
                    asset, identity['bytes'], identity['sha256']):
                raise ValueError('LyNoS native section identity differs')
    return files


def references():
    files = delivery()
    prefix = f'/app/anatomy/{ATLAS}/'
    item = {
        'id': ATLAS,
        'title': 'LyNoS CT with source station assignments and nearby anatomy',
        'caption': ('Inspect 44 original node masks on the complete Pat9 CT, compare their source '
                    'mask map, and isolate their sampled surfaces. The map shows individual node and '
                    'nearby anatomy masks at the acquired spacing, including their overlapping cells. '
                    'Read the authors’ literal station assignments with their conflicts and undefined entries.'),
        'src': prefix + 'index.html',
        'manifest_url': prefix + 'source.json',
        'sha256': files['index.html']['sha256'],
        'manifest_sha256': files['source.json']['sha256'],
        'modality': 'CT',
        'source_url': SOURCE_URL,
        'publication_url': ARTICLE_URL,
        'license': 'CC BY 4.0',
        'license_url': LICENSE,
        'attribution': ('Bouget, Pedersen, Vanel, Leira and Langø. Primer presents all original '
                        'NIfTI samples, the authors’ per-node station terms and voxel-face surfaces.'),
        'clinical_approval': False,
        'fine_anatomical_approval': False,
        'current_patient_registration': False,
        'normal_anatomical_atlas_approval': False,
        'complete_reporting_anatomy_approved': False,
    }
    return {identifier: [dict(item)] for identifier in ('ra.ct-mediastinum', 'ra.ct-lung-cancer')}
