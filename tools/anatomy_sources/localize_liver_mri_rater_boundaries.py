#!/usr/bin/env python3
"""Locate source adjacency ambiguity and independent rater mask disagreement on native MRI."""
import argparse
import hashlib
import json
from pathlib import Path


def adjacency_locations(mask):
    import numpy as np
    from tools.anatomy_sources.localize_aeropath_adjacency import CORNERS, cube_components
    if mask.dtype != np.bool_ or mask.ndim != 3 or not mask.any():
        raise ValueError('Need nonempty binary 3D source selection')
    if any(mask.take(index, axis=axis).any() for axis in range(3) for index in (0, -1)):
        raise ValueError('Source selection touches boundary; do not pad as acquired anatomy')
    points = np.argwhere(mask); lo = points.min(0) - 1; hi = points.max(0) + 2
    crop = mask[tuple(slice(a, b) for a, b in zip(lo, hi))]; shape = np.asarray(crop.shape) - 1
    codes = np.zeros(shape, np.uint8)
    for index, corner in enumerate(CORNERS):
        codes |= crop[tuple(slice(c, c+n) for c, n in zip(corner, shape))].astype(np.uint8) << index
    fore, back = cube_components(); sensitive = (fore[codes] > 1) | (back[codes] > 1)
    return np.argwhere(sensitive)+lo, codes[sensitive], {'complete_native_cubes_checked': int(codes.size),
            'bounds_start_ijk': lo.tolist(), 'bounds_stop_exclusive_ijk': hi.tolist(),
            'foreground_disconnected_cubes': int((fore[codes] > 1).sum()),
            'background_disconnected_cubes': int((back[codes] > 1).sum())}


def outside_components(liver, tumour):
    import numpy as np
    from scipy import ndimage
    if liver.dtype != np.bool_ or tumour.dtype != np.bool_ or liver.shape != tumour.shape:
        raise ValueError('Need same-grid binary source masks')
    outside = tumour & ~liver; labels, count = ndimage.label(outside, ndimage.generate_binary_structure(3, 3))
    rows = []
    for label in range(1, count+1):
        points = np.argwhere(labels == label); planes, counts = np.unique(points[:, 2], return_counts=True)
        rows.append({'component_26': label, 'voxels': len(points), 'bounds_start_ijk': points.min(0).tolist(),
                     'bounds_stop_exclusive_ijk': (points.max(0)+1).tolist(),
                     'native_z_planes': [{'index': int(z), 'voxels': int(n)} for z, n in zip(planes, counts)],
                     'clinical_invasion_or_annotation_error_inferred': False})
    return outside, {'total_outside_tumour_voxels': int(outside.sum()), 'components_6': int(ndimage.label(outside)[1]),
                     'components_26': count, 'components': rows, 'source_masks_changed': False}


def review(root, inventory_path, output):
    import numpy as np
    import nibabel as nib
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from tools.anatomy_sources.localize_aeropath_adjacency import cube_components
    source = json.loads(inventory_path.read_text()); entries = {r['filename']: r for r in source['records']}
    names = ['art.nii.gz', 'rater1_liver.nii.gz', 'rater2_liver.nii.gz', 'rater1_tumor1.nii.gz', 'rater2_tumor1.nii.gz']
    images = {}; arrays = {}
    for name in names:
        path = root/name
        if hashlib.sha256(path.read_bytes()).hexdigest() != entries[name]['sha256']: raise ValueError('Source changed')
        images[name] = nib.load(path); arrays[name] = np.asanyarray(images[name].dataobj)
    image = images['art.nii.gz']; affine = image.affine; spacing = np.asarray(image.header.get_zooms()[:3]); volume = arrays['art.nii.gz']
    if nib.aff2axcodes(affine) != ('R', 'A', 'S') or not np.array_equal(affine[:3, :3], np.diag(spacing)):
        raise ValueError('Source direction requires separate review')
    for name in names[1:]:
        if images[name].shape != image.shape or not np.array_equal(images[name].affine, affine) or set(np.unique(arrays[name])) != {0, 1}:
            raise ValueError('Source binary mask geometry differs')
        arrays[name] = arrays[name] > 0
    output.mkdir(parents=True, exist_ok=True); figures = []; records = []; windows = np.percentile(volume, [2, 98])
    def patch_figure(name, liver, tumour, planes, bounds, title, cube_origin=None):
        x0, y0, x1, y1 = bounds
        x = affine[0, 3] + np.arange(x0, x1) * spacing[0]; y = affine[1, 3] + np.arange(y0, y1) * spacing[1]
        extent = [x[-1]+spacing[0]/2, x[0]-spacing[0]/2, y[0]-spacing[1]/2, y[-1]+spacing[1]/2]
        fig, axes = plt.subplots(len(planes), 2, figsize=(10, max(5, 3.8*len(planes))), squeeze=False, layout='constrained')
        for row, z in enumerate(planes):
            for col, marked in enumerate((False, True)):
                ax = axes[row, col]; pixels = volume[x0:x1, y0:y1, z].T[:, ::-1]
                ax.imshow(pixels, cmap='gray', origin='lower', extent=extent, interpolation='nearest', aspect='equal', vmin=windows[0], vmax=windows[1])
                if marked:
                    for mask, colour in ((liver, '#ecb453'), (tumour, '#65b6dc')):
                        plane = mask[x0:x1, y0:y1, z].T[:, ::-1]
                        if plane.any() and not plane.all(): ax.contour(x[::-1], y, plane, levels=[.5], colors=[colour], linewidths=.9)
                    outside = (tumour & ~liver)[x0:x1, y0:y1, z].T[:, ::-1]
                    if outside.any(): ax.contourf(x[::-1], y, outside, levels=[.5, 1.5], colors=['#de5260'], alpha=.3)
                    if cube_origin is not None:
                        point = nib.affines.apply_affine(affine, np.asarray(cube_origin)+.5)
                        ax.plot(point[0], point[1], 'r+', markersize=9)
                ax.set_title(f'Original arterial MRI | native z={z} | ' + ('source contours' if marked else 'unmarked'), fontsize=9)
                ax.set_xlabel('RAS X mm (R → L)', fontsize=8); ax.set_ylabel('RAS Y mm (P → A)', fontsize=8)
        fig.suptitle(title+'\nLiver amber / tumour blue / outside-liver label red; source sampling unchanged; no clinical cause inferred', fontsize=10)
        path = output/(name+'.png'); fig.savefig(path, dpi=140); plt.close(fig)
        row = {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'native_z_indices': list(map(int, planes)),
               'patch_start_xy': [int(x0), int(y0)], 'patch_stop_exclusive_xy': [int(x1), int(y1)], 'source_resampled': False}
        figures.append(row); return row
    for rater in (1, 2):
        liver = arrays[f'rater{rater}_liver.nii.gz']; tumour = arrays[f'rater{rater}_tumor1.nii.gz']
        origins, codes, stats = adjacency_locations(liver)
        path = output/f'rater{rater}-liver-adjacency-locations.npz'; np.savez_compressed(path, native_origins_ijk=origins, configuration_codes=codes)
        fore, back = cube_components(); unique, counts = np.unique(codes, return_counts=True)
        cube_planes, frequencies = np.unique(origins[:, 2], return_counts=True); selected = []
        for index, origin in enumerate(origins):
            i, j, k = map(int, origin)
            bounds = (max(i-8, 0), max(j-8, 0), min(i+10, liver.shape[0]), min(j+10, liver.shape[1]))
            fig = patch_figure(f'rater{rater}-adjacency-{i}-{j}-{k}', liver, tumour, [k, k+1], bounds,
                               f'Rater {rater} | adjacency-sensitive liver cube IJK {origin.tolist()} | code {int(codes[index])}', origin)
            selected.append({'cube_origin_ijk': origin.tolist(), 'source_cube_values': liver[i:i+2, j:j+2, k:k+2].astype(int).tolist(),
                             'configuration_code': int(codes[index]), 'figure': fig['file']})
        outside, relations = outside_components(liver, tumour)
        outside_points = np.argwhere(outside); path_out = output/f'rater{rater}-outside-liver-locations.npz'; np.savez_compressed(path_out, native_indices_ijk=outside_points)
        relation_figures = []
        for component in relations['components']:
            lo = np.asarray(component['bounds_start_ijk']); hi = np.asarray(component['bounds_stop_exclusive_ijk'])
            planes = [p['index'] for p in component['native_z_planes']]
            bounds = (max(int(lo[0])-8, 0), max(int(lo[1])-8, 0), min(int(hi[0])+8, liver.shape[0]), min(int(hi[1])+8, liver.shape[1]))
            for start in range(0, len(planes), 3):
                fig = patch_figure(f'rater{rater}-outside-component{component["component_26"]}-page{start//3+1}', liver, tumour, planes[start:start+3], bounds,
                                   f'Rater {rater} | tumour outside own liver label | component {component["component_26"]} ({component["voxels"]} voxels)')
                relation_figures.append(fig['file'])
        records.append({'rater': rater, 'liver_source_sha256': entries[f'rater{rater}_liver.nii.gz']['sha256'],
                        'tumour_source_sha256': entries[f'rater{rater}_tumor1.nii.gz']['sha256'], **stats,
                        'adjacency_sensitive_cubes': len(origins), 'adjacency_locations_file': path.name,
                        'adjacency_locations_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'configurations': [{'code': int(c), 'cubes': int(n), 'foreground_6_components': int(fore[c]), 'background_6_components': int(back[c])} for c, n in zip(unique, counts)],
                        'native_z_cube_counts': [{'index': int(z), 'cubes': int(n)} for z, n in zip(cube_planes, frequencies)],
                        'selected_sites': selected, 'source_mask_relations': relations,
                        'outside_locations_file': path_out.name, 'outside_locations_sha256': hashlib.sha256(path_out.read_bytes()).hexdigest(),
                        'mask_relation_figures': relation_figures, 'all_adjacency_cubes_displayed': len(selected) == len(origins),
                        'all_outside_component_z_planes_displayed': True})
        print('Rater', rater, 'adjacency cubes', len(origins), 'outside voxels', relations['total_outside_tumour_voxels'], '26-components', relations['components_26'], flush=True)
    result = {'case_id': source['case_id'], 'source_doi': source['source_doi'], 'source_inventory_sha256': hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
              'original_arterial_sha256': entries['art.nii.gz']['sha256'], 'records': records, 'figures': figures,
              'source_masks_changed': False, 'source_raters_merged': False, 'clinical_approval': False, 'runtime_promoted': False,
              'limits': ['Adjacency-sensitive cubes are not handle locations, artifact diagnoses or proof of pathological boundaries.',
                         'Every adjacency cube and every affected component Z plane is displayed; localization still does not establish anatomical boundary accuracy.',
                         'Outside-liver tumour label components are annotation relations, not separate lesions or invasion.',
                         'No connectivity repair, boundary consensus or automatic clinical coverage is granted.']}
    (output/'boundary-localization-review.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-root',type=Path,required=True);parser.add_argument('--inventory',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();review(a.case_root,a.inventory,a.output)
