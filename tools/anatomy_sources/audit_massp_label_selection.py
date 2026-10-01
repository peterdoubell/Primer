#!/usr/bin/env python3
"""Compare complete native probability competition with publisher label volumes."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from tools.anatomy_sources.massp_probability_mesh import load_verified


def audit(root, output):
    acquisition = json.loads((root/'all-probability-acquisition.json').read_text())
    original = json.loads((root/'acquisition.json').read_text())
    table_path = root/'massp_2p0-label-list.txt'
    expected = next(e for e in original['files'] if e['name'] == table_path.name)
    if hashlib.sha256(table_path.read_bytes()).hexdigest() != expected['sha256']:
        raise ValueError('Publisher label table changed')
    entries = {e['name']: e for e in acquisition['files']}
    names = {}
    for line in table_path.read_text().splitlines():
        fields = [s.strip() for s in line.split(':')]
        if not fields[0].isdigit():
            continue
        label, code, side = int(fields[0]), fields[2], fields[3]
        name = f'proba_ahead-massp2_avg-{code}_hem-{side}_decade-18to80_n97.nii.gz'
        if label in names or name not in entries:
            raise ValueError('Label/probability inventory mismatch')
        names[label] = name
    if set(names) != set(range(1,64)) or len(entries) != 64:
        raise ValueError('Incomplete native label competition')
    source_image = load_verified(root, 'ahead-massp2_avg-maxlabel_decade-18to80.nii.gz', original)
    shape, affine = source_image.shape, source_image.affine
    highest = np.zeros(shape, dtype=np.float32)
    first = np.zeros(shape, dtype=np.uint8)
    last = np.zeros(shape, dtype=np.uint8)
    for label in sorted(names):
        image = load_verified(root, names[label], acquisition)
        if image.shape != shape or not np.array_equal(image.affine,affine):
            raise ValueError('Source probability grids differ')
        values = np.asarray(image.dataobj)
        if not np.isfinite(values).all() or values.min()<0 or values.max()>1:
            raise ValueError('Invalid source probabilities')
        wins = values > highest
        ties = (values == highest) & (values > 0)
        first[wins] = label
        last[wins | ties] = label
        highest[wins] = values[wins]
        print(label, flush=True)
    background_name='proba_ahead-massp2_avg-background_decade-18to80_n97.nii.gz'
    background_image=load_verified(root,background_name,acquisition)
    if background_image.shape != shape or not np.array_equal(background_image.affine,affine):
        raise ValueError('Background grid differs')
    background=np.asarray(background_image.dataobj)
    if not np.isfinite(background).all() or background.min()<0 or background.max()>1:
        raise ValueError('Invalid background')
    records=[]
    for selection in ('maxlabel','bestlabel'):
        image=load_verified(root,f'ahead-massp2_avg-{selection}_decade-18to80.nii.gz',original)
        if image.shape != shape or not np.array_equal(image.affine,affine):
            raise ValueError('Publisher selection grid differs')
        source=np.asarray(image.dataobj)
        comparisons=[]
        for include_background in (False,True):
            for tie_rule,foreground in (('lowest_label',first),('highest_label',last)):
                candidate=foreground.copy()
                if include_background:
                    # Label zero wins equal probabilities under the first rule.
                    candidate[background>=highest if tie_rule=='lowest_label' else background>highest]=0
                disagreements=source != candidate
                comparisons.append({'include_background':include_background,'tie_rule':tie_rule,
                                    'disagreeing_voxels':int(disagreements.sum()),
                                    'source_nonzero_voxels':int(np.count_nonzero(source)),
                                    'candidate_nonzero_voxels':int(np.count_nonzero(candidate)),
                                    'exact_voxel_match':bool(not disagreements.any())})
        records.append({'publisher_selection':selection,'comparisons':comparisons})
    result={'source_doi':acquisition['doi'],'all_probability_acquisition_sha256':hashlib.sha256((root/'all-probability-acquisition.json').read_bytes()).hexdigest(),
            'native_grid_shape':list(shape),'native_affine':affine.tolist(),'probability_maps_checked':64,
            'source_values_unchanged':True,'records':records,'clinical_approval':False,
            'limits':'Empirical comparison of arithmetic selections with source volumes. This is not author confirmation of map semantics or proof of anatomical/clinical accuracy.'}
    output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    audit(args.source,args.output)
