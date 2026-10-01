#!/usr/bin/env python3
"""Acquire all pinned MASSP average probabilities, preserving earlier records."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

from tools.anatomy_sources.acquire_massp_lifespan import METADATA_URL, EXPECTED_DOI, verified


def acquire(root):
    root.mkdir(parents=True, exist_ok=True)
    raw = urlopen(METADATA_URL, timeout=60).read()
    metadata = json.loads(raw)
    if metadata['doi'] != EXPECTED_DOI or metadata['license']['url'] != 'https://creativecommons.org/licenses/by/4.0/':
        raise ValueError('Pinned dataset or licence changed')
    entries = [e for e in metadata['files'] if re.fullmatch(
        r'proba_ahead-massp2_avg-(?:[a-z0-9]+_hem-(?:l|r|lr|3|4)|background)_decade-18to80_n97\.nii\.gz', e['name'])]
    if len(entries) != 64 or len({e['name'] for e in entries}) != 64:
        raise ValueError('Full probability collection is incomplete or duplicated')

    def download(entry):
        path = root / entry['name']
        if not verified(path, entry):
            tmp = path.with_name(path.name + '.part')
            with urlopen(entry['download_url'], timeout=60) as response, tmp.open('wb') as out:
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    out.write(block)
            if not verified(tmp, entry):
                raise ValueError('Publisher probability checksum mismatch: ' + entry['name'])
            tmp.replace(path)
        return {**entry, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'integrity_passed': True}

    files = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for record in pool.map(download, entries):
            files.append(record)
            print(len(files), record['name'], flush=True)
    result = {'source_metadata_url': METADATA_URL, 'source_metadata_sha256': hashlib.sha256(raw).hexdigest(),
              'doi': EXPECTED_DOI, 'license': metadata['license'], 'authors': metadata['authors'],
              'files': files, 'coordinate_or_probability_changes': False, 'clinical_approval': False}
    (root / 'all-probability-acquisition.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    acquire(parser.parse_args().destination)
