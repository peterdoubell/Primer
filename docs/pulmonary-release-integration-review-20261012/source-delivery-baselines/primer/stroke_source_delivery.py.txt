"""Pinned stroke publication and source-native packets; fidelity is not clinical approval."""
import hashlib
import json
import os
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/radiology/acute-stroke-source-delivery.json'
REGISTRY_SHA256 = '5dd069f8237dc81aed27d421bfab395da5aefc0c3fb9a3edd915675a114234a2'
CTP_REVIEW_SHA256 = '4af86b0db18667fd1b5af5e3c8244e7654828d4b2c0cfa5584de1b2f9deecde4'
SOOP_REVIEW_SHA256 = '5f51f80d3bf56d412fc81e825927f1415e19d59fc1409651fab5a667836a9902'
SOOP_PROPOSAL_SHA256 = '640b646f74ba254aa4e4f864e643bd9462b52429ee79849be22ffe131cd1cd2d'
PROJECT_ID = 'prj_AkCCMkedaGlozDzJqTtteq29MAit'
STORE_ID = 'store_JA2lsNp9UCA4bivw'
BLOB_HOST = 'ja2lsnp9uca4bivw.public.blob.vercel-storage.com'
PUBLICATION_PREFIX = '/app/reference-media/radiology-open/acute-stroke/'
NATIVE_PREFIX = '/app/anatomy/soop-stroke-sub342/'
PUBLICATION_BLOB_PREFIX = 'https://' + BLOB_HOST + '/radiology-original/acute-stroke/'
NATIVE_BLOB_PREFIX = 'https://' + BLOB_HOST + '/anatomy/soop-stroke-sub342/'
MIME = {'png': 'image/png', 'jpg': 'image/jpeg', 'pdf': 'application/pdf',
        'gz': 'application/gzip', 'json': 'application/json'}
APPROVAL_FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'structure_coverage_granted',
                  'current_patient_registration', 'whole_goal_complete')


def _no_approval(data):
    if any(data.get(flag) is not False for flag in APPROVAL_FLAGS):
        raise ValueError('Source packet cannot grant anatomical, clinical or patient registration approval')


@lru_cache(maxsize=1)
def delivery():
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError('Stroke delivery packet differs from its reviewed fingerprint')
    data = json.loads(raw)
    _no_approval(data)
    if (data.get('schema_version') != 1 or data.get('project_id') != PROJECT_ID
            or data.get('store_id') != STORE_ID or data.get('blob_hostname') != BLOB_HOST
            or data.get('investigation_id') != 'ra.acute-stroke' or data.get('module_id') != 'rad.4.stroke'
            or data.get('independent_ctp_source_review_sha256') != CTP_REVIEW_SHA256
            or data.get('independent_soop_source_review_sha256') != SOOP_REVIEW_SHA256
            or data.get('soop_source_proposal_sha256') != SOOP_PROPOSAL_SHA256
            or data.get('soop_pinned_root_tree') != 'a62344db73f18f384a95b452f4a1a423087e059b'):
        raise ValueError('Unreviewed stroke scope, source, store or project')
    files = data.get('files')
    if not isinstance(files, dict) or len(files) != 48:
        raise ValueError('Incomplete stroke source delivery inventory')
    counts = Counter()
    totals = Counter()
    for src, row in files.items():
        if not isinstance(src, str) or not isinstance(row, dict):
            raise ValueError('Invalid stroke file identity')
        _no_approval(row)
        publication = src.startswith(PUBLICATION_PREFIX)
        native = src.startswith(NATIVE_PREFIX)
        if publication == native:
            raise ValueError('Stroke delivery escapes its two reviewed source directories')
        prefix = PUBLICATION_PREFIX if publication else NATIVE_PREFIX
        filename = src.removeprefix(prefix)
        suffix = filename.rsplit('.', 1)[-1]
        if (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.(png|jpg|pdf|gz|json)', filename)
                or not re.fullmatch(r'[a-f0-9]{64}', row.get('sha256', ''))
                or type(row.get('bytes')) is not int or row['bytes'] < 24
                or row.get('content_type') != MIME.get(suffix)
                or row.get('license') != ('CC BY 4.0' if publication else 'CC0')
                or row.get('source_values_changed') is not False):
            raise ValueError('Invalid licensed stroke asset identity or unchanged values')
        role = row.get('role')
        if publication:
            valid = {'display_raster': 'png', 'publisher_original_raster': 'jpg', 'publication_pdf': 'pdf'}
            blob_prefix = '/radiology-original/acute-stroke/'
        else:
            valid = {'source_original': suffix if suffix in {'gz', 'json'} else None,
                     'complete_native_storage_array': 'gz', 'source_mask_cell_geometry': 'gz'}
            blob_prefix = '/anatomy/soop-stroke-sub342/'
            if row.get('source_original_bytes_changed') is not (False if role == 'source_original' else None):
                raise ValueError('Native packet must distinguish unchanged originals from derived transport')
        if valid.get(role) != suffix:
            raise ValueError('Stroke asset role differs from its original or transport format')
        if not isinstance(row.get('url'), str):
            raise ValueError('Stroke asset has no fixed URL')
        url = urlsplit(row['url'])
        if (url.scheme != 'https' or url.netloc != BLOB_HOST or url.hostname != BLOB_HOST
                or url.path != blob_prefix + row['sha256'] + '/' + filename or url.query or url.fragment):
            raise ValueError('Stroke URL leaves its pinned content-addressed store')
        local = ROOT / 'web' / src.removeprefix('/app/')
        if local.is_file():
            original = local.read_bytes()
            if len(original) != row['bytes'] or hashlib.sha256(original).hexdigest() != row['sha256']:
                raise ValueError('Local stroke bytes differ from source metadata')
        elif not os.environ.get('VERCEL'):
            raise ValueError('Original stroke source is absent locally')
        packet = 'ctp' if publication else 'soop'
        counts[packet, role] += 1
        totals[packet] += row['bytes']
    if (counts != Counter({('ctp', 'display_raster'): 13, ('ctp', 'publisher_original_raster'): 13,
                          ('ctp', 'publication_pdf'): 1, ('soop', 'source_original'): 11,
                          ('soop', 'complete_native_storage_array'): 7, ('soop', 'source_mask_cell_geometry'): 3})
            or totals != Counter(ctp=37429274, soop=105836672)
            or data.get('file_count') != 48 or data.get('total_bytes') != 143265946):
        raise ValueError('Stroke source packet is incomplete or roles changed')
    return data


def validate_raster_bindings(images, static_inventory):
    displays = {src: row for src, row in delivery()['files'].items() if row['role'] == 'display_raster'}
    rows = {row['src']: row for row in images if row['src'].startswith(PUBLICATION_PREFIX)}
    if set(rows) != set(displays):
        raise ValueError('Stroke cloud display set differs from complete source figures')
    for src, row in rows.items():
        hosted = static_inventory.get(src)
        if (not hosted or hosted.get('sha256') != row['sha256'] or hosted.get('sha256') != displays[src]['sha256']
                or hosted.get('bytes') != displays[src]['bytes']
                or (hosted.get('width'), hosted.get('height')) != (row['width'], row['height'])):
            raise ValueError('Stroke display differs from native source dimensions or bytes')
    return len(rows)
