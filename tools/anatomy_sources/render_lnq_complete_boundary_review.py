#!/usr/bin/env python3
"""Render all native LNQ source-label planes and components without diagnostic relabelling."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.review_tcia_lung_case import read_series


def render(root, source_review, output):
    import numpy as np
    from scipy import ndimage
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    report = json.loads(source_review.read_text())
    path = root / 'case_0571-ct.zip'
    if hashlib.sha256(path.read_bytes()).hexdigest() != report['ct_archive_sha256']:
        raise ValueError('Original CT archive changed')
    path = root / 'lnq-case-0571-derived/source-annotation-on-ct-indices.npy'
    if hashlib.sha256(path.read_bytes()).hexdigest() != report['reconstructed_mask_sha256']:
        raise ValueError('Source annotation placement changed')
    mask = np.load(path)
    images = read_series(root / 'case_0571-ct.zip')
    images.sort(key=lambda d: float(d.ImagePositionPatient[2]))
    volume = np.stack([d.pixel_array.astype(float) * float(d.RescaleSlope) + float(d.RescaleIntercept) for d in images])
    if list(mask.shape) != report['ct_shape_zyx'] or int(mask.sum()) != report['encoded_annotation_voxels']:
        raise ValueError('Annotation extent changed')
    labels, count = ndimage.label(mask, ndimage.generate_binary_structure(3, 3))
    if count != report['connected_components_26']:
        raise ValueError('Source component selection changed')
    sz, sy, sx = report['ct_spacing_zyx_mm']
    delta = np.asarray(report['frame_records'][0]['seg_position_lps']) - np.asarray(report['frame_records'][0]['ct_position_lps'])
    output.mkdir(parents=True, exist_ok=True)
    figures = []; component_rows = []
    def save(fig, name, info):
        fig.savefig(output / name, dpi=150); plt.close(fig)
        row = {'file': name, 'sha256': hashlib.sha256((output / name).read_bytes()).hexdigest(), **info}
        figures.append(row)
    def show(ax, pixels, selected, aspect, plane, x0, y0, window, marked):
        ax.imshow(pixels, cmap='gray', vmin=window[0], vmax=window[1], interpolation='nearest', aspect=aspect,
                  origin='upper' if plane == 'axial' else 'lower')
        if marked and selected.any():
            dx = delta[0] / sx if plane != 'sagittal' else delta[1] / sy
            dy = delta[1] / sy if plane == 'axial' else delta[2] / sz
            ax.contour(np.arange(selected.shape[1]) + dx, np.arange(selected.shape[0]) + dy,
                       selected, levels=[0.5], colors=['#ecb453'], linewidths=0.8)
        ax.set_xticks([]); ax.set_yticks([])
    # Every component receives independent local views, including the smaller selections.
    for number in range(1, count + 1):
        coords = np.argwhere(labels == number)
        low = np.maximum(coords.min(0) - 12, 0); high = np.minimum(coords.max(0) + 13, volume.shape)
        centre = np.rint(coords.mean(0)).astype(int)
        component_rows.append({'component': number, 'positive_voxels': len(coords), 'section_indices_zyx': centre.tolist(),
                               'crop_start_zyx': low.tolist(), 'crop_stop_exclusive_zyx': high.tolist(),
                               'node_and_station_identity_verified': False})
        views = [
            (volume[centre[0], low[1]:high[1], low[2]:high[2]], labels[centre[0], low[1]:high[1], low[2]:high[2]] == number, sy / sx, 'axial', low[2], low[1]),
            (volume[low[0]:high[0], centre[1], low[2]:high[2]], labels[low[0]:high[0], centre[1], low[2]:high[2]] == number, sz / sx, 'coronal', low[2], low[0]),
            (volume[low[0]:high[0], low[1]:high[1], centre[2]], labels[low[0]:high[0], low[1]:high[1], centre[2]] == number, sz / sy, 'sagittal', low[1], low[0])]
        for marked in (False, True):
            fig, axes = plt.subplots(2, 3, figsize=(12, 8))
            for row, window in enumerate([(-1000, 400), (-160, 240)]):
                for ax, (pixels, selected, aspect, plane, x0, y0) in zip(axes[row], views):
                    show(ax, pixels, selected, aspect, plane, x0, y0, window, marked)
                    ax.set_title(f'{plane}; native window {window}', fontsize=10)
            fig.suptitle(f'LNQ case_0571 | annotation component {number} | indices {centre.tolist()}\n'
                         + ('Original component contour; not an assigned node/station' if marked else 'Unmarked source CT detail; no annotation values changed'), fontsize=11)
            fig.tight_layout(rect=(0, 0, 1, 0.93))
            save(fig, f'component-{number:02d}-' + ('source-labels' if marked else 'unmarked') + '.png',
                 {'component': number, 'marked': marked, 'native_source_resampling': False})
    # Full set of encoded source planes is retained, including any all-zero encoded frame.
    indices = sorted({f['ct_index'] for f in report['frame_records']})
    coords = np.argwhere(mask)
    low = np.maximum(coords.min(0) - 18, 0); high = np.minimum(coords.max(0) + 19, volume.shape)
    for window_name, window in [('lung', (-1000, 400)), ('soft-tissue', (-160, 240))]:
        for marked in (False, True):
            rows = (len(indices) + 5) // 6
            fig, axes = plt.subplots(rows, 6, figsize=(18, rows * 3), squeeze=False)
            for ax in axes.ravel(): ax.axis('off')
            for ax, index in zip(axes.ravel(), indices):
                pixels = volume[index, low[1]:high[1], low[2]:high[2]]
                selection = mask[index, low[1]:high[1], low[2]:high[2]]
                show(ax, pixels, selection, sy / sx, 'axial', low[2], low[1], window, marked)
                ax.set_title(f'CT index {index}; SEG {int(selection.sum())} vox', fontsize=9)
            fig.suptitle(f'LNQ case_0571 | all {len(indices)} encoded native SEG planes | {window_name} window {window}\n'
                         + ('Original source contours; no completeness or malignancy inferred' if marked else 'Unmarked source CT; every encoded annotation plane retained'), fontsize=12)
            fig.tight_layout(rect=(0, 0, 1, 0.94))
            save(fig, 'all-encoded-planes-' + window_name + '-' + ('source-labels' if marked else 'unmarked') + '.png',
                 {'marked': marked, 'window': list(window), 'ct_indices': indices,
                  'crop_start_yx': low[1:].tolist(), 'crop_stop_exclusive_yx': high[1:].tolist(), 'native_source_resampling': False})
    result = {'case_id': 'case_0571', 'source_doi': report['source_doi'],
        'source_native_review_sha256': hashlib.sha256(source_review.read_bytes()).hexdigest(),
        'source_mask_sha256': report['reconstructed_mask_sha256'], 'source_ct_archive_sha256': report['ct_archive_sha256'],
        'components': component_rows, 'encoded_ct_planes_rendered': indices, 'encoded_seg_plane_count': len(indices),
        'rendered_positive_source_voxels': int(mask[indices].sum()), 'source_annotation_voxels': report['encoded_annotation_voxels'],
        'source_ct_seg_position_difference_mm_preserved': delta.tolist(), 'figures': figures,
        'native_source_resampling': False, 'original_source_labels_changed': False, 'clinical_approval': False,
        'node_or_station_identities_assigned': False, 'runtime_promoted': False,
        'limits': ['Complete source-annotation plane review does not prove complete clinical node coverage.',
                  'Component views are source-label selections, not individual-node or station labels.',
                  '2.5 mm native slice spacing and unresolved anatomical boundary confidence remain explicit.']}
    if result['rendered_positive_source_voxels'] != result['source_annotation_voxels']:
        raise ValueError('A positive source plane was omitted')
    (output / 'complete-boundary-view-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Rendered', len(figures), 'figures; all', len(indices), 'source planes;', int(mask.sum()), 'source voxels')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--review', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args(); render(a.source_root, a.review, a.output)
