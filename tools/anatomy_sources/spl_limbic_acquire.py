"""Acquire only the pinned original SPL limbic MRI bodies and scene metadata."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / '.research/limbic-next-20261016'
SOURCE = RESEARCH / 'spl'
COMMIT = 'bec24db25aad5f7600e2df3becfb1f883e61ff56'
PATHS = (
    'slicer/volumes/imaging/A1_grayT1.nrrd',
    'slicer/volumes/imaging/A1_grayT2.nrrd',
    'slicer/brain-atlas.mrml',
    'slicer/colortables/hncma-atlas-lut.ctbl',
)


def acquire():
    index = json.loads((RESEARCH / 'external-metadata/spl-tree.json').read_text())
    records = {row['path']: row for row in index['tree'] if row['path'] in PATHS}
    if set(records) != set(PATHS) or sum(row['size'] for row in records.values()) > 150_000_000:
        raise ValueError('Pinned SPL selection differs or exceeds its bounded size')
    if shutil.disk_usage(SOURCE).free < 2_000_000_000:
        raise ValueError('At least2GB free space is required for this bounded source package')

    def fetch(path):
        row = records[path]
        target = SOURCE / path
        target.parent.mkdir(parents=True, exist_ok=True)
        url = 'https://raw.githubusercontent.com/mhalle/spl-brain-atlas/' + COMMIT + '/' + path
        packed = hashlib.sha256()
        blob = hashlib.sha1(('blob ' + str(row['size']) + '\0').encode())
        count = 0
        if target.exists():
            stream = target.open('rb')
            output = None
        else:
            request = urllib.request.Request(url, headers={'User-Agent': 'Primer-SPL-source-verification/1.0'})
            stream = urllib.request.urlopen(request, timeout=90)
            output = target.with_name(target.name + '.part').open('wb')
        try:
            with stream:
                while chunk := stream.read(1024 * 1024):
                    count += len(chunk)
                    if count > row['size']:
                        raise ValueError('Original SPL object exceeded its pinned byte length')
                    packed.update(chunk)
                    blob.update(chunk)
                    if output is not None:
                        output.write(chunk)
                    if count % (16 * 1024 * 1024) == 0:
                        print(path, count, '/', row['size'], flush=True)
        finally:
            if output is not None:
                output.close()
        if count != row['size'] or blob.hexdigest() != row['sha']:
            raise ValueError('Original SPL Git blob identity differs: ' + path)
        if output is not None:
            target.with_name(target.name + '.part').replace(target)
        print('Verified', path, count, flush=True)
        return {'path': path, 'url': url, 'bytes': count, 'git_blob_sha1': blob.hexdigest(),
                'sha256': packed.hexdigest(), 'source_commit': COMMIT, 'original_bytes_unchanged': True}

    with ThreadPoolExecutor(max_workers=2) as pool:
        files = list(pool.map(fetch, PATHS))
    result = {'source_repository': 'mhalle/spl-brain-atlas', 'source_commit': COMMIT,
              'files': files, 'total_original_bytes': sum(row['bytes'] for row in files),
              'no_unrelated_downloads': True, 'clinical_approval': False}
    (RESEARCH / 'original-volume-acquisition.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    result = acquire()
    print(json.dumps({'verified_files': len(result['files']), 'bytes': result['total_original_bytes']}))
