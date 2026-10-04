#!/usr/bin/env python3
"""Render separate unmarked native pancreatic CT sections without registration."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile


def verified_objects(root, case, role, expected_sha):
    import pydicom
    receipt = json.loads((root / (case + '-' + role + '-archive-audit.json')).read_text())
    if receipt['archive_sha256'] != expected_sha:
        raise ValueError('Receipt differs from original geometry audit')
    with (root / (case + '-' + role + '.zip')).open('rb') as source:
        digest = hashlib.sha256()
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
        if digest.hexdigest() != expected_sha:
            raise ValueError('Original archive changed')
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            return [pydicom.dcmread(io.BytesIO(archive.read(row['member'])))
                    for row in receipt['members']]


def native_region(points, origin, spacing_xyz, shape_zyx, margin_mm=25):
    """Select native indices; the source annotation is solely a location aid."""
    import numpy as np
    points = np.asarray(points, float)
    spacing = np.asarray(spacing_xyz, float)
    shape = np.asarray(shape_zyx[::-1], int)
    if points.ndim != 2 or points.shape[1] != 3 or not len(points) or not np.isfinite(points).all():
        raise ValueError('Invalid source location points')
    if np.any(spacing <= 0) or margin_mm < 0:
        raise ValueError('Invalid source sampling or review margin')
    indices = (points - origin) / spacing
    if np.any(indices < -.5) or np.any(indices > shape - .5):
        raise ValueError('Source location outside native grid')
    centre = np.rint((indices.min(0) + indices.max(0)) / 2).astype(int)
    start = np.maximum(np.floor(indices.min(0) - margin_mm / spacing).astype(int), 0)
    stop = np.minimum(np.ceil(indices.max(0) + margin_mm / spacing).astype(int) + 1, shape)
    if np.any(centre < start) or np.any(centre >= stop):
        raise ValueError('Selected plane outside review region')
    return centre, start, stop


def render(root, selection_path, geometry_path, output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from tools.anatomy_sources.acquire_cptac_pancreatic_case import validate_selection
    selection = json.loads(selection_path.read_text())
    validate_selection(selection)
    geometry = json.loads(geometry_path.read_text())
    selection_sha = hashlib.sha256(selection_path.read_bytes()).hexdigest()
    if geometry['source_selection_sha256'] != selection_sha:
        raise ValueError('Selection differs from geometry audit')
    output.mkdir(parents=True, exist_ok=True)
    results = []
    case = selection['case_id']
    for pair in selection['source_pairs']:
        role = pair['role']
        record = next(r for r in geometry['records'] if r['source_role'] == role)
        images = verified_objects(root, case, role + '-ct', record['ct_archive_sha256'])
        annotations = verified_objects(root, case, role + '-annotation', record['annotation_archive_sha256'])
        if len(annotations) != 1 or len(images) != record['ct_objects']:
            raise ValueError('Original object counts differ')
        if any(list(map(float, d.ImageOrientationPatient)) != [1, 0, 0, 0, 1, 0]
               or str(d.SeriesInstanceUID) != record['original_ct_series_uid']
               or str(d.PatientID) != case or str(d.RescaleType) != 'HU' for d in images):
            raise ValueError('Only audited axial source HU grids are supported')
        images.sort(key=lambda d: float(d.ImagePositionPatient[2]))
        positions = np.asarray([d.ImagePositionPatient for d in images], float)
        affine = np.asarray(record['native_index_zyx_to_lps_mm'], float)
        expected = affine[:3, 3] + np.arange(len(images))[:, None] * affine[:3, 0]
        if not np.array_equal(positions, expected):
            raise ValueError('Original native positions differ from audit')
        sy, sx = record['source_pixel_spacing_mm']
        sz = float(affine[2, 0])
        if [sx, sy, sz] != [.703125, .703125, .625] or not np.array_equal(affine[:3, :3], [[0, 0, sx], [0, sy, 0], [sz, 0, 0]]):
            raise ValueError('Unreviewed source shear or orientation')
        if any(list(map(float, d.PixelSpacing)) != [sy, sx] or
               [d.Rows, d.Columns] != record['source_shape_zyx'][1:] for d in images):
            raise ValueError('Source shape or spacing differs')
        volume = np.stack([d.pixel_array.astype(np.float64) * float(d.RescaleSlope)
                           + float(d.RescaleIntercept) for d in images])
        rt = annotations[0]
        if str(rt.SeriesInstanceUID) != pair['annotation_series']['SeriesInstanceUID']:
            raise ValueError('Source annotation differs')
        lookup = {str(d.SOPInstanceUID): i for i, d in enumerate(images)}
        points = []
        for roi in rt.ROIContourSequence:
            for c in roi.ContourSequence:
                refs = [str(r.ReferencedSOPInstanceUID) for r in c.ContourImageSequence]
                p = np.asarray(c.ContourData, float).reshape(-1, 3)
                if len(refs) != 1 or refs[0] not in lookup or str(c.ContourGeometricType) != 'CLOSED_PLANAR':
                    raise ValueError('Contour does not directly reference this native CT')
                if not np.all(p[:, 2] == positions[lookup[refs[0]], 2]):
                    raise ValueError('Source contour is off its referenced plane')
                points.append(p)
        if len(points) != len(record['contours']):
            raise ValueError('Source contour count differs')
        centre, start, stop = native_region(np.concatenate(points), positions[0], [sx, sy, sz], volume.shape)
        xi, yi, zi = map(int, centre)
        x0, y0, z0 = map(int, start)
        x1, y1, z1 = map(int, stop)
        # RAS millimetres are labels only; no array resampling or inter-series fit.
        x = -positions[0, 0] - np.arange(x0, x1) * sx
        y = -positions[0, 1] - np.arange(y0, y1) * sy
        z = positions[0, 2] + np.arange(z0, z1) * sz
        views = [
            (volume[zi, y0:y1, x0:x1], [x[0]+sx/2, x[-1]-sx/2, y[-1]-sy/2, y[0]+sy/2], 'upper', 'Axial', 0, zi, 'RAS X mm (R → L)', 'RAS Y mm (P → A)'),
            (volume[z0:z1, yi, x0:x1], [x[0]+sx/2, x[-1]-sx/2, z[0]-sz/2, z[-1]+sz/2], 'lower', 'Coronal', 1, yi, 'RAS X mm (R → L)', 'RAS Z mm (I → S)'),
            (volume[z0:z1, y0:y1, xi], [y[0]+sy/2, y[-1]-sy/2, z[0]-sz/2, z[-1]+sz/2], 'lower', 'Sagittal', 2, xi, 'RAS Y mm (A → P)', 'RAS Z mm (I → S)')]
        fig, axes = plt.subplots(2, 3, figsize=(12, 8), layout='constrained')
        for row, (low, high, label) in enumerate([(-160, 240, 'Soft-tissue display'), (-600, 1000, 'Wide display')]):
            for ax, (pixels, extent, mode, name, axis, index, xlabel, ylabel) in zip(axes[row], views):
                ax.imshow(pixels, cmap='gray', vmin=low, vmax=high, extent=extent, origin=mode, interpolation='nearest', aspect='equal')
                ax.set_title(f'{name} | native index {index}\n{label}: {low} to {high} HU', fontsize=9)
                ax.set_xlabel(xlabel, fontsize=8); ax.set_ylabel(ylabel, fontsize=8); ax.tick_params(labelsize=7)
        fig.suptitle(f'{case} | {role} original CT | selected unmarked native sections\n'
                     '0.703125 × 0.703125 × 0.625 mm; phase/diagnosis/boundaries unapproved; no annotation/model overlay', fontsize=10)
        path = output / (case + '-' + role + '-native-ct.png')
        fig.savefig(path, dpi=150); plt.close(fig)
        results.append({'source_role': role, 'figure': path.name, 'figure_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'ct_archive_sha256': record['ct_archive_sha256'], 'annotation_archive_sha256': record['annotation_archive_sha256'],
                        'source_shape_zyx': list(volume.shape), 'source_sampling_zyx_mm': [sz, sy, sx],
                        'source_acquisition_number': record['acquisitions'][0]['source_acquisition_number'],
                        'source_acquisition_time': record['acquisitions'][0]['source_acquisition_time'],
                        'axial_source_sop_instance_uid': str(images[zi].SOPInstanceUID),
                        'planes': [{'axis_zyx': axis, 'index': index, 'resampling': False,
                                    'selected_hu_shape': list(pixels.shape),
                                    'selected_hu_float64_le_sha256': hashlib.sha256(np.ascontiguousarray(pixels, dtype='<f8').tobytes()).hexdigest(),
                                    'display_extent_ras_mm': list(map(float, extent)), 'display_origin': mode}
                                   for pixels, extent, mode, _, axis, index, _, _ in views],
                        'crop_start_zyx': start[::-1].tolist(), 'crop_stop_exclusive_zyx': stop[::-1].tolist(),
                        'display_hu_windows': [[-160, 240], [-600, 1000]], 'source_rescale_applied_per_object': True,
                        'annotation_is_location_aid_only': True, 'native_sections_registered_between_roles': False})
        del volume, images
        print('Rendered', path, flush=True)
    result = {'case_id': case, 'image_doi': selection['original_image_doi'], 'annotation_doi': selection['annotation_doi'],
              'image_license': 'CC BY 4.0', 'annotation_license': 'CC BY 4.0', 'source_selection_sha256': selection_sha,
              'geometry_review_sha256': hashlib.sha256(geometry_path.read_bytes()).hexdigest(), 'records': results,
              'selection_basis': 'Each own annotation bounding-box midpoint and 25 mm physical margin, clipped to acquired extent; not measured anatomical centre or full organ coverage.',
              'source_voxels_resampled': False, 'annotation_overlay': False, 'model_overlay': False,
              'tracking_identity_reconciled': False, 'phase_adequacy_verified': False, 'histological_diagnosis_verified': False,
              'complete_pancreatic_anatomy_verified': False, 'clinical_approval': False, 'runtime_promoted': False}
    (output / (case + '-native-sections.provenance.json')).write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--selection', type=Path, required=True)
    p.add_argument('--geometry', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    render(a.source_root, a.selection, a.geometry, a.output)
