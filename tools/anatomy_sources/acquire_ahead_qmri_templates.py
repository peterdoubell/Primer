#!/usr/bin/env python3
"""Acquire pinned quantitative MRI templates, retaining median and variability."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen
from tools.anatomy_sources.acquire_massp_lifespan import verified

METADATA_URL = 'https://api.figshare.com/v2/articles/19646364/versions/3'
EXPECTED_DOI = '10.21942/uva.19646364.v3'


def acquire(root):
    root.mkdir(parents=True, exist_ok=True)
    raw = urlopen(METADATA_URL, timeout=60).read()
    metadata = json.loads(raw)
    if metadata['doi'] != EXPECTED_DOI or metadata['license']['url'] != 'https://creativecommons.org/licenses/by/4.0/':
        raise ValueError('Pinned MRI source or licence changed')
    entries = [entry for entry in metadata['files'] if re.fullmatch(
        r'ahead_qmri2_mni09b_(med|iqr)_(r1map|r2map|qsmap)_n105\.nii\.gz', entry['name'])]
    if len(entries) != 6 or len({entry['name'] for entry in entries}) != 6:
        raise ValueError('Incomplete MRI contrast/variability selection')
    (root/'metadata-v3.json').write_bytes(raw)

    def download(entry):
        path = root/entry['name']
        if not verified(path, entry):
            temporary = path.with_name(path.name+'.part')
            with urlopen(entry['download_url'], timeout=60) as response, temporary.open('wb') as out:
                while True:
                    block = response.read(1024*1024)
                    if not block:
                        break
                    out.write(block)
            if not verified(temporary, entry):
                raise ValueError('Publisher MRI size/checksum mismatch: '+entry['name'])
            temporary.replace(path)
        record = {**entry, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'integrity_passed': True}
        print(entry['name'], 'verified', flush=True)
        return record

    with ThreadPoolExecutor(max_workers=3) as pool:
        files = list(pool.map(download, entries))
    result = {'source_metadata_url': METADATA_URL, 'source_metadata_sha256': hashlib.sha256(raw).hexdigest(),
              'doi': EXPECTED_DOI, 'license': metadata['license'], 'authors': metadata['authors'],
              'description': metadata['description'], 'files': files,
              'source_coordinate_or_intensity_changes': False, 'clinical_approval': False}
    (root/'acquisition.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path,required=True)
    acquire(parser.parse_args().destination)
