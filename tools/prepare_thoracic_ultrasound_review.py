"""Materialize hash-verified review cine from the retained acquisition folder."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    review = root / 'docs/thoracic-ultrasound-source-review-20261013'
    manifest = json.loads((review / 'manifest.json').read_text())
    pending = []
    for asset in manifest['assets']:
        target = review / asset['path']
        if asset['kind'] == 'video':
            source = args.source / 'browser-clips' / target.name
            original = args.source / asset['original_path']
            if digest(original) != asset['original_sha256']:
                raise ValueError(f'Original checksum mismatch: {original.name}')
        else:
            source = target
        if source.stat().st_size != asset['bytes'] or digest(source) != asset['sha256']:
            raise ValueError(f'Checksum mismatch: {source.name}')
        if source != target:
            pending.append((source, target))
    for source, target in pending:
        shutil.copyfile(source, target)
    print(f"Verified {len(manifest['assets'])} assets; prepared {len(pending)} cine clips.")


if __name__ == '__main__':
    main()
