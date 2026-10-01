#!/usr/bin/env python3
"""Verify an NBIA getImageWithMD5Hash archive without changing source bytes."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from pathlib import PurePosixPath
import zipfile


def audit_archive(path, expected_count, expected_dicom_bytes=None):
    path = Path(path)
    records = []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive member')
        if 'md5hashes.csv' not in names:
            raise ValueError('Publisher MD5 manifest missing')
        rows = list(csv.DictReader(io.StringIO(archive.read('md5hashes.csv').decode('utf-8-sig'))))
        listed = [r['Filename'] for r in rows]
        dicom_names = [n for n in names if n.lower().endswith('.dcm')]
        if len(listed) != len(set(listed)) or set(listed) != set(dicom_names) or len(listed) != expected_count:
            raise ValueError('DICOM count or exact publisher manifest membership differs')
        for row in rows:
            name = row['Filename']
            if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                raise ValueError('Unsafe source member name')
            data = archive.read(name)  # zipfile checks CRC as well.
            actual = hashlib.md5(data).hexdigest()
            if actual.lower() != row['MD5Hash'].lower():
                raise ValueError('Publisher MD5 mismatch: ' + name)
            records.append({'member': name, 'bytes': len(data), 'publisher_md5': actual,
                            'sha256': hashlib.sha256(data).hexdigest()})
        total = sum(r['bytes'] for r in records)
        if expected_dicom_bytes is not None and total != expected_dicom_bytes:
            raise ValueError('Uncompressed DICOM bytes differ from series metadata')
    raw = path.read_bytes()
    return {'archive_bytes': len(raw), 'archive_sha256': hashlib.sha256(raw).hexdigest(),
            'archive_sha256_is_local_fingerprint': True, 'publisher_per_file_md5_verified': True,
            'zip_member_crc_verified': True, 'dicom_count': len(records), 'dicom_bytes': total,
            'members': records, 'clinical_approval': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--expected-count', type=int, required=True)
    parser.add_argument('--expected-dicom-bytes', type=int)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit_archive(args.archive, args.expected_count, args.expected_dicom_bytes)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('Verified', report['dicom_count'], 'DICOM files;', report['dicom_bytes'], 'bytes')


if __name__ == '__main__':
    main()
