"""Native source CT and original pelvic node masks from Rojas-Pizarro et al."""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re

ANATOMY = Path(__file__).resolve().parents[1] / 'web/anatomy'
DATASET = 'https://zenodo.org/records/17788162'
ARTICLE = 'https://doi.org/10.1038/s41597-026-06597-6'
LICENSE = 'https://creativecommons.org/licenses/by/4.0/'
CASES = {
    'recist-pelvic-015': {
        'investigation': 'ra.mri-bladder',
        'title': 'Pelvic nodes on bladder cancer baseline CT',
        'caption': ('Inspect three original pelvic nodal labels on one acquired CT and isolate their '
                    'sampled 3D boundaries. This case supplies CT nodal context for bladder cancer. '
                    'VI-RADS assesses the bladder tumour on MRI.'),
        'nodes': 3,
        'source_sha256': 'cdf9d1700250b8e773c09ac72c657a135ee68ad75f4d020d281221941cf72a51',
    },
    'recist-pelvic-023': {
        'investigation': 'ra.recist',
        'title': 'Iliac nodes and a 16 mm RECIST target on baseline CT',
        'caption': ('Inspect two source-labelled iliac nodes on the baseline CT and isolate their '
                    'sampled 3D boundaries. The authors measured node 1 at 16 mm on its axial short '
                    'axis as target A. This single scan illustrates the baseline measurement context.'),
        'nodes': 2,
        'source_sha256': '441e5d7bd0c9592a0aafdfcae45ef031ab9a7c168175c0884b7a827fedbd70ee',
    },
}


@lru_cache(maxsize=len(CASES))
def delivery(case_id):
    """Validate the exact case inventory and any assets resident in the function."""
    directory = ANATOMY / case_id
    case = CASES[case_id]
    files = json.loads((directory / 'delivery.json').read_bytes())['files']
    expected = {'index.html', 'surfaces.html', 'source.json', 'surfaces.json',
                'ct-int16.gz', 'labels-int16.gz'}
    expected.update(f'node-{label}.mesh.gz' for label in range(1, case['nodes'] + 1))
    if set(files) != expected or files['source.json']['sha256'] != case['source_sha256']:
        raise ValueError('Pelvic source case inventory differs')
    for asset, record in files.items():
        if (type(record.get('bytes')) is not int or record['bytes'] <= 0
                or not re.fullmatch(r'[0-9a-f]{64}', record.get('sha256', ''))):
            raise ValueError('Invalid pelvic source asset identity')
        path = directory / asset
        if path.is_file():
            raw = path.read_bytes()
            if len(raw) != record['bytes'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
                raise ValueError('Pelvic source asset bytes differ')
        elif not asset.endswith('.gz') or not os.environ.get('VERCEL'):
            raise ValueError('Pelvic source asset missing')
    source = json.loads((directory / 'source.json').read_bytes())
    if (source['case'] != case_id.rsplit('-', 1)[1]
            or source['sourceURL'] != DATASET or source['articleURL'] != ARTICLE
            or source['license'] != LICENSE
            or source['surfaceManifestSHA256'] != files['surfaces.json']['sha256']):
        raise ValueError('Pelvic source case provenance differs')
    for role, asset in (('ct', 'ct-int16.gz'), ('labels', 'labels-int16.gz')):
        volume = source['volumes'][role]
        if (volume['file'] != asset or volume['bytes'] != files[asset]['bytes']
                or volume['compressedSHA256'] != files[asset]['sha256']):
            raise ValueError('Pelvic source volume identity differs')
    return files


def references():
    result = {}
    for case_id, case in CASES.items():
        files = delivery(case_id)
        prefix = f'/app/anatomy/{case_id}/'
        result[case['investigation']] = [{
            'id': case_id,
            'title': case['title'],
            'caption': case['caption'],
            'src': prefix + 'index.html',
            'manifest_url': prefix + 'source.json',
            'sha256': files['index.html']['sha256'],
            'manifest_sha256': files['source.json']['sha256'],
            'modality': 'CT',
            'source_url': DATASET,
            'publication_url': ARTICLE,
            'license': 'CC BY 4.0',
            'license_url': LICENSE,
            'attribution': ('Rojas-Pizarro and colleagues, University of Chile clinical hospital, '
                            'Zenodo 10.5281/zenodo.17788162. Primer crops the original CT and masks '
                            'without resampling and displays the source voxel boundaries.'),
            'clinical_approval': False,
            'fine_anatomical_approval': False,
            'current_patient_registration': False,
            'normal_anatomical_atlas_approval': False,
            'complete_reporting_anatomy_approved': False,
        }]
    return result
