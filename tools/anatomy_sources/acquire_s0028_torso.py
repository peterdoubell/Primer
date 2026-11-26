"""Retrieve the original s0028 label members from their pinned public ZIP byte range."""
import hashlib
import json
import struct
import urllib.request
import zlib

from package_s0028_torso import GROUPS, LABEL_DIR, RECEIPT

RECORD = 'https://zenodo.org/api/records/22688904'
CONTENT = RECORD + '/files/Totalsegmentator_dataset_v300.zip/content'


def confirm_archive(receipt):
    with urllib.request.urlopen(RECORD, timeout=60) as response:
        record = json.load(response)
    entry, = record['files']
    if (record['metadata']['license']['id'] != 'cc-by-4.0' or entry['size'] != receipt['archiveBytes']
            or entry['checksum'] != receipt['archiveChecksum'] or entry['links']['self'] != CONTENT):
        raise ValueError('Publisher identity or licence changed')


def main():
    receipt = json.loads(RECEIPT.read_bytes())
    confirm_archive(receipt)
    start, end = receipt['sourceRange']
    request = urllib.request.Request(CONTENT+f'?source_range={start}-{end}',
                                     headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
    with urllib.request.urlopen(request, timeout=90) as response:
        if response.status != 206 or response.headers.get('Content-Range') != f"bytes {start}-{end}/{receipt['archiveBytes']}":
            raise ValueError('Expected an exact publisher archive range')
        span = response.read(end-start+2)
    if len(span) != end-start+1 or hashlib.sha256(span).hexdigest() != receipt['rangeSHA256']:
        raise ValueError('Archive range differs from the reviewed source')
    records = {r['file']:r for r in receipt['labels']}
    LABEL_DIR.mkdir(parents=True,exist_ok=True)
    for names in GROUPS.values():
        for name in names:
            member = name + '.nii.gz'
            meta = records[member]
            at = meta['headerOffset'] - start
            header = struct.unpack_from('<4s5H3I2H', span, at)
            name_len, extra_len = header[-2:]
            offset = at+30
            path = span[offset:offset+name_len].decode()
            if header[0] != b'PK\x03\x04' or header[3] != 8 or path != 'Totalsegmentator_dataset_v300/s0028/segmentations/'+member:
                raise ValueError('Unexpected ZIP entry')
            offset += name_len + extra_len
            raw = zlib.decompress(span[offset:offset+meta['storedBytes']],wbits=-15)
            if len(raw) != meta['bytes'] or zlib.crc32(raw) != int(meta['crc32'],16) or hashlib.sha256(raw).hexdigest() != meta['sha256']:
                raise ValueError('Source member failed verification')
            (LABEL_DIR/member).write_bytes(raw)
    confirm_archive(receipt)
    print('Verified all',len(records),'source label members.')


if __name__ == '__main__':
    main()
