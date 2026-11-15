#!/usr/bin/env python3
"""Review exact native CT/SEG correspondence; do not repair semantic labels."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile


def match_native_planes(ct_positions, seg_positions, tolerance=1e-6):
    import numpy as np
    ct = np.asarray(ct_positions, dtype=float)
    seg = np.asarray(seg_positions, dtype=float)
    if ct.ndim != 2 or ct.shape[1] != 3 or seg.shape != ct.shape:
        raise ValueError('Complete CT/SEG positions must both be N by 3')
    if not np.isfinite(ct).all() or not np.isfinite(seg).all():
        raise ValueError('Nonfinite positions')
    mapping = []
    for position in seg:
        matches = np.flatnonzero(np.max(np.abs(ct - position), axis=1) <= tolerance)
        if len(matches) != 1:
            raise ValueError('Missing or ambiguous native plane')
        mapping.append(int(matches[0]))
    if len(set(mapping)) != len(ct):
        raise ValueError('Repeated or omitted SEG plane')
    return mapping


def read_series(path):
    import pydicom
    with zipfile.ZipFile(path) as archive:
        return [pydicom.dcmread(io.BytesIO(archive.read(n))) for n in archive.namelist() if n.endswith('.dcm')]


def review(ct_archive, seg_archive, output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from audit_tcia_series_archive import audit_archive
    ct_integrity = audit_archive(ct_archive, 304, 160142106)
    seg_integrity = audit_archive(seg_archive, 1, 10130036)
    images = read_series(ct_archive)
    seg = read_series(seg_archive)[0]
    shared = seg.SharedFunctionalGroupsSequence[0]
    iop = np.asarray(images[0].ImageOrientationPatient, float)
    if not np.allclose(iop, [1, 0, 0, 0, 1, 0], atol=1e-9, rtol=0):
        raise ValueError('Reviewer display supports this declared axial LPS source only')
    spacing = np.asarray(images[0].PixelSpacing, float)
    first = images[0]
    for image in images:
        if (image.PatientID != 'R01-001' or image.SeriesInstanceUID != first.SeriesInstanceUID
                or image.FrameOfReferenceUID != first.FrameOfReferenceUID
                or image.Rows != 512 or image.Columns != 512
                or not np.allclose(image.ImageOrientationPatient, iop, atol=1e-9, rtol=0)
                or not np.allclose(image.PixelSpacing, spacing, atol=1e-9, rtol=0)):
            raise ValueError('Inconsistent native CT identity or grid')
    if seg.FrameOfReferenceUID != first.FrameOfReferenceUID or seg.PatientID != first.PatientID:
        raise ValueError('SEG patient/frame differs')
    ref = seg.ReferencedSeriesSequence
    if len(ref) != 1 or ref[0].SeriesInstanceUID != first.SeriesInstanceUID:
        raise ValueError('SEG refers to another series')
    actual_sops = {str(im.SOPInstanceUID) for im in images}
    declared_sops = {str(im.ReferencedSOPInstanceUID) for im in ref[0].ReferencedInstanceSequence}
    if len(actual_sops) != len(images) or declared_sops != actual_sops:
        raise ValueError('Complete SEG source-instance references differ')
    if (seg.SegmentationType != 'BINARY' or len(seg.SegmentSequence) != 1
            or shared.SegmentIdentificationSequence[0].ReferencedSegmentNumber != seg.SegmentSequence[0].SegmentNumber
            or not np.allclose(shared.PlaneOrientationSequence[0].ImageOrientationPatient, iop, atol=1e-9, rtol=0)
            or not np.allclose(shared.PixelMeasuresSequence[0].PixelSpacing, spacing, atol=1e-9, rtol=0)):
        raise ValueError('Unexpected SEG type, identity or orientation/spacing')
    images.sort(key=lambda im: float(im.ImagePositionPatient[2]))
    positions = np.asarray([im.ImagePositionPatient for im in images], float)
    steps = np.diff(positions, axis=0)
    if not np.allclose(steps, [0, 0, 1], atol=1e-6, rtol=0):
        raise ValueError('Native slice positions are irregular, repeated or sheared')
    seg_positions = [f.PlanePositionSequence[0].ImagePositionPatient for f in seg.PerFrameFunctionalGroupsSequence]
    mapping = match_native_planes(positions, seg_positions)
    raw_seg = seg.pixel_array
    if raw_seg.shape != (304, 512, 512) or set(np.unique(raw_seg)) != {0, 1}:
        raise ValueError('Unexpected segmentation shape or values')
    mask = np.empty_like(raw_seg)
    for source_index, target_index in enumerate(mapping):
        mask[target_index] = raw_seg[source_index]
    stored = np.stack([im.pixel_array for im in images])
    slopes = np.asarray([float(im.RescaleSlope) for im in images])
    intercepts = np.asarray([float(im.RescaleIntercept) for im in images])
    volume = stored.astype(np.float64) * slopes[:, None, None] + intercepts[:, None, None]
    points = np.argwhere(mask)
    centre = np.rint(points.mean(axis=0)).astype(int)
    bounds = [points.min(axis=0).tolist(), points.max(axis=0).tolist()]
    output.mkdir(parents=True, exist_ok=True)
    views = [(volume[centre[0]], mask[centre[0]], spacing[0] / spacing[1], 'Axial', int(centre[0])),
             (volume[:, centre[1], :], mask[:, centre[1], :], 1 / spacing[1], 'Coronal', int(centre[1])),
             (volume[:, :, centre[2]], mask[:, :, centre[2]], 1 / spacing[0], 'Sagittal', int(centre[2]))]
    figure_records = []
    for marked in (False, True):
        fig, axes = plt.subplots(2, 3, figsize=(15, 10), facecolor='white')
        for row, window in enumerate([(-1000, 400), (-160, 240)]):
            for ax, (pixels, labels, aspect, title, index) in zip(axes[row], views):
                origin = 'upper' if title == 'Axial' else 'lower'
                ax.imshow(pixels, cmap='gray', vmin=window[0], vmax=window[1], aspect=aspect,
                          origin=origin, interpolation='nearest')
                if marked and labels.any():
                    ax.contour(np.arange(labels.shape[1]), np.arange(labels.shape[0]), labels,
                               levels=[0.5], colors=['#e8b54f'], linewidths=0.8)
                ax.set_title(f'{title} native index {index}; window {window}', fontsize=10)
                ax.set_xticks([]); ax.set_yticks([])
        fig.suptitle('NSCLC-Radiogenomics R01-001 | exact native CT sections\n'
                     + ('Original SEG contour: coded Heart; target identity held' if marked else 'Unmarked source CT; no segmentation identity inferred'), fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        name = 'r01-001-native-' + ('declared-seg' if marked else 'unmarked') + '.png'
        fig.savefig(output / name, dpi=150); plt.close(fig)
        figure_records.append({'file': name, 'sha256': hashlib.sha256((output / name).read_bytes()).hexdigest(),
                               'native_voxels_resampled': False, 'annotation_overlaid': marked})
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), facecolor='white')
    low = np.maximum(points.min(axis=0) - 16, 0)
    high = np.minimum(points.max(axis=0) + 17, volume.shape)
    ranges = [(low[2], high[2], low[1], high[1]),
              (low[2], high[2], low[0], high[0]),
              (low[1], high[1], low[0], high[0])]
    for row, window in enumerate([(-1000, 400), (-160, 240)]):
        for ax, (pixels, labels, aspect, title, index), (x0, x1, y0, y1) in zip(axes[row], views, ranges):
            ax.imshow(pixels[y0:y1, x0:x1], cmap='gray', vmin=window[0], vmax=window[1],
                      aspect=aspect, origin='upper' if title == 'Axial' else 'lower', interpolation='nearest')
            ax.set_title(f'{title} {index}; x[{x0}:{x1}], y[{y0}:{y1}]', fontsize=9)
            ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle('R01-001 unmarked native CT detail | source SEG bounding region only\n'
                 'No target relabelling, contour, fitted alignment or source resampling', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    name = 'r01-001-native-unmarked-detail.png'
    fig.savefig(output / name, dpi=150); plt.close(fig)
    figure_records.append({'file': name, 'sha256': hashlib.sha256((output / name).read_bytes()).hexdigest(),
                           'native_voxels_resampled': False, 'annotation_overlaid': False,
                           'crop_ranges': [list(map(int, r)) for r in ranges]})
    declared = seg.SegmentSequence[0]
    prop = declared.SegmentedPropertyTypeCodeSequence[0]
    report = {'case_id': 'R01-001', 'source_doi': '10.7937/K9/TCIA.2017.7hs46erv',
        'ct_series_instance_uid': str(first.SeriesInstanceUID), 'seg_series_instance_uid': str(seg.SeriesInstanceUID),
        'ct_archive_sha256': ct_integrity['archive_sha256'], 'seg_archive_sha256': seg_integrity['archive_sha256'],
        'complete_publisher_file_md5_verified': True, 'shape_zyx': list(volume.shape),
        'spacing_zyx_mm': [1, *spacing.tolist()], 'native_lps_origin': positions[0].tolist(),
        'native_iop': iop.tolist(), 'matching_source_sops': len(actual_sops), 'matching_native_planes': len(mapping),
        'max_plane_coordinate_difference_mm': float(np.max(np.abs(positions[np.asarray(mapping)] - np.asarray(seg_positions)))),
        'ct_rescale_slopes': sorted(set(slopes.tolist())), 'ct_rescale_intercepts': sorted(set(intercepts.tolist())),
        'ct_rescale_types': sorted({str(getattr(im, 'RescaleType', 'not_reported')) for im in images}),
        'convolution_kernels': sorted({str(getattr(im, 'ConvolutionKernel', 'not_reported')) for im in images}),
        'contrast_bolus_agents': sorted({str(getattr(im, 'ContrastBolusAgent', 'not_reported')) for im in images}),
        'contrast_phase_verified': False, 'source_annotation': {'segment_label': str(declared.SegmentLabel),
            'property_code': str(prop.CodeValue), 'property_scheme': str(prop.CodingSchemeDesignator),
            'property_meaning': str(prop.CodeMeaning), 'algorithm_type': str(declared.SegmentAlgorithmType),
            'algorithm_name': str(declared.SegmentAlgorithmName)},
        'positive_voxels': int(len(points)), 'annotation_bbox_zyx_inclusive': bounds,
        'section_indices_zyx': centre.tolist(), 'figures': figure_records,
        'status': 'held_source_semantic_identity_conflict', 'source_segmentation_values_changed': False,
        'clinical_approval': False, 'runtime_bindings_added': False,
        'limitations': ['SEG explicitly labels/codes Heart; not automatically recoded as tumour.',
                        'AIM/clinical descriptions are separate source evidence; neither changes SEG metadata.',
                        'Exact grid/source consistency does not prove target identity, boundaries or clinical fidelity.',
                        'No verified phase, station map, invasive interface or complete staging coverage.']}
    (output / 'r01-001-native-review.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Native planes:', len(mapping), '; positive voxels:', len(points), '; declared target:', declared.SegmentLabel)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ct-archive', type=Path, required=True)
    p.add_argument('--seg-archive', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    review(a.ct_archive, a.seg_archive, a.output)
