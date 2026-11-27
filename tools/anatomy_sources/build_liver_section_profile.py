"""Count the publisher's nine regions on each original axial CT section for systematic sampling."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CASE = Path('web/anatomy/medseg-liver-001')
OUTPUT = Path('web/radiology/liver-segment-assembly/axial-profile.json')


def _require_owned_root(root):
    # Validate spellings only. Never resolve, inspect or access the supplied path.
    trusted = {
        os.fspath(ROOT),
        os.fspath(Path(__file__).absolute().parents[2]),
        os.path.relpath(ROOT, Path.cwd()),
    }
    try:
        requested = os.fspath(root)
    except TypeError as error:
        raise ValueError('Root must identify the checkout containing this script') from error
    if requested not in trusted:
        raise ValueError('Root must identify the checkout containing this script')


def build(root=ROOT):
    _require_owned_root(root)
    manifest = json.loads((ROOT/CASE/'manifest.json').read_bytes())
    source = nib.load(ROOT/CASE/'original-labels.nii.gz')
    values = np.asanyarray(source.dataobj)
    original = hashlib.sha256(values.astype('<f4').tobytes(order='F')).hexdigest()
    if original != manifest['originalLabelSampleSHA256'] or list(source.shape) != manifest['shape']:
        raise ValueError('Original region array differs from the selected CT case')
    counts = []
    for plane in range(source.shape[2]):
        samples = values[:,:,plane]
        labels = samples.astype(np.uint8)
        if not np.array_equal(samples, labels) or np.max(labels)>9:
            raise ValueError('Invalid published region value')
        counts.append(np.bincount(labels.ravel(),minlength=10)[1:].tolist())
    totals = np.sum(counts,axis=0).tolist()
    if totals != [row['voxelCount'] for row in manifest['labels']]:
        raise ValueError('Individual CT section counts do not restore the complete label volumes')
    return {'case':manifest['id'], 'sourceLabelSampleSHA256':original, 'shape':manifest['shape'],
            'spacingMm':manifest['spacingMm'], 'codes':[row['code'] for row in manifest['labels']],
            'countsByAxialSection':counts}


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--root',type=Path,default=ROOT,
                      help='Trusted absolute or cwd-relative spelling of this script checkout')
    args.add_argument('--write',action='store_true')
    opts=args.parse_args()
    data=build(opts.root)
    payload=json.dumps(data,separators=(',',':'))+'\n'
    path=ROOT/OUTPUT
    if opts.write: path.write_text(payload)
    elif path.read_text()!=payload: raise SystemExit('The distributed axial profile differs from the original masks')
    print(f"{len(data['countsByAxialSection'])} original sections, {len(data['codes'])} regions")
