"""Count the publisher's nine regions on each original axial CT section for systematic sampling."""
import argparse
import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CASE = Path('web/anatomy/medseg-liver-001')
OUTPUT = Path('web/radiology/liver-segment-assembly/axial-profile.json')


def build(root=ROOT):
    manifest = json.loads((root/CASE/'manifest.json').read_bytes())
    source = nib.load(root/CASE/'original-labels.nii.gz')
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
    args.add_argument('--root',type=Path,default=ROOT)
    args.add_argument('--write',action='store_true')
    opts=args.parse_args()
    data=build(opts.root)
    payload=json.dumps(data,separators=(',',':'))+'\n'
    path=opts.root/OUTPUT
    if opts.write: path.write_text(payload)
    elif path.read_text()!=payload: raise SystemExit('The distributed axial profile differs from the original masks')
    print(f"{len(data['countsByAxialSection'])} original sections, {len(data['codes'])} regions")
