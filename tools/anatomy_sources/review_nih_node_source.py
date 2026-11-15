#!/usr/bin/env python3
"""Verify converted CT/SEG against the original NIH manual NIfTI node labels."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.audit_tcia_series_archive import audit_archive
from tools.anatomy_sources.review_tcia_lung_case import read_series


def verify_original_grid_positions(positions, affine, source_plane_count):
    import numpy as np
    import nibabel as nib
    positions = np.asarray(positions, dtype=float)
    if positions.shape != (source_plane_count, 3) or source_plane_count < 2 or not np.isfinite(positions).all():
        raise ValueError('Incomplete or invalid original source positions')
    expected = nib.affines.apply_affine(affine, np.column_stack([
        np.zeros(source_plane_count), np.zeros(source_plane_count), np.arange(source_plane_count)]))
    expected[:, :2] *= -1
    errors = np.abs(positions - expected)
    if not np.isfinite(expected).all() or np.max(errors) > 1e-5:
        raise ValueError('Converted CT positions differ from the original label grid')
    return errors


def review(root, output):
    import numpy as np
    import nibabel as nib
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    series = json.loads((root / 'med-001-series.json').read_text())
    ct_meta = next(s for s in series if s['Modality'] == 'CT'); seg_meta = next(s for s in series if s['Modality'] == 'SEG')
    ct_path, seg_path = root / 'med-001-ct.zip', root / 'med-001-seg.zip'
    for m in (ct_meta, seg_meta):
        if m['PatientID'] != 'MED_LYMPH_001' or m['LicenseURI'] != 'http://creativecommons.org/licenses/by/3.0/':
            raise ValueError('Source identity or licence differs')
    ct_integrity = audit_archive(ct_path, ct_meta['ImageCount'], ct_meta['FileSize'])
    seg_integrity = audit_archive(seg_path, seg_meta['ImageCount'], seg_meta['FileSize'])
    image = nib.load(root / 'MED_LYMPH_001_mask.nii.gz'); labels = np.asanyarray(image.dataobj)
    q, qcode = image.get_qform(coded=True); s, scode = image.get_sform(coded=True)
    if not qcode or not scode or not np.array_equal(q, s) or not np.array_equal(image.affine, s):
        raise ValueError('Ambiguous original label coordinates')
    if labels.shape != (512, 512, 666) or set(np.unique(labels)) != {0, 1, 2, 3}:
        raise ValueError('Original label dimensions/identities differ')
    images = read_series(ct_path); images.sort(key=lambda d: float(d.ImagePositionPatient[2])); seg = read_series(seg_path)[0]
    first = images[0]; positions = np.asarray([d.ImagePositionPatient for d in images], float)
    spacing = np.asarray(first.PixelSpacing, float); by_sop = {str(d.SOPInstanceUID): i for i, d in enumerate(images)}
    if len(by_sop) != len(images): raise ValueError('Repeated CT source instance')
    for d in images:
        if (d.PatientID != 'MED_LYMPH_001' or d.SeriesInstanceUID != ct_meta['SeriesInstanceUID']
                or d.FrameOfReferenceUID != first.FrameOfReferenceUID or d.Rows != 512 or d.Columns != 512
                or not np.array_equal(np.asarray(d.ImageOrientationPatient, float), [1, 0, 0, 0, 1, 0])
                or not np.array_equal(np.asarray(d.PixelSpacing, float), spacing)):
            raise ValueError('Converted CT native identity/grid differs')
    # Test every source position against the original affine, rather than
    # treating tiny decimal serialization changes as physical slice gaps.
    source_position_errors = verify_original_grid_positions(positions, image.affine, labels.shape[2])
    ct_affine = np.array([[-spacing[1], 0, 0, -positions[0, 0]], [0, -spacing[0], 0, -positions[0, 1]],
                          [0, 0, 1, positions[0, 2]], [0, 0, 0, 1]], float)
    if not np.allclose(ct_affine, image.affine, atol=1e-5, rtol=0):
        raise ValueError('Original NIfTI and converted CT coordinates do not agree within recorded serialization tolerance')
    if (seg.PatientID != first.PatientID or seg.FrameOfReferenceUID != first.FrameOfReferenceUID
            or seg.SeriesInstanceUID != seg_meta['SeriesInstanceUID'] or seg.SegmentationType != 'BINARY'):
        raise ValueError('SEG identity/type differs')
    descriptors = {int(d.SegmentNumber): d for d in seg.SegmentSequence}
    if set(descriptors) != {1, 2, 3}: raise ValueError('Segment mapping differs')
    for descriptor in descriptors.values():
        code = descriptor.SegmentedPropertyTypeCodeSequence[0]
        if descriptor.SegmentAlgorithmType != 'MANUAL' or code.CodeValue != '62683002' or code.CodingSchemeDesignator != 'SCT':
            raise ValueError('Source segment tissue/manual annotation differs')
    shared = seg.SharedFunctionalGroupsSequence[0]
    seg_spacing = np.asarray(shared.PixelMeasuresSequence[0].PixelSpacing, float)
    if (not np.array_equal(np.asarray(shared.PlaneOrientationSequence[0].ImageOrientationPatient, float), [1, 0, 0, 0, 1, 0])
            or not np.array_equal(seg_spacing.astype(np.float32), spacing.astype(np.float32))):
        raise ValueError('SEG orientation or spacing differs')
    raw = seg.pixel_array; frames = []; seen = set(); totals = {k: 0 for k in descriptors}; errors = 0
    for index, frame in enumerate(seg.PerFrameFunctionalGroupsSequence):
        number = int(frame.SegmentIdentificationSequence[0].ReferencedSegmentNumber)
        src = frame.DerivationImageSequence[0].SourceImageSequence
        if len(src) != 1 or str(src[0].ReferencedSOPInstanceUID) not in by_sop: raise ValueError('Unresolved frame source')
        sop = str(src[0].ReferencedSOPInstanceUID); z = by_sop[sop]
        if (number, z) in seen: raise ValueError('Duplicate segment/source plane')
        seen.add((number, z)); pos = np.asarray(frame.PlanePositionSequence[0].ImagePositionPatient, float)
        difference = float(np.max(np.abs(pos - positions[z])))
        if difference > 1e-5: raise ValueError('SEG/source position offset requires separate reconciliation')
        expected = (labels[:, :, z] == number).T
        mismatch = int(np.count_nonzero(expected != raw[index])); errors += mismatch
        totals[number] += int(np.count_nonzero(raw[index]))
        frames.append({'seg_frame': index, 'source_ct_index': z, 'segment_number': number,
                       'source_sop': sop, 'max_position_difference_mm': difference, 'original_label_pixel_mismatches': mismatch})
    original_totals = {k: int(np.count_nonzero(labels == k)) for k in descriptors}
    if errors or totals != original_totals:
        raise ValueError('Not every original positive label voxel was retained exactly')
    declared = seg.ReferencedSeriesSequence
    if (len(declared) != 1 or declared[0].SeriesInstanceUID != first.SeriesInstanceUID
            or {str(d.ReferencedSOPInstanceUID) for d in declared[0].ReferencedInstanceSequence} != {f['source_sop'] for f in frames}):
        raise ValueError('Declared and per-frame source references differ')
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for number in descriptors:
        points = np.argwhere(labels == number); centre = np.rint(points.mean(0)).astype(int)
        i, j, k = map(int, centre)
        # Read original converted source pixels for each native plane; apply source rescale only.
        axial = images[k].pixel_array.astype(float) * float(images[k].RescaleSlope) + float(images[k].RescaleIntercept)
        coronal = np.stack([d.pixel_array[j, :].astype(float) * float(d.RescaleSlope) + float(d.RescaleIntercept) for d in images])
        sagittal = np.stack([d.pixel_array[:, i].astype(float) * float(d.RescaleSlope) + float(d.RescaleIntercept) for d in images])
        low = np.maximum(points.min(0) - 15, 0); high = np.minimum(points.max(0) + 16, labels.shape)
        views = [(axial[low[1]:high[1], low[0]:high[0]], (labels[low[0]:high[0], low[1]:high[1], k] == number).T, 'axial', 1),
                 (coronal[low[2]:high[2], low[0]:high[0]], (labels[low[0]:high[0], j, low[2]:high[2]] == number).T, 'coronal', 1 / spacing[1]),
                 (sagittal[low[2]:high[2], low[1]:high[1]], (labels[i, low[1]:high[1], low[2]:high[2]] == number).T, 'sagittal', 1 / spacing[0])]
        for marked in (False, True):
            fig, axes = plt.subplots(2, 3, figsize=(12, 8))
            for row, window in enumerate([(-1000, 400), (-160, 240)]):
                for ax, (pixels, selection, name, aspect) in zip(axes[row], views):
                    ax.imshow(pixels, cmap='gray', vmin=window[0], vmax=window[1], interpolation='nearest', aspect=aspect,
                              origin='upper' if name == 'axial' else 'lower')
                    if marked and selection.any():
                        ax.contour(np.arange(selection.shape[1]), np.arange(selection.shape[0]), selection,
                                   levels=[0.5], colors=['#ecb453'], linewidths=0.8)
                    ax.set_title(f'{name}; original label {number}; window {window}', fontsize=9)
                    ax.set_xticks([]); ax.set_yticks([])
            fig.suptitle(f'MED_LYMPH_001 | native label {number} | source index IJK {centre.tolist()}\n'
                         + ('Original manual selection; no centroid-index, station or malignancy assignment' if marked else 'Unmarked converted source CT; native 1 mm slice spacing'), fontsize=11)
            fig.tight_layout(rect=(0, 0, 1, 0.93))
            filename = f'label-{number:02d}-' + ('source-labels' if marked else 'unmarked') + '.png'
            fig.savefig(output / filename, dpi=150); plt.close(fig)
            records.append({'file': filename, 'sha256': hashlib.sha256((output / filename).read_bytes()).hexdigest(),
                            'label': number, 'marked': marked, 'source_resampling': False,
                            'source_indices_ijk': centre.tolist(), 'crop_start_ijk': low.tolist(),
                            'crop_stop_exclusive_ijk': high.tolist()})
    record = {'case_id': 'MED_LYMPH_001', 'source_doi': '10.7937/K9/TCIA.2015.AQIIDCNM', 'data_license': 'CC BY 3.0',
              'ct_archive_sha256': ct_integrity['archive_sha256'], 'seg_archive_sha256': seg_integrity['archive_sha256'],
              'original_mask_sha256': hashlib.sha256((root / 'MED_LYMPH_001_mask.nii.gz').read_bytes()).hexdigest(),
              'original_mask_shape_ijk': list(labels.shape), 'original_mask_affine_ras': image.affine.tolist(),
              'converted_ct_affine_ras': ct_affine.tolist(), 'max_original_mask_ct_affine_difference_mm': float(np.abs(ct_affine - image.affine).max()),
              'complete_ct_planes': len(images), 'native_slice_position_step_mm': 1.0, 'in_plane_pixel_spacing_mm': spacing.tolist(),
              'max_ct_position_difference_from_original_label_grid_mm': float(source_position_errors.max()),
              'observed_converted_ct_step_range_mm': [float(np.diff(positions[:, 2]).min()), float(np.diff(positions[:, 2]).max())],
              'original_acquisition_resolution_verified': False,
              'seg_declared_pixel_spacing_mm': seg_spacing.tolist(),
              'max_seg_ct_pixel_spacing_difference_mm': float(np.max(np.abs(seg_spacing-spacing))),
              'seg_spacing_equal_at_original_nifti_float32_precision': True,
              'max_seg_ct_frame_position_difference_mm': max(f['max_position_difference_mm'] for f in frames),
              'slice_thickness_tag_reported': all(hasattr(d, 'SliceThickness') for d in images),
              'original_label_voxel_counts': original_totals, 'seg_label_voxel_counts': totals, 'seg_frames': frames,
              'seg_to_original_label_pixel_mismatches': errors, 'source_labels_changed': False, 'source_ct_resampled': False,
              'clinical_approval': False, 'centroid_annotation_indices_matched': False, 'stations_assigned': [],
              'nodal_malignancy_confirmed': False, 'runtime_promoted': False, 'figures': records,
              'limits': ['CT DICOM files were converted from volumetric source images; scanner/protocol and calibrated intensity units require separate source review.',
                         '1 mm sampling is verified from every slice position; original acquisition thickness is not supplied by these converted tags.',
                         'Manual mask indices are not the separately released centroid annotation indices.',
                         'Original annotation extent, anatomical boundaries, individual-node identity and station/disease context remain unverified.']}
    (output / 'med-001-native-crossformat-review.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Matched all', sum(totals.values()), 'original positive mask voxels; source CT step 1 mm; label mismatches', errors)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); review(a.source_root, a.output)
