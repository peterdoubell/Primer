#!/usr/bin/env python3
"""Independent direct-line check of one pinned Leeds native INP, not clinical QA.

This does not import the main parser, render, fit or modify geometry. Requires
NumPy in the offline scientific runtime; it adds no application dependency.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


EXPECTED = '55b3050e3b6e0ce594d418f865e4bedfeef5bb360f12769de002fadc4d68eb03'
SOURCE = Path('/tmp/primer-msk-sources/leeds-knee-981/fe-baseline/ltkn8941_seg_intact_fix.inp')


def check(source):
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED
    node_rows, element_rows, groups = [], [], {}
    mode, part = None, False
    for line in raw.decode('utf-8-sig').splitlines():
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            fields = [item.strip().upper() for item in line.split(',')]
            key, mode = fields[0], None
            if key == '*PART':
                assert not part
                part = True
            elif key == '*END PART':
                break
            elif part and key == '*NODE':
                mode = 'node'
            elif part and key == '*ELEMENT':
                assert 'TYPE=C3D10' in fields
                mode = 'element'
            elif part and key == '*ELSET' and fields[1].startswith('ELSET=PT_'):
                assert 'GENERATE' in fields
                mode = fields[1].split('=')[1]
                assert mode not in groups
                groups[mode] = []
            continue
        if mode == 'node':
            values = [item.strip() for item in line.split(',') if item.strip()]
            assert len(values) == 4
            node_rows.append([int(values[0]), *map(float, values[1:])])
        elif mode == 'element':
            values = [int(item) for item in line.split(',') if item.strip()]
            assert len(values) == 11
            element_rows.append(values)
        elif mode and mode.startswith('PT_'):
            first, last, step = [int(item) for item in line.split(',') if item.strip()]
            groups[mode].extend(range(first, last + 1, step))
    nodes, elements = np.asarray(node_rows, float), np.asarray(element_rows, np.int64)
    assert np.array_equal(nodes[:, 0], np.arange(1, len(nodes) + 1))
    assert np.array_equal(elements[:, 0], np.arange(1, len(elements) + 1))
    xyz, cells = nodes[:, 1:], elements[:, 1:] - 1
    assert cells.min() >= 0 and cells.max() < len(xyz)
    assigned = np.concatenate([np.asarray(ids, np.int64) for ids in groups.values()])
    assert len(groups) == 7 and np.array_equal(np.sort(assigned), elements[:, 0])
    pairs = np.array([[0, 1], [1, 2], [2, 0], [0, 3], [1, 3], [2, 3]])
    rows = []
    for name, ids in groups.items():
        selected = cells[np.asarray(ids) - 1]
        points = xyz[selected]
        deviation = np.linalg.norm(points[:, 4:] - points[:, pairs].mean(axis=2), axis=2)
        corners = points[:, :4]
        determinant = np.linalg.det(np.stack([corners[:, 1] - corners[:, 0],
            corners[:, 2] - corners[:, 0], corners[:, 3] - corners[:, 0]], axis=2))
        edge_lengths = np.linalg.norm(points[:, pairs[:, 0]] - points[:, pairs[:, 1]], axis=2)
        rows.append({'source_elset': name, 'tetrahedra': len(ids),
            'unique_nodes': len(np.unique(selected)),
            'nodal_bounds_native_units': [points.min(axis=(0, 1)).tolist(), points.max(axis=(0, 1)).tolist()],
            'median_corner_edge_native_units': float(np.median(edge_lengths)),
            'maximum_midside_offset_from_edge_midpoint_native_units': float(deviation.max()),
            'midside_offset_quantiles_native_units': np.quantile(deviation, [.5, .95, .99]).tolist(),
            'edges_above_1e_5_native_units': int((deviation > 1e-5).sum()),
            'negative_corner_determinants': int((determinant < 0).sum()),
            'zero_corner_determinants': int((determinant == 0).sum())})
    return {'source_sha256': hashlib.sha256(raw).hexdigest(),
        'method': 'Independent direct line parser; first PART only; sequential ID checks and exact seven-material partition; C3D10 official edge order; no render/parser-module import',
        'nodes': len(xyz), 'quadratic_tetrahedra': len(cells), 'groups': rows,
        'limitations': 'Corner determinants are not full quadratic-Jacobian validation. Offsets and counts describe the source FE representation, not anatomical accuracy or confirmed physical units. No MRI registration or clinical approval.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.source.resolve() or (
            args.output.exists() and args.output.samefile(args.source)):
        parser.error('The audit report cannot overwrite the native source')
    report = check(args.source)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'nodes': report['nodes'], 'tetrahedra': report['quadratic_tetrahedra'],
                      'materials': len(report['groups']), 'output': str(args.output)}))
