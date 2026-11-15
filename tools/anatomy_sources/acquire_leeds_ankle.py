#!/usr/bin/env python3
"""Acquire the public CC BY4.0 Leeds ankle candidate into research staging.

No application publication or clinical approval. Fixed official public URLs;
no access-control workarounds, archive execution, or bulk image acquisition.
"""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

STAGE = Path('/tmp/primer-msk-sources/ankle-next/leeds-1207')
FILES = {
    'landing.html': 'https://archive.researchdata.leeds.ac.uk/1016/',
    'readme.txt': 'https://archive.researchdata.leeds.ac.uk/1016/1/readme.txt',
    'datacite.json': 'https://api.datacite.org/dois/10.5518/1207',
    'FE_input_files.zip': 'https://archive.researchdata.leeds.ac.uk/1016/7/FE_input_files.zip',
    'publication.pdf': 'https://eprints.whiterose.ac.uk/id/eprint/190744/1/TalbotEtAl_2022_ClinicalBiomechanics.pdf',
}
LIMIT = 400_000_000


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    records = []
    for name, url in FILES.items():
        path = STAGE / name
        if not path.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                if int(response.headers.get('Content-Length', '0')) > LIMIT:
                    raise ValueError('Source exceeds bounded download size')
                temporary = path.with_suffix(path.suffix + '.partial')
                total = 0
                with temporary.open('wb') as stream:
                    while True:
                        block = response.read(1024 * 1024)
                        if not block:
                            break
                        total += len(block)
                        if total > LIMIT:
                            raise ValueError('Source exceeds bounded download size')
                        stream.write(block)
                temporary.replace(path)
        body = path.read_bytes()
        records.append({'file': name, 'source_url': url, 'bytes': len(body),
                        'sha256': hashlib.sha256(body).hexdigest(), 'md5': hashlib.md5(body).hexdigest()})
        print(name, len(body), records[-1]['sha256'], flush=True)
    archive = STAGE / 'FE_input_files.zip'
    # Published Content-MD5 / ETag from the official archive response.
    assert hashlib.md5(archive.read_bytes()).hexdigest() == 'a4f366536171f223eb708bb7d5208a41'
    with zipfile.ZipFile(archive) as source:
        members = [{'name': member.filename, 'bytes': member.file_size,
                    'compressed_bytes': member.compress_size, 'crc32': f'{member.CRC:08x}'}
                   for member in source.infolist()]
    report = {'source_doi': '10.5518/1207', 'license': 'CC BY 4.0',
              'license_url': 'https://creativecommons.org/licenses/by/4.0/',
              'status': 'Research candidate only; no clinical approval or runtime publication',
              'records': records, 'archive_members': members}
    (STAGE / 'acquisition.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(members, indent=2))


if __name__ == '__main__':
    main()
