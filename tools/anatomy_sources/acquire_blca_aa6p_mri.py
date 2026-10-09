#!/usr/bin/env python3
"""Acquire the complete, explicitly selected public TCGA bladder MRI study unchanged."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

from tools.anatomy_sources.audit_tcia_series_archive import audit_archive

CASE = 'TCGA-DK-AA6P'
STUDY = '1.3.6.1.4.1.14519.5.2.1.9203.4016.142258435654094518230804693190'


def validate_selection(rows):
    if not isinstance(rows, list) or len(rows) != 22:
        raise ValueError('Need all 22 source MRI series, not a selected appearance')
    if len({r['SeriesInstanceUID'] for r in rows}) != 22 or len({int(r['SeriesNumber']) for r in rows}) != 22:
        raise ValueError('Duplicate source series identity')
    for row in rows:
        if (row['PatientID'] != CASE or row['StudyInstanceUID'] != STUDY
                or row['Collection'] != 'TCGA-BLCA' or row['Modality'] != 'MR'
                or row['LicenseURI'].replace('http:', 'https:') != 'https://creativecommons.org/licenses/by/3.0/'
                or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)+', row['SeriesInstanceUID'])
                or not 1 <= int(row['SeriesNumber']) <= 9999
                or int(row['ImageCount']) <= 0 or int(row['FileSize']) <= 0):
            raise ValueError('Original source identity/licence/declaration changed')
    if sum(int(r['ImageCount']) for r in rows) != 1359:
        raise ValueError('Complete original object count changed')
    return sorted(rows, key=lambda r: int(r['SeriesNumber']))


def acquire(selection_path, output):
    raw = selection_path.read_bytes()
    rows = validate_selection(json.loads(raw))
    output.mkdir(parents=True, exist_ok=True)
    def series(row):
        number = int(row['SeriesNumber'])
        path = output / f'series-{number:04d}.zip'
        partial = path.with_suffix('.zip.partial')
        if partial.exists():
            raise ValueError('Partial source writer requires inspection, not an automatic restart')
        url = 'https://services.cancerimagingarchive.net/nbia-api/services/v1/getImageWithMD5Hash?' + urllib.parse.urlencode({'SeriesInstanceUID': row['SeriesInstanceUID']})
        if not path.exists():
            with urllib.request.urlopen(url, timeout=120) as response, partial.open('xb') as target:
                total = 0
                for chunk in iter(lambda: response.read(1024 * 1024), b''):
                    target.write(chunk)
                    total += len(chunk)
                expected = response.headers.get('Content-Length')
                if expected is not None and total != int(expected):
                    raise ValueError('Incomplete source HTTP body')
            partial.rename(path)
        proof = audit_archive(path, int(row['ImageCount']), int(row['FileSize']))
        proof.update(source_series=row, download_url=url, source_selection_sha256=hashlib.sha256(raw).hexdigest(),
                     original_source_values_changed=False, runtime_promoted=False)
        (output / f'series-{number:04d}-receipt.json').write_text(json.dumps(proof, indent=2) + '\n')
        print('Verified', number, row['SeriesDescription'], proof['dicom_count'], 'objects', flush=True)
        return proof
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(series, rows))
    summary = {'case_id': CASE, 'study_instance_uid': STUDY, 'source_doi': '10.7937/K9/TCIA.2016.8LNG8XDR',
               'source_selection_sha256': hashlib.sha256(raw).hexdigest(), 'source_series': len(receipts),
               'source_objects': sum(r['dicom_count'] for r in receipts),
               'source_dicom_bytes': sum(r['dicom_bytes'] for r in receipts),
               'all_publisher_per_object_MD5_and_archive_CRC_verified': True,
               'clinical_or_anatomical_approval': False, 'runtime_promoted': False,
               'series_receipts': [f"series-{int(r['source_series']['SeriesNumber']):04d}-receipt.json" for r in receipts]}
    (output / 'acquisition-review.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selection', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    acquire(args.selection, args.output)
