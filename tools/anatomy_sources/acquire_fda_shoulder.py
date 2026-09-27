#!/usr/bin/env python3
"""Acquire pinned public FDA shoulder data for research inspection, not publication."""
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

STAGE = Path('/tmp/primer-msk-sources/shoulder-next/fda-shoulder')
REPOSITORY = 'OSEL-DAM/ShoulderFiniteElementModel'
COMMIT = 'fc9f3e56b104c06759750495be1f8dd5d53c1741'
FILES = {'LICENSE': '0e259d42c996742e9e3cba14c677129b2c1b6311',
         'README.md': '6accf22968d19218be7500ec4430493882aa7e22',
         'Human Shoulder Finite Element Model ReadMe.docx': 'c6d3f7c75e29561a6ffd066465188621c5b5cd48',
         'Male-Shoulder.inp': '2341fbdf78044053e73877dcfb8d1928858be907'}


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    records = []
    for name, expected in FILES.items():
        url = 'https://raw.githubusercontent.com/' + REPOSITORY + '/' + COMMIT + '/' + urllib.parse.quote(name)
        target = STAGE / name
        if not target.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                if int(response.headers.get('Content-Length', '0')) > 100_000_000:
                    raise ValueError('Unexpected source size')
                body = response.read(100_000_001)
                if len(body) > 100_000_000:
                    raise ValueError('Unexpected source size')
                target.write_bytes(body)
        body = target.read_bytes()
        blob_sha1 = hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()
        assert blob_sha1 == expected, 'Pinned upstream Git blob changed: ' + name
        records.append({'name': name, 'url': url, 'bytes': len(body),
                        'sha256': hashlib.sha256(body).hexdigest(), 'git_blob_sha1': blob_sha1})
        print(json.dumps(records[-1]), flush=True)
    with zipfile.ZipFile(STAGE / 'Human Shoulder Finite Element Model ReadMe.docx') as archive:
        tree = ET.fromstring(archive.read('word/document.xml'))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    # Only Word text elements, excluding any other XML field metadata.
    paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t', ns))
                  for p in tree.findall('.//w:p', ns)]
    (STAGE / 'source-readme.txt').write_text('\n'.join(paragraphs) + '\n')
    result = {'repository': REPOSITORY, 'commit': COMMIT, 'license': 'CC0-1.0',
              'source_url': 'https://cdrh-rst.fda.gov/human-shoulder-finite-element-model',
              'status': 'Unpromoted research candidate; no clinical approval', 'files': records}
    (STAGE / 'acquisition.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
