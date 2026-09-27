#!/usr/bin/env python3
"""Retrieve the MRML-declared segmentation reference via the public ZIP API.

No source rewrite, full archive claim, fitted registration or runtime publication.
"""
import hashlib
import io
import json
from pathlib import Path
import struct
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
import zlib
from acquire_malaya_knee import ranged, API

ROOT = Path('/tmp/primer-msk-sources/high-fidelity')
OUT = ROOT / 'um-knee-image-audit'


def references(element):
    return dict(piece.split(':', 1) for piece in element.get('references', '').split(';') if ':' in piece)


def main():
    OUT.mkdir(exist_ok=True)
    scene = ET.parse(ROOT / 'um-registration/Final model.mrml').getroot()
    nodes = {node.get('id'): node for node in scene if node.get('id')}
    segmentation = next(node for node in scene if node.tag == 'Segmentation')
    reference = nodes[references(segmentation)['referenceImageGeometryRef']]
    storage = nodes[references(reference)['storage']]
    filename = urllib.parse.unquote(storage.get('fileName'))
    metadata_url = 'https://researchdata.um.edu.my/api/datasets/:persistentId/?persistentId=doi:10.22452/RD/5T6TZ7'
    metadata = json.load(urllib.request.urlopen(metadata_url, timeout=30))
    version = metadata['data']['latestVersion']
    assert version['license']['name'] == 'CC0 1.0'
    file_record = next(item for item in version['files'] if item['dataFile']['id'] == 595)
    assert file_record['restricted'] is False
    archive = file_record['dataFile']; base = archive['filesize'] - 65536
    tail = ranged(API + '595', base, archive['filesize'] - 1)
    with zipfile.ZipFile(io.BytesIO(tail)) as source:
        entry = next(item for item in source.infolist() if item.filename.rsplit('/', 1)[-1] == filename)
    assert entry.file_size < 100_000_000 and entry.compress_size < 100_000_000
    destination = OUT / filename
    if not destination.exists():
        offset = entry.header_offset + base
        header = ranged(API + '595', offset, offset + 29)
        assert header[:4] == b'PK\x03\x04'
        name_bytes, extra = struct.unpack_from('<HH', header, 26)
        start = offset + 30 + name_bytes + extra
        payload = ranged(API + '595', start, start + entry.compress_size - 1)
        body = zlib.decompress(payload, -15) if entry.compress_type == 8 else payload
        assert len(body) == entry.file_size and zlib.crc32(body) == entry.CRC
        destination.write_bytes(body)
    body = destination.read_bytes()
    assert len(body) == entry.file_size and zlib.crc32(body) == entry.CRC
    result = {'status': 'Offline source audit only; no clinical approval',
              'reference_volume_id': reference.get('id'), 'reference_volume_name': reference.get('name'),
              'storage_id': storage.get('id'), 'reference_image_file': str(destination),
              'source_archive_url': API + '595', 'source_member': entry.filename,
              'source_archive_published_md5': archive['md5'], 'source_archive_full_md5_verified': False,
              'zip_crc32': f'{entry.CRC:08x}', 'bytes': len(body), 'compressed_bytes': entry.compress_size,
              'sha256': hashlib.sha256(body).hexdigest(), 'license': 'CC0 1.0',
              'mrml_sha256': hashlib.sha256((ROOT / 'um-registration/Final model.mrml').read_bytes()).hexdigest()}
    (OUT / 'reference-volume-acquisition.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
