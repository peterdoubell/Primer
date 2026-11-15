#!/usr/bin/env python3
"""Acquire pinned MASSP 2.0 source candidates; never modifies runtime anatomy."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

METADATA_URL = 'https://api.figshare.com/v2/articles/27291579/versions/2'
EXPECTED_DOI = '10.21942/uva.27291579.v2'


def selected(name):
    return (bool(re.fullmatch(r'proba_ahead-massp2_avg-(cau|put|gpe|gpi|ic|tha)_hem-[lr]_decade-18to80_n97\.nii\.gz', name))
            or name in {'massp_2p0-label-list.txt', 'ahead-massp2_avg-bestlabel_decade-18to80.nii.gz',
                        'ahead-massp2_avg-maxlabel_decade-18to80.nii.gz', 'ahead-massp2_avg-maxproba_decade-18to80.nii.gz'})


def verified(path, entry):
    if not path.is_file() or path.stat().st_size != entry['size']:
        return False
    return hashlib.md5(path.read_bytes()).hexdigest() == entry['computed_md5']


def acquire(destination):
    destination.mkdir(parents=True, exist_ok=True)
    raw = urlopen(METADATA_URL, timeout=60).read()
    metadata = json.loads(raw)
    if metadata['doi'] != EXPECTED_DOI or metadata['version'] != 2:
        raise ValueError('Unexpected source version')
    if metadata['license']['name'] != 'CC BY 4.0':
        raise ValueError('Source licence changed; review required')
    entries = [entry for entry in metadata['files'] if selected(entry['name'])]
    if len(entries) != 16 or len({e['name'] for e in entries}) != 16:
        raise ValueError('Source selection incomplete or duplicated')
    (destination / 'metadata-v2.json').write_bytes(raw)
    records = []
    for entry in entries:
        path = destination / entry['name']
        if not verified(path, entry):
            tmp = path.with_name(path.name + '.part')
            with urlopen(entry['download_url'], timeout=60) as response, tmp.open('wb') as out:
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    out.write(block)
            if not verified(tmp, entry):
                raise ValueError('Source size or publisher checksum mismatch: ' + entry['name'])
            tmp.replace(path)
        records.append({**entry, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'integrity_passed': True})
        print(entry['name'], flush=True)
    record = {'source_metadata_url': METADATA_URL, 'source_metadata_sha256': hashlib.sha256(raw).hexdigest(),
              'doi': EXPECTED_DOI, 'license': metadata['license'], 'authors': metadata['authors'],
              'description': metadata['description'], 'files': records,
              'coordinate_or_value_changes': False, 'runtime_binding_added': False,
              'clinical_approval': False}
    (destination / 'acquisition.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    acquire(parser.parse_args().destination)
