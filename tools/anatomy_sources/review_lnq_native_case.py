#!/usr/bin/env python3
"""Audit same-case LNQ CT/SEG references and preserve incomplete-label semantics."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.audit_tcia_series_archive import audit_archive
from tools.anatomy_sources.review_tcia_lung_case import read_series


def coordinate_roundtrip_check(ct_position, seg_position):
    import numpy as np
    source = np.asarray(ct_position, dtype=float)
    target = np.asarray(seg_position, dtype=float)
    if source.shape != (3,) or target.shape != (3,) or not np.isfinite(source).all() or not np.isfinite(target).all():
        raise ValueError('Invalid native position')
    delta = np.abs(source - target)
    if np.max(delta) <= 1e-9:
        return {'mode': 'exact_decimal_position', 'max_difference_mm': float(np.max(delta))}
    expected = np.round(source.astype(np.float32).astype(np.float64), 6)
    if np.max(delta) > 1e-5 or np.max(np.abs(expected - target)) > 1e-9:
        raise ValueError('Position is neither exact nor consistent with float32/six-decimal roundtrip')
    return {'mode': 'consistent_with_float32_six_decimal_roundtrip',
            'max_difference_mm': float(np.max(delta)),
            'quantization_consistency_is_not_proof_of_author_conversion': True}


def review(root, output):
    import numpy as np
    from scipy import ndimage
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    series = json.loads((root / 'case_0571-series.json').read_text())
    ct_meta = next(s for s in series if s['Modality'] == 'CT')
    seg_meta = next(s for s in series if s['Modality'] == 'SEG')
    if seg_meta['SeriesDescription'] != 'Fully Annotated':
        raise ValueError('Source annotation scope changed')
    for meta in (ct_meta, seg_meta):
        if meta['PatientID'] != 'case_0571' or meta['LicenseURI'] != 'https://creativecommons.org/licenses/by/4.0/':
            raise ValueError('Case or source licence changed')
    ct_path, seg_path = root / 'case_0571-ct.zip', root / 'case_0571-seg.zip'
    ct_integrity = audit_archive(ct_path, ct_meta['ImageCount'], ct_meta['FileSize'])
    seg_integrity = audit_archive(seg_path, seg_meta['ImageCount'], seg_meta['FileSize'])
    images = read_series(ct_path); seg = read_series(seg_path)[0]
    images.sort(key=lambda d: float(d.ImagePositionPatient[2]))
    first = images[0]; orientation = [1, 0, 0, 0, 1, 0]
    spacing = np.asarray(first.PixelSpacing, float)
    positions = np.asarray([d.ImagePositionPatient for d in images], float)
    for d in images:
        if (d.PatientID != 'case_0571' or d.SeriesInstanceUID != ct_meta['SeriesInstanceUID']
                or d.StudyInstanceUID != ct_meta['StudyInstanceUID']
                or d.FrameOfReferenceUID != first.FrameOfReferenceUID or d.Rows != 512 or d.Columns != 512
                or not np.allclose(d.ImageOrientationPatient, orientation, rtol=0, atol=1e-9)
                or not np.allclose(d.PixelSpacing, spacing, rtol=0, atol=1e-9)):
            raise ValueError('CT native identity or grid differs')
    step = np.diff(positions, axis=0)
    if not np.allclose(step, [0, 0, 2.5], rtol=0, atol=1e-6):
        raise ValueError('CT has gaps, duplicates, shear or unexpected slice spacing')
    shared = seg.SharedFunctionalGroupsSequence[0]
    if (seg.PatientID != first.PatientID or seg.StudyInstanceUID != first.StudyInstanceUID
            or seg.SeriesInstanceUID != seg_meta['SeriesInstanceUID'] or seg.FrameOfReferenceUID != first.FrameOfReferenceUID
            or seg.SegmentationType != 'BINARY' or len(seg.SegmentSequence) != 1
            or not np.allclose(shared.PlaneOrientationSequence[0].ImageOrientationPatient, orientation, rtol=0, atol=1e-9)
            or not np.allclose(shared.PixelMeasuresSequence[0].PixelSpacing, spacing, rtol=0, atol=1e-9)):
        raise ValueError('SEG native identity or grid differs')
    descriptor = seg.SegmentSequence[0]; code = descriptor.SegmentedPropertyTypeCodeSequence[0]
    if (descriptor.SegmentLabel != 'Mediastinal lymph node' or descriptor.SegmentAlgorithmType != 'MANUAL'
            or code.CodeValue != '62683002' or code.CodingSchemeDesignator != 'SCT'):
        raise ValueError('Source target identity or manual-annotation claim changed')
    by_sop = {str(d.SOPInstanceUID): i for i, d in enumerate(images)}
    if len(by_sop) != len(images):
        raise ValueError('Repeated CT SOP')
    declared = seg.ReferencedSeriesSequence
    if len(declared) != 1 or declared[0].SeriesInstanceUID != first.SeriesInstanceUID:
        raise ValueError('SEG reference series differs')
    declared_sops = {str(d.ReferencedSOPInstanceUID) for d in declared[0].ReferencedInstanceSequence}
    if not declared_sops <= set(by_sop):
        raise ValueError('SEG refers to unavailable source slices')
    raw = seg.pixel_array
    if raw.shape != (int(seg.NumberOfFrames), 512, 512) or set(np.unique(raw)) != {0, 1}:
        raise ValueError('Unexpected SEG dimensions or values')
    mask = np.zeros((len(images), 512, 512), dtype=np.uint8)
    frame_records = []
    used = set()
    for index, frame in enumerate(seg.PerFrameFunctionalGroupsSequence):
        if frame.SegmentIdentificationSequence[0].ReferencedSegmentNumber != descriptor.SegmentNumber:
            raise ValueError('Unexpected segment number')
        source = frame.DerivationImageSequence[0].SourceImageSequence
        if len(source) != 1:
            raise ValueError('Ambiguous per-frame source reference')
        sop = str(source[0].ReferencedSOPInstanceUID)
        if sop not in by_sop or sop in used:
            raise ValueError('Missing or repeated per-frame source')
        used.add(sop); target = by_sop[sop]
        comparison = coordinate_roundtrip_check(positions[target], frame.PlanePositionSequence[0].ImagePositionPatient)
        mask[target] = raw[index]
        frame_records.append({'seg_frame': index, 'ct_index': target, 'source_sop': sop,
            'ct_position_lps': positions[target].tolist(),
            'seg_position_lps': list(map(float, frame.PlanePositionSequence[0].ImagePositionPatient)), **comparison})
    if used != declared_sops:
        raise ValueError('Per-frame and declared source memberships differ')
    pixels = np.stack([d.pixel_array for d in images])
    slopes = np.asarray([float(d.RescaleSlope) for d in images]); intercepts = np.asarray([float(d.RescaleIntercept) for d in images])
    volume = pixels.astype(np.float64) * slopes[:, None, None] + intercepts[:, None, None]
    lab6, count6 = ndimage.label(mask, ndimage.generate_binary_structure(3, 1))
    lab26, count26 = ndimage.label(mask, ndimage.generate_binary_structure(3, 3))
    counts = np.bincount(lab26.ravel()); counts[0] = 0
    components = []
    for number in range(1, count26 + 1):
        points = np.argwhere(lab26 == number)
        components.append({'annotation_component': number, 'voxel_count': len(points),
            'bbox_zyx_inclusive': [points.min(0).tolist(), points.max(0).tolist()],
            'centroid_zyx': points.mean(0).tolist(), 'independent_node_identity_verified': False})
    positive = np.argwhere(mask); largest = int(np.argmax(counts))
    centre = np.rint(np.argwhere(lab26 == largest).mean(0)).astype(int)
    views = [(volume[centre[0]], mask[centre[0]], spacing[0] / spacing[1], 'Axial', int(centre[0])),
             (volume[:, centre[1], :], mask[:, centre[1], :], 2.5 / spacing[1], 'Coronal', int(centre[1])),
             (volume[:, :, centre[2]], mask[:, :, centre[2]], 2.5 / spacing[0], 'Sagittal', int(centre[2]))]
    # SEG coordinates differ by tiny recorded quantization. Draw direct native-coordinate contours.
    offset = np.asarray(frame_records[0]['seg_position_lps']) - np.asarray(frame_records[0]['ct_position_lps'])
    if any(not np.allclose(np.asarray(f['seg_position_lps']) - np.asarray(f['ct_position_lps']), offset,
                           rtol=0, atol=1e-9) for f in frame_records):
        raise ValueError('Variable SEG plane offsets need separate rendering review')
    output.mkdir(parents=True, exist_ok=True)
    figure_records = []
    for marked in (False, True):
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        for row, window in enumerate([(-1000, 400), (-160, 240)]):
            for ax, (plane, labels, aspect, name, index) in zip(axes[row], views):
                ax.imshow(plane, cmap='gray', vmin=window[0], vmax=window[1], aspect=aspect,
                          interpolation='nearest', origin='upper' if name == 'Axial' else 'lower')
                if marked and labels.any():
                    dx = offset[0] / spacing[1] if name != 'Sagittal' else offset[1] / spacing[0]
                    dy = offset[1] / spacing[0] if name == 'Axial' else offset[2] / 2.5
                    ax.contour(np.arange(labels.shape[1]) + dx, np.arange(labels.shape[0]) + dy,
                               labels, levels=[0.5], colors=['#f0b45d'], linewidths=0.8)
                ax.set_title(f'{name} native index {index}; window {window}', fontsize=10)
                ax.set_xticks([]); ax.set_yticks([])
        fig.suptitle('LNQ case_0571 | native CT 2.5 mm slice spacing\n'
                     + ('Original manual lymph-node annotation; no station or malignancy inferred' if marked else 'Unmarked CT; unlabelled tissue is not a negative nodal finding'), fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        name = 'case-0571-native-' + ('source-labels' if marked else 'unmarked') + '.png'
        fig.savefig(output / name, dpi=150); plt.close(fig)
        figure_records.append({'file': name, 'sha256': hashlib.sha256((output / name).read_bytes()).hexdigest(),
            'annotation_overlaid': marked, 'source_voxels_resampled': False})
    derived = root / 'lnq-case-0571-derived'; derived.mkdir(exist_ok=True)
    np.save(derived / 'source-annotation-on-ct-indices.npy', mask)
    report = {'case_id': 'case_0571', 'source_doi': '10.7937/QVAZ-JA09', 'data_license': 'CC BY 4.0',
        'source_annotation_scope': seg_meta['SeriesDescription'], 'ct_archive_sha256': ct_integrity['archive_sha256'],
        'seg_archive_sha256': seg_integrity['archive_sha256'], 'publisher_per_file_md5_verified': True,
        'ct_shape_zyx': list(mask.shape), 'ct_spacing_zyx_mm': [2.5, *spacing.tolist()],
        'ct_origin_lps': positions[0].tolist(), 'ct_iop': orientation,
        'seg_segment_label': str(descriptor.SegmentLabel), 'seg_property_code': str(code.CodeValue),
        'seg_algorithm_type': str(descriptor.SegmentAlgorithmType), 'seg_frame_count': len(frame_records),
        'matching_per_frame_source_sops': len(used), 'matching_declared_source_references': len(declared_sops),
        'max_position_difference_mm': max(f['max_difference_mm'] for f in frame_records),
        'position_comparison_modes': sorted({f['mode'] for f in frame_records}), 'frame_records': frame_records,
        'encoded_annotation_voxels': int(np.count_nonzero(raw)), 'placed_annotation_voxels': int(np.count_nonzero(mask)),
        'unencoded_ct_planes': len(images) - len(used),
        'unencoded_planes_mean': 'No source SEG frame encoded for this plane; not proof of absent lymph nodes or malignancy.',
        'connected_components_6': int(count6), 'connected_components_26': int(count26),
        'connected_components_are_individual_node_count': False, 'components': components,
        'ct_rescale_slopes': sorted(set(slopes.tolist())), 'ct_rescale_intercepts': sorted(set(intercepts.tolist())),
        'ct_rescale_types': sorted({str(getattr(d, 'RescaleType', 'not_reported')) for d in images}),
        'source_seg_values_changed': False, 'fitted_registration_applied': False,
        'reconstructed_mask_sha256': hashlib.sha256((derived / 'source-annotation-on-ct-indices.npy').read_bytes()).hexdigest(),
        'native_section_indices_zyx': centre.tolist(), 'figures': figure_records,
        'clinical_approval': False, 'stations_assigned': [], 'nodal_malignancy_confirmed': False,
        'clinical_requirement_scope_complete': False, 'runtime_bindings_added': False,
        'limitations': ['Fully Annotated is the source challenge scope, not every node, station or clinical requirement.',
                        '2.5 mm native slice spacing remains visible; no finer boundary resolution is manufactured.',
                        'Lung Non-Small primary diagnosis does not prove malignant involvement of every annotated node.',
                        'No nodal station inferred from coordinate centroid or connected component count.',
                        'Small coordinate differences are compatible with float32/six-decimal conversion, not fitted away.']}
    if report['encoded_annotation_voxels'] != report['placed_annotation_voxels']:
        raise ValueError('Annotation values were lost during referenced-plane placement')
    (output / 'case-0571-native-review.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Matched', len(frame_records), 'SEG/source planes; retained', len(positive), 'annotation voxels;', count26, 'components')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); review(a.source_root, a.output)
