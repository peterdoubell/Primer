#!/usr/bin/env python3
"""Locate all adjacency-sensitive LNQ label cubes and preserve native CT patches."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def localize(root, review_path, geometry_path, output):
    import numpy as np
    from scipy import ndimage
    from skimage.measure import euler_number
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from tools.anatomy_sources.localize_aeropath_adjacency import CORNERS, cube_components
    from tools.anatomy_sources.review_tcia_lung_case import read_series
    review = json.loads(review_path.read_text()); geometry = json.loads(geometry_path.read_text())
    path = root / 'lnq-case-0571-derived/source-annotation-on-ct-indices.npy'
    if hashlib.sha256(path.read_bytes()).hexdigest() != review['reconstructed_mask_sha256']:
        raise ValueError('Source selection changed')
    full = np.load(path)
    labels, count = ndimage.label(full, ndimage.generate_binary_structure(3, 3))
    largest = max(review['components'], key=lambda c: c['voxel_count'])['annotation_component']
    mask = labels == largest; coords = np.argwhere(mask)
    low, high = coords.min(0) - 1, coords.max(0) + 2
    crop = mask[tuple(slice(a, b) for a, b in zip(low, high))]
    shape = np.asarray(crop.shape) - 1; codes = np.zeros(shape, dtype=np.uint8)
    for index, corner in enumerate(CORNERS):
        codes |= crop[tuple(slice(c, c + n) for c, n in zip(corner, shape))].astype(np.uint8) << index
    foreground, background = cube_components()
    sensitive = (foreground[codes] > 1) | (background[codes] > 1)
    origins = np.argwhere(sensitive) + low; values = codes[sensitive]
    output.mkdir(parents=True, exist_ok=True)
    path = output / 'component-02-adjacency-locations.npz'
    np.savez_compressed(path, native_origins_zyx=origins, configuration_codes=values)
    planes, counts = np.unique(origins[:, 0], return_counts=True)
    selected = [int(np.flatnonzero(origins[:, 0] == z)[0]) for z in planes[np.argsort(-counts)[:3]]]
    ct_path = root / 'case_0571-ct.zip'
    if hashlib.sha256(ct_path.read_bytes()).hexdigest() != review['ct_archive_sha256']:
        raise ValueError('Source CT changed')
    images = read_series(ct_path); images.sort(key=lambda d: float(d.ImagePositionPatient[2]))
    ct = np.stack([d.pixel_array.astype(float) * float(d.RescaleSlope) + float(d.RescaleIntercept) for d in images])
    delta = np.asarray(review['frame_records'][0]['seg_position_lps']) - np.asarray(review['frame_records'][0]['ct_position_lps'])
    sy, sx = review['ct_spacing_zyx_mm'][1:]
    sites = []
    for number, index in enumerate(selected, 1):
        origin = origins[index]; z, y, x = map(int, origin)
        y0, y1 = max(y - 8, 0), min(y + 10, ct.shape[1]); x0, x1 = max(x - 8, 0), min(x + 10, ct.shape[2])
        fig, axes = plt.subplots(2, 2, figsize=(8, 8))
        for row, plane in enumerate((z, z + 1)):
            pixels = ct[plane, y0:y1, x0:x1]; annotation = mask[plane, y0:y1, x0:x1]
            for column, marked in enumerate((False, True)):
                ax = axes[row, column]
                ax.imshow(pixels, cmap='gray', vmin=-160, vmax=240, origin='upper', interpolation='nearest', aspect=sy / sx)
                if marked:
                    if annotation.any() and not annotation.all():
                        ax.contour(np.arange(annotation.shape[1]) + delta[0] / sx,
                                   np.arange(annotation.shape[0]) + delta[1] / sy,
                                   annotation, levels=[0.5], colors=['#ecb453'], linewidths=0.8)
                    ax.plot(x - x0 + 0.5 + delta[0] / sx, y - y0 + 0.5 + delta[1] / sy, 'r+', markersize=8)
                ax.set_title(f'Native CT z={plane}; ' + ('component contour/cube XY centre' if marked else 'unmarked CT'), fontsize=9)
                ax.set_xticks([]); ax.set_yticks([])
        fig.suptitle(f'LNQ component {largest} | cube ZYX {origin.tolist()} | code {int(values[index])}\n'
                     'Both source cube planes; no cause/repair or station identity inferred', fontsize=10)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        name = f'component-02-site-{number:02d}.png'; fig.savefig(output / name, dpi=150); plt.close(fig)
        slices = (slice(z, z + 2), slice(y, y + 2), slice(x, x + 2))
        sites.append({'native_cube_origin_zyx': origin.tolist(), 'configuration_code': int(values[index]),
            'native_component_cube_zyx': mask[slices].astype(int).tolist(), 'native_rescaled_ct_cube_zyx': ct[slices].tolist(),
            'displayed_ct_planes': [z, z + 1], 'patch_start_yx': [y0, x0], 'patch_stop_exclusive_yx': [y1, x1],
            'marker_basis': 'Native cube XY centre in each displayed source plane, with original SEG offset; not a fitted point.',
            'file': name, 'sha256': hashlib.sha256((output / name).read_bytes()).hexdigest()})
    unique, frequencies = np.unique(values, return_counts=True)
    result = {'case_id': 'case_0571', 'source_doi': review['source_doi'], 'component': int(largest),
        'source_mask_sha256': review['reconstructed_mask_sha256'], 'source_geometry_audit_sha256': hashlib.sha256(geometry_path.read_bytes()).hexdigest(),
        'native_component_voxels': int(mask.sum()), 'native_euler_6_connectivity': int(euler_number(crop, connectivity=1)),
        'native_euler_26_connectivity': int(euler_number(crop, connectivity=3)),
        'native_cubes_checked': int(codes.size), 'adjacency_sensitive_cube_count': len(origins),
        'adjacency_locations_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'configurations': [{'code': int(c), 'cubes': int(n), 'foreground_6_components': int(foreground[c]),
                            'background_6_components': int(background[c])} for c, n in zip(unique, frequencies)],
        'native_z_plane_counts': [{'ct_index': int(z), 'cubes': int(n)} for z, n in zip(planes, counts)],
        'selected_sites': sites, 'site_selection': 'First indexed candidate in each of the three most populated native Z planes.',
        'source_values_changed': False, 'clinical_approval': False, 'runtime_promoted': False,
        'status': 'held_unclassified_source_component_topology',
        'limits': ['Adjacency-sensitive cube count is not a surface-handle count or a diagnosis.',
                   'Native voxel Euler characteristics depend on declared adjacency and are not equated silently to the extracted surface.',
                   'Selected patches do not prove clinical cause, complete 3D topology or all boundary accuracy.',
                   'No holes filled, components removed or assumed individual-node splits introduced.']}
    (output / 'component-02-native-topology-review.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Adjacency-sensitive cubes', len(origins), '; native Euler 6/26', result['native_euler_6_connectivity'], result['native_euler_26_connectivity'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--review', type=Path, required=True)
    p.add_argument('--geometry-audit', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); localize(a.source_root, a.review, a.geometry_audit, a.output)
