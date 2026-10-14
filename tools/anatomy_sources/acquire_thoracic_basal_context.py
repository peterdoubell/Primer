"""Acquire complete same-case liver/spleen labels without changing source arrays."""
import hashlib
import json
import shutil
import urllib.request
import zipfile
import zlib
from pathlib import Path

from tools.anatomy_sources.acquire_hipas_case import RemoteArchive


def acquire(source, output):
    url = 'https://zenodo.org/api/records/22688904'
    metadata = json.loads(urllib.request.urlopen(url, timeout=45).read())
    entry, = metadata['files']
    if metadata['metadata']['license']['id'] != 'cc-by-4.0':
        raise ValueError('Source license changed')
    output.mkdir(parents=True, exist_ok=True)
    acquisition = json.loads((source / 'CT-acquisition.json').read_text())
    screen = json.loads((source / 'mask-screen.json').read_text())
    if acquisition['case'] != 's0028' or screen['case'] != 's0028':
        raise ValueError('Source case differs')
    for name in ['ct.nii.gz', 'CT-acquisition.json', 'lung-mask-review.json',
                 'lung-source-correspondence.png']:
        shutil.copyfile(source / name, output / name)
    for row in screen['labels']:
        path = source / (row['label'] + '.nii.gz')
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Existing source lobe changed')
        shutil.copyfile(path, output / path.name)
    remote = RemoteArchive(entry['links']['self'], entry['size'])
    rows = []
    with zipfile.ZipFile(remote) as archive:
        for label in ['liver', 'spleen']:
            member = 'Totalsegmentator_dataset_v300/s0028/segmentations/' + label + '.nii.gz'
            info = archive.getinfo(member)
            raw = archive.read(member)
            if len(raw) != info.file_size or zlib.crc32(raw) != info.CRC:
                raise ValueError('Original archive member differs')
            (output / (label + '.nii.gz')).write_bytes(raw)
            row = {'label': label, 'member': member, 'bytes': len(raw),
                   'sha256': hashlib.sha256(raw).hexdigest(), 'CRC32': f'{info.CRC:08x}'}
            rows.append(row)
            print('Acquired complete original', label, len(raw), flush=True)
    fresh = json.loads(urllib.request.urlopen(url, timeout=45).read())['files'][0]
    if (fresh['checksum'], fresh['size']) != (entry['checksum'], entry['size']):
        raise ValueError('Publisher archive changed during acquisition')
    screen['labels'].extend(rows)
    (output / 'mask-screen.json').write_text(json.dumps(screen, indent=2) + '\n')
    proof = {'source_record': 22688904, 'case': 's0028', 'license': 'CC BY 4.0',
             'archive_checksum': entry['checksum'], 'archive_bytes': entry['size'],
             'publisher_archive_identity_unchanged_before_after': True,
             'full_archive_checksum_verified': False, 'member_CRCs_verified': True,
             'members': rows, 'ranges': remote.ranges, 'clinical_approval': False}
    (output / 'basal-context-acquisition.json').write_text(json.dumps(proof, indent=2) + '\n')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    acquire(args.source_root, args.output)
