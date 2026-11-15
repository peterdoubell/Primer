#!/usr/bin/env python3
"""Compare direct model sections on original CT at native topology-sensitive sites."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def render(root, native_review, comparison_path, site_path, output):
    import numpy as np
    import nibabel as nib
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from tools.anatomy_sources.audit_massp_mesh_voxels import section
    from tools.anatomy_sources.review_tcia_lung_case import read_series
    review = json.loads(native_review.read_text()); comparison = json.loads(comparison_path.read_text())
    sites = json.loads(site_path.read_text())['selected_sites']
    ct_path = root / 'case_0571-ct.zip'
    if hashlib.sha256(ct_path.read_bytes()).hexdigest() != review['ct_archive_sha256']:
        raise ValueError('Original source CT changed')
    baseline_root = root / 'lnq-case-0571-derived/surface'
    baseline = json.loads((baseline_root / 'surface-review.json').read_text())
    baseline_affine = np.asarray(baseline['native_seg_affine_zyx_to_ras'])
    study_root = root / 'lnq-case-0571-derived/interpolation-study'
    paths = [(baseline_root / baseline['mesh_file'], baseline['mesh_sha256'], 'Original MC baseline', '#ecb453')]
    paths += [(study_root / r['mesh_file'], r['mesh_sha256'], r['choice'], colour) for r, colour in zip(comparison['records'], ['#e46b71', '#6bb7e4', '#4aa98f', '#b493d3'])]
    meshes = []
    for path, expected, name, colour in paths:
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Source-derived comparison mesh changed')
        with np.load(path) as m:
            native = nib.affines.apply_affine(np.linalg.inv(baseline_affine), m['vertices'])
            triangles = native[m['faces']]
        meshes.append((triangles, name, colour))
    images = read_series(ct_path); images.sort(key=lambda d: float(d.ImagePositionPatient[2]))
    delta = np.asarray(review['frame_records'][0]['seg_position_lps']) - np.asarray(review['frame_records'][0]['ct_position_lps'])
    sz, sy, sx = review['ct_spacing_zyx_mm']
    fig, axes = plt.subplots(len(sites), 6, figsize=(18, 4.0 * len(sites)), squeeze=False)
    selected = []
    for row, site in enumerate(sites):
        z, y, x = site['native_cube_origin_zyx']; y0, x0 = site['patch_start_yx']; y1, x1 = site['patch_stop_exclusive_yx']
        d = images[z]; pixels = d.pixel_array[y0:y1, x0:x1].astype(float) * float(d.RescaleSlope) + float(d.RescaleIntercept)
        for column, ax in enumerate(axes[row]):
            ax.imshow(pixels, cmap='gray', vmin=-160, vmax=240, origin='upper', interpolation='nearest', aspect=sy / sx)
            if column:
                triangles, name, colour = meshes[column - 1]
                edges = section(triangles, 0, z, 2, 1)
                for a, b in edges:
                    ax.plot([a[0] - x0 + delta[0] / sx, b[0] - x0 + delta[0] / sx],
                            [a[1] - y0 + delta[1] / sy, b[1] - y0 + delta[1] / sy], colour, linewidth=0.8)
                ax.set_title(name, fontsize=9)
            else:
                ax.set_title(f'Unmarked CT\nz={z}; cube {site["native_cube_origin_zyx"]}', fontsize=9)
            ax.set_xlim(-0.5, x1 - x0 - 0.5); ax.set_ylim(y1 - y0 - 0.5, -0.5)
            ax.set_xticks([]); ax.set_yticks([])
        selected.append({'native_cube_origin_zyx': [z, y, x], 'displayed_ct_index': z,
                         'crop_start_yx': [y0, x0], 'crop_stop_exclusive_yx': [y1, x1],
                         'section_basis': 'Direct source-derived surface intersections at the original native SEG index plane; original tiny SEG/CT offset preserved.'})
    fig.suptitle('LNQ case_0571 | unchanged labels, different subvoxel interpolation choices\n'
                 'Native 2.5 mm CT slice sampling; direct model sections, no anatomy/diagnosis/correction inferred', fontsize=12)
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.03, top=0.89, hspace=0.4, wspace=0.15)
    output.mkdir(parents=True, exist_ok=True)
    path = output / 'case-0571-native-interpolation-comparison.png'; fig.savefig(path, dpi=150); plt.close(fig)
    record = {'source_doi': review['source_doi'], 'case_id': 'case_0571',
              'comparison_evidence_sha256': hashlib.sha256(comparison_path.read_bytes()).hexdigest(),
              'site_evidence_sha256': hashlib.sha256(site_path.read_bytes()).hexdigest(),
              'figure_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'selected_sites': selected,
              'source_ct_voxels_resampled': False, 'source_labels_changed': False,
              'source_meshes_changed': False, 'clinical_approval': False, 'runtime_promoted': False,
              'limits': 'Selected direct sections expose geometric interpolation differences, not full 3D boundary accuracy or an anatomical reason to prefer any surface.'}
    (output / 'case-0571-interpolation-figure-review.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Rendered direct model sections at', len(sites), 'native CT sites')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--review', type=Path, required=True)
    p.add_argument('--comparison', type=Path, required=True); p.add_argument('--sites', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    render(a.source_root, a.review, a.comparison, a.sites, a.output)
