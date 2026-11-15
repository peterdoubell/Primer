"""Exact source identities for one released LIDC study; source fidelity is not approval."""
from collections import Counter
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/radiology/pulmonary-source-delivery.json'
REGISTRY_SHA256 = 'dc85f989d10940b2674b72e80d845765f03486fc53f9ca9dbbdd54d9416a8cd6'
REVIEW_SHA256 = 'bbfee4f5cb3be1466884c6900006f924a2634c25f589e5a110ed1914b2c42734'
PROPOSAL_SHA256 = '95e54b8da2e07885e473245ef9815ef14e360621fa9ef0abf9e4cff6afcc514d'
MANIFEST_SHA256 = 'e9c1a47e9c3a7e8e5ad441c5e66c45fbb32e136908aebd2e7a640faf60290c31'
PROJECT_ID = 'prj_AkCCMkedaGlozDzJqTtteq29MAit'
TEAM_ID = 'team_uugEwCrCXYWxwsADiEYhKfwD'
STORE_ID = 'store_JA2lsNp9UCA4bivw'
BLOB_HOST = 'ja2lsnp9uca4bivw.public.blob.vercel-storage.com'
PREFIX = '/app/anatomy/lidc-idri-0525/'
BLOB_PREFIX = 'https://' + BLOB_HOST + '/anatomy/lidc-idri-0525/'
SOURCE_URL = 'https://doi.org/10.7937/K9/TCIA.2015.LO9QL9SX'
ANNOTATION_SOURCE_URL = 'https://doi.org/10.7937/TCIA.2018.h7umfurq'
LICENSE_URL = 'https://creativecommons.org/licenses/by/3.0/'
APPROVAL_FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'structure_coverage_granted',
                  'current_patient_registration', 'whole_goal_complete')
AUTHORED_FILES = frozenset({'reference.html', 'reference.js', 'manifest.json'})
ANNOTATIONS = frozenset({'annotation-0', 'annotation-2', 'annotation-13688', 'annotation-13706',
                         'annotation-50449', 'annotation-50456', 'annotation-50468', 'annotation-57914'})
SOURCE_ARCHIVES = frozenset({
    'source-1.2.276.0.7230010.3.1.3.0.35176.1553319157.186906.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35177.1553319161.680638.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35178.1553319166.368613.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35179.1553319170.839038.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35180.1553319176.311398.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35181.1553319180.897685.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35182.1553319186.851619.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35183.1553319191.423540.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35184.1553319197.160727.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35186.1553319201.751894.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35187.1553319207.534442.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35188.1553319212.110028.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35226.1553319218.3722.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35227.1553319222.562792.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35228.1553319228.101798.zip',
    'source-1.2.276.0.7230010.3.1.3.0.35229.1553319232.593914.zip',
})


def expected_files():
    """Only original-ct is a legitimate nested namespace, with 429 literal names."""
    files = {'original-ct/' + format(i, '08d') + '.dcm': ('unchanged-original-CT-DICOM', 'application/dicom')
             for i in range(1, 430)}
    files.update({name: ('unchanged-released-SEG-SR-archive', 'application/zip') for name in SOURCE_ARCHIVES})
    for name in ANNOTATIONS:
        for suffix, role in [('mask', 'lossless-complete-released-SEG-array'),
                             ('mesh', 'literal-native-SEG-boundary'), ('faces', 'native-SEG-face-oracle')]:
            files[name + '.' + suffix + '.gz'] = (role, 'application/gzip')
    for first, stop in [(0, 63), (64, 127), (128, 191), (192, 255), (256, 319), (320, 383), (384, 428)]:
        files[f'ct.native.{first:03d}-{stop:03d}.gz'] = ('lossless-complete-CT-chunk', 'application/gzip')
    files.update({'original-0525.xml': ('unchanged-source-XML-or-checksum-file', 'application/xml'),
                  'ct-source-md5.csv': ('unchanged-source-XML-or-checksum-file', 'text/csv'),
                  'LICENSE': ('source-license-or-attribution', 'text/plain'),
                  'ATTRIBUTION.txt': ('source-license-or-attribution', 'text/plain')})
    return files


def no_approval(data):
    if any(data.get(flag) is not False for flag in APPROVAL_FLAGS):
        raise ValueError('Pulmonary source packet cannot grant clinical, anatomy or patient approval')


def validate_local_file(src, row):
    local = ROOT / 'web' / src.removeprefix('/app/')
    if local.exists() or local.is_symlink():
        if (not local.is_file() or local.is_symlink()
                or not local.resolve().is_relative_to((ROOT / 'web/anatomy/lidc-idri-0525').resolve())):
            raise ValueError('Pulmonary source path is not an unchanged regular file')
        body = local.read_bytes()
        if len(body) != row['bytes'] or hashlib.sha256(body).hexdigest() != row['sha256']:
            raise ValueError('Present pulmonary source bytes differ from reviewed source')
    elif not os.environ.get('VERCEL'):
        raise ValueError('Original pulmonary source is absent locally')


@lru_cache(maxsize=1)
def delivery():
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError('Pulmonary delivery differs from its reviewed fingerprint')
    data = json.loads(raw)
    no_approval(data)
    identities = {'schema_version': 1, 'project_id': PROJECT_ID, 'team_id': TEAM_ID, 'store_id': STORE_ID,
                  'blob_hostname': BLOB_HOST, 'investigation_id': 'ra.ct-pulmonary-nodules',
                  'module_id': 'rad.4.pulmonary-nodule', 'source_case': 'LIDC-IDRI-0525',
                  'source_proposal_sha256': PROPOSAL_SHA256, 'independent_source_review_sha256': REVIEW_SHA256,
                  'manifest_sha256': MANIFEST_SHA256, 'source_url': SOURCE_URL,
                  'annotation_source_url': ANNOTATION_SOURCE_URL, 'license': 'CC BY 3.0',
                  'license_url': LICENSE_URL, 'file_count': 480, 'total_bytes': 370135064}
    if any(data.get(key) != value for key, value in identities.items()):
        raise ValueError('Unreviewed pulmonary source, project, store, rights or inventory')
    files = data.get('files')
    expected = expected_files()
    if not isinstance(files, dict) or set(files) != {PREFIX + name for name in expected}:
        raise ValueError('Pulmonary source namespace is incomplete or contains an arbitrary path')
    counts, totals = Counter(), Counter()
    for src, row in files.items():
        if not isinstance(row, dict):
            raise ValueError('Invalid pulmonary source row')
        no_approval(row)
        name = src.removeprefix(PREFIX)
        role, mime = expected[name]
        original = role.startswith('unchanged-') or role == 'source-license-or-attribution'
        if (row.get('role') != role or row.get('content_type') != mime or row.get('license') != 'CC BY 3.0'
                or row.get('source_values_changed') is not False
                or row.get('source_original_bytes_changed') is not (False if original else None)
                or not re.fullmatch(r'[a-f0-9]{64}', row.get('sha256', ''))
                or type(row.get('bytes')) is not int or row['bytes'] < 24):
            raise ValueError('Pulmonary source role, type, hash or unchanged original identity differs')
        if not isinstance(row.get('url'), str):
            raise ValueError('Pulmonary source has no fixed URL')
        url = urlsplit(row['url'])
        if (url.scheme != 'https' or url.netloc != BLOB_HOST or url.hostname != BLOB_HOST
                or url.path != '/anatomy/lidc-idri-0525/' + row['sha256'] + '/' + name
                or url.query or url.fragment):
            raise ValueError('Pulmonary URL leaves its exact content-addressed source namespace')
        validate_local_file(src, row)
        counts[role] += 1
        totals[role] += row['bytes']
    if counts != Counter(role for role, mime in expected.values()) or totals != Counter({
            'unchanged-original-CT-DICOM': 225717122, 'unchanged-released-SEG-SR-archive': 204956,
            'lossless-complete-CT-chunk': 143845449, 'lossless-complete-released-SEG-array': 20985,
            'literal-native-SEG-boundary': 71585, 'native-SEG-face-oracle': 17882,
            'unchanged-source-XML-or-checksum-file': 252311, 'source-license-or-attribution': 4774}):
        raise ValueError('Pulmonary source role counts or exact source byte totals changed')
    return data
