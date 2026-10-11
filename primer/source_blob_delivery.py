"""Pinned public publication assets; byte integrity grants no anatomical approval."""
import hashlib
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/radiology/source-blob-delivery.json'
REGISTRY_SHA256 = 'b633f4ae33b0a41357b06881447df805ef3b24ff61bdc5d37409e75a34a6f818'
INDEPENDENT_REVIEW_SHA256 = '73a9979a40c7407728cdf223c3cbd6b7a3326ffae75d4292abddc6606f33f6d8'
PROJECT_ID = 'prj_AkCCMkedaGlozDzJqTtteq29MAit'
STORE_ID = 'store_JA2lsNp9UCA4bivw'
BLOB_HOST = 'ja2lsnp9uca4bivw.public.blob.vercel-storage.com'
PREFIX = '/app/reference-media/radiology-open/traumatic-haemorrhage/'
BLOB_PREFIX = 'https://' + BLOB_HOST + '/radiology-original/traumatic-haemorrhage/'
MIME = {'png': 'image/png', 'jpg': 'image/jpeg', 'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}


@lru_cache(maxsize=1)
def delivery():
    raw_registry = REGISTRY.read_bytes()
    if hashlib.sha256(raw_registry).hexdigest() != REGISTRY_SHA256:
        raise ValueError('Publication delivery packet differs from the reviewed fingerprint')
    data = json.loads(raw_registry)
    if (data.get('schema_version') != 1 or data.get('project_id') != PROJECT_ID
            or data.get('store_id') != STORE_ID or data.get('blob_hostname') != BLOB_HOST
            or data.get('independent_source_review_sha256') != INDEPENDENT_REVIEW_SHA256
            or data.get('clinical_approval') is not False
            or data.get('fine_anatomical_approval') is not False):
        raise ValueError('Unreviewed publication store, project or approval')
    files = data.get('files')
    if not isinstance(files, dict) or len(files) != 34:
        raise ValueError('Empty publication delivery inventory')
    total = 0
    for src, row in files.items():
        filename = src.removeprefix(PREFIX) if isinstance(src, str) else ''
        if (not isinstance(src, str) or not isinstance(row, dict)
                or not src.startswith(PREFIX) or not re.fullmatch(r'[a-z0-9][a-z0-9.-]*\.(png|jpg|pdf|docx)', filename)
                or not re.fullmatch(r'[a-f0-9]{64}', row.get('sha256', ''))
                or type(row.get('bytes')) is not int or row['bytes'] < 24
                or row.get('content_type') != MIME[filename.rsplit('.', 1)[-1]]
                or row.get('license') != 'CC BY 4.0'
                or row.get('role') not in {'display_raster', 'encoded_pdf_stream', 'publication_pdf', 'source_document'}
                or not isinstance(row.get('url'), str)):
            raise ValueError('Invalid licensed publication asset identity')
        suffix = filename.rsplit('.', 1)[-1]
        if ((row['role'] == 'display_raster' and suffix not in {'png', 'jpg'})
                or (row['role'] == 'encoded_pdf_stream' and suffix != 'jpg')
                or (row['role'] == 'publication_pdf' and suffix != 'pdf')):
            raise ValueError('Publication role differs from its source format')
        url = urlsplit(row.get('url', ''))
        expected = '/radiology-original/traumatic-haemorrhage/' + row['sha256'] + '/' + filename
        if (url.scheme != 'https' or url.netloc != BLOB_HOST or url.hostname != BLOB_HOST
                or url.path != expected or url.query or url.fragment):
            raise ValueError('Publication URL leaves its pinned content-addressed store')
        local = ROOT / 'web' / src.removeprefix('/app/')
        if local.is_file():
            raw = local.read_bytes()
            if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('Local publication differs from reviewed cloud metadata')
        elif not os.environ.get('VERCEL'):
            raise ValueError('Original publication asset is missing locally')
        total += row['bytes']
    if (total != data.get('total_bytes') or total != 38875353
            or len(files) != data.get('file_count')):
        raise ValueError('Publication asset inventory is incomplete')
    return data


def validate_raster_bindings(images, static_inventory):
    """Every registered cloud display must match the existing original raster contract."""
    files = delivery()['files']
    displays = {src: row for src, row in files.items() if row['role'] == 'display_raster'}
    rows = {row['src']: row for row in images if row['src'].startswith(PREFIX)}
    if set(rows) != set(displays):
        raise ValueError('Cloud display assets differ from the reviewed source figure set')
    for src, row in rows.items():
        hosted = static_inventory.get(src)
        if (not hosted or hosted.get('sha256') != row['sha256']
                or hosted.get('sha256') != displays[src]['sha256']
                or hosted.get('bytes') != displays[src]['bytes']
                or (hosted.get('width'), hosted.get('height')) != (row['width'], row['height'])):
            raise ValueError('Cloud figure differs from original source dimensions or bytes')
    return len(rows)


def validate_context_documents(documents):
    expected = {'traumatic-ninds-2025-original-publication': 'ninds-2025-original-publication.pdf',
                'traumatic-ninds-2025-original-supplementary-appendix': 'ninds-2025-original-supplementary-appendix.docx',
                'traumatic-ninds-2025-proposed-template-original': 'ninds-2025-proposed-template-original.jpg'}
    if (not isinstance(documents, list) or len(documents) != 3
            or any(not isinstance(row, dict) for row in documents)
            or {row.get('id') for row in documents} != set(expected)):
        raise ValueError('Unreviewed source-context document scope')
    files = delivery()['files']
    for document in documents:
        source = files.get(document.get('src'))
        if (document.get('src') != PREFIX + expected[document['id']]
                or not source or document.get('sha256') != source['sha256']
                or document.get('bytes') != source['bytes']
                or document.get('mime_type') != source['content_type']
                or document.get('license') != source['license']
                or document.get('unchanged_original') is not True):
            raise ValueError('Source-context document differs from reviewed original')
        if (document.get('source_url') != 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12409119/'
                or document.get('license_url') != 'https://creativecommons.org/licenses/by/4.0/'):
            raise ValueError('Source-context publication or license link changed')
        for flag in ('clinical_approval', 'current_patient_findings', 'patient_registration_verified',
                     'fine_structure_coverage_granted', 'native_patient_registration_verified',
                     'source_case_registration_between_TRACK_TBI_and_CENTER_TBI_established'):
            if document.get(flag, False) is not False:
                raise ValueError('Source document cannot promote clinical or patient-specific approval')
    return 3
