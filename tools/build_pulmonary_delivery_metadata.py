"""Create local delivery metadata from the frozen, independently reviewed source packet.

This tool has no network operations and never uploads, deploys, or edits source files.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / 'docs/pulmonary-nodule-source-review-20261011/integration-proposal.json'
PROPOSAL_SHA256 = '95e54b8da2e07885e473245ef9815ef14e360621fa9ef0abf9e4cff6afcc514d'
REVIEW_SHA256 = 'bbfee4f5cb3be1466884c6900006f924a2634c25f589e5a110ed1914b2c42734'
PREFIX = '/app/anatomy/lidc-idri-0525/'
HOST = 'ja2lsnp9uca4bivw.public.blob.vercel-storage.com'
FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'structure_coverage_granted',
         'current_patient_registration', 'whole_goal_complete')


def registry():
    raw = PROPOSAL.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROPOSAL_SHA256:
        raise ValueError('Pulmonary proposal has changed')
    review = ROOT / 'docs/pulmonary-nodule-independent-review-20261011/independent-review.json'
    if hashlib.sha256(review.read_bytes()).hexdigest() != REVIEW_SHA256:
        raise ValueError('Pulmonary independent review has changed')
    files = {}
    for row in json.loads(raw)['runtime_files']:
        if row['role'] == 'authored-viewer-or-reviewed-manifest':
            continue
        name = row['relative_path']
        source = ROOT / row['path']
        body = source.read_bytes()
        if len(body) != row['bytes'] or hashlib.sha256(body).hexdigest() != row['sha256']:
            raise ValueError('Frozen pulmonary source bytes changed: ' + name)
        suffix = name.rsplit('.', 1)[-1]
        mime = {'gz': 'application/gzip', 'zip': 'application/zip', 'dcm': 'application/dicom',
                'xml': 'application/xml', 'csv': 'text/csv', 'txt': 'text/plain', 'LICENSE': 'text/plain'}[suffix]
        original = row['role'].startswith('unchanged-') or row['role'] == 'source-license-or-attribution'
        files[PREFIX + name] = {
            'sha256': row['sha256'], 'bytes': row['bytes'], 'role': row['role'],
            'content_type': mime, 'license': 'CC BY 3.0',
            'url': 'https://' + HOST + '/anatomy/lidc-idri-0525/' + row['sha256'] + '/' + name,
            'source_values_changed': False,
            'source_original_bytes_changed': False if original else None,
            **dict.fromkeys(FLAGS, False),
        }
    if len(files) != 480 or sum(row['bytes'] for row in files.values()) != 370135064:
        raise ValueError('Incomplete pulmonary source packet')
    return {
        'schema_version': 1, 'project_id': 'prj_AkCCMkedaGlozDzJqTtteq29MAit',
        'team_id': 'team_uugEwCrCXYWxwsADiEYhKfwD', 'store_id': 'store_JA2lsNp9UCA4bivw',
        'blob_hostname': HOST, 'investigation_id': 'ra.ct-pulmonary-nodules',
        'module_id': 'rad.4.pulmonary-nodule', 'source_case': 'LIDC-IDRI-0525',
        'source_proposal_sha256': PROPOSAL_SHA256,
        'independent_source_review_sha256': REVIEW_SHA256,
        'manifest_sha256': 'e9c1a47e9c3a7e8e5ad441c5e66c45fbb32e136908aebd2e7a640faf60290c31',
        'source_url': 'https://doi.org/10.7937/K9/TCIA.2015.LO9QL9SX',
        'annotation_source_url': 'https://doi.org/10.7937/TCIA.2018.h7umfurq',
        'license': 'CC BY 3.0', 'license_url': 'https://creativecommons.org/licenses/by/3.0/',
        'file_count': 480, 'total_bytes': 370135064, 'files': files,
        **dict.fromkeys(FLAGS, False),
    }


if __name__ == '__main__':
    path = ROOT / 'data/radiology/pulmonary-source-delivery.json'
    path.write_text(json.dumps(registry(), indent=2, ensure_ascii=False) + '\n')
    print(hashlib.sha256(path.read_bytes()).hexdigest())
