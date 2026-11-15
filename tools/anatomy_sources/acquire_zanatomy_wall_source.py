#!/usr/bin/env python3
"""Acquire pinned native wall-source FBX and official transform-reader inputs."""
import argparse
import json
from pathlib import Path
import subprocess
from tools.anatomy_sources.acquire_z_anatomy import COMMIT, FILES, UFBX_COMMIT, fetch


def acquire(root):
    root.mkdir(parents=True, exist_ok=True)
    records = []
    for name in ['MuscularSystem100.fbx', 'License.txt', 'LICENSE']:
        relative, size, digest = FILES[name]
        records.append(fetch('https://raw.githubusercontent.com/LluisV/Z-Anatomy/' + COMMIT + '/' + relative,
                             root / name, size, digest))
    (root / 'acquisition.json').write_text(json.dumps({'source_commit': COMMIT, 'files': records,
        'runtime_promoted': False, 'clinical_approval': False}, indent=2) + '\n')
    libraries = []
    for name in ['ufbx.h', 'ufbx.c', 'LICENSE']:
        libraries.append(fetch('https://raw.githubusercontent.com/ufbx/ufbx/' + UFBX_COMMIT + '/' + name,
                               root / ('ufbx-LICENSE' if name == 'LICENSE' else name)))
    (root / 'ufbx-acquisition.json').write_text(json.dumps({'source_commit': UFBX_COMMIT, 'files': libraries}, indent=2) + '\n')
    exporter = Path(__file__).with_name('export_ufbx.c')
    subprocess.run(['clang', '-O2', '-I' + str(root), str(exporter), str(root / 'ufbx.c'), '-lm', '-o', str(root / 'export_ufbx')], check=True)
    with (root / 'world-inventory.json').open('w') as stream:
        subprocess.run([str(root / 'export_ufbx'), str(root / 'MuscularSystem100.fbx')], stdout=stream, check=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True)
    acquire(p.parse_args().source_root)
