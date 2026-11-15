#!/usr/bin/env python3
"""Verify every delivered study file and complete lossless scalar payload."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from primer.source_study import validate_study_references


def inventory():
    registry = json.loads((ROOT / 'data/radiology/source-study-references.json').read_text())
    known = {i['id'] for i in json.loads((ROOT / 'data/radiology/reference-investigations.json').read_text())['investigations']}
    validate_study_references(registry, known, ROOT / 'web')
    files = {}
    for entries in registry.values():
        for row in entries:
            folder = ROOT / 'web/studies' / row['id']
            html = (folder / 'mri-reference.html').read_text()
            data = json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>', html, re.S).group(1))
            assert data['source_frames'] == row['source_frames']
            assert data['source_pixel_samples'] == row['source_pixel_samples']
            assert len(data['series']) == row['source_series']
            sops = set()
            for source, transport in zip(data['series'], row['series_transport']):
                for key in ('file', 'decoded_bytes', 'decoded_int16_le_sha256', 'compressed_sha256'):
                    assert source[key] == transport[key]
                assert len(source['frames']) == transport['frames']
                raw = gzip.decompress((folder / source['file']).read_bytes())
                assert len(raw) == source['decoded_bytes']
                assert hashlib.sha256(raw).hexdigest() == source['decoded_int16_le_sha256']
                offset = 0
                for frame in source['frames']:
                    assert frame['offset'] == offset and frame['sop'] not in sops
                    sops.add(frame['sop'])
                    count = frame['rows'] * frame['columns'] * 2
                    assert hashlib.sha256(raw[offset:offset + count]).hexdigest() == frame['source_pixel_int16_le_sha256']
                    offset += count
                assert offset == len(raw)
            assert len(sops) == row['source_frames']
            for name, identity in row['files'].items():
                files['/app/studies/' + row['id'] + '/' + name] = identity
    return {'schema_version': 1, 'scope': 'Complete independent source-study transport identities; release integrity does not establish anatomical or clinical approval.', 'files': dict(sorted(files.items()))}


if __name__ == '__main__':
    result = inventory()
    path = ROOT / 'data/radiology/radiology-static-source-studies.json'
    if json.loads(path.read_text()) != result:
        raise SystemExit('Static source study inventory differs')
    print(len(result['files']), 'source-study files and all native scalar spans verified')
