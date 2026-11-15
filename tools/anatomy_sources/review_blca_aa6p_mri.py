#!/usr/bin/env python3
"""Verify every original MRI scalar and source grid without inferring histology or registration."""
import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile

from tools.anatomy_sources.acquire_blca_aa6p_mri import CASE, STUDY


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def explicit_vr_pixel_bytes(raw):
    """Independently walk the uncompressed explicit-VR little-endian container.

    This reader never searches for a byte pattern that might occur in a value.
    Metadata sequences are walked by their item and delimiter grammar.
    """
    if raw[128:132] != b'DICM':
        raise ValueError('DICOM preamble missing')
    long_vr = {b'OB', b'OD', b'OF', b'OL', b'OV', b'OW', b'SQ', b'UC', b'UN', b'UR', b'UT'}
    def element_header(cursor):
        if cursor + 8 > len(raw): raise ValueError('Truncated explicit-VR header')
        group, element = struct.unpack_from('<HH', raw, cursor)
        vr = raw[cursor + 4:cursor + 6]
        if not (len(vr) == 2 and vr.isalpha() and vr.isupper()):
            raise ValueError('Unsupported non-explicit VR container')
        if vr in long_vr:
            if cursor + 12 > len(raw) or raw[cursor + 6:cursor + 8] != b'\0\0':
                raise ValueError('Invalid long-VR header')
            length = struct.unpack_from('<I', raw, cursor + 8)[0]
            start = cursor + 12
        else:
            length = struct.unpack_from('<H', raw, cursor + 6)[0]
            start = cursor + 8
        if length != 0xffffffff and start + length > len(raw):
            raise ValueError('Truncated source element')
        return (group, element), vr, length, start
    def skip_sequence(cursor, depth):
        if depth > 32: raise ValueError('Excessive metadata sequence nesting')
        while cursor + 8 <= len(raw):
            group, tag, length = struct.unpack_from('<HHI', raw, cursor)
            if group != 0xfffe: raise ValueError('Sequence content is not an item')
            cursor += 8
            if tag == 0xe0dd:
                if length != 0: raise ValueError('Invalid sequence delimiter length')
                return cursor
            if tag != 0xe000: raise ValueError('Unexpected metadata item delimiter')
            if length != 0xffffffff:
                if cursor + length > len(raw): raise ValueError('Truncated metadata item')
                cursor += length
                continue
            while cursor + 8 <= len(raw):
                group, tag, length = struct.unpack_from('<HHI', raw, cursor)
                if (group, tag) == (0xfffe, 0xe00d):
                    if length != 0: raise ValueError('Invalid item delimiter length')
                    cursor += 8
                    break
                _, vr, length, start = element_header(cursor)
                if length == 0xffffffff:
                    if vr != b'SQ': raise ValueError('Unsupported undefined non-sequence value')
                    cursor = skip_sequence(start, depth + 1)
                else: cursor = start + length
            else: raise ValueError('Unterminated metadata item')
        raise ValueError('Unterminated metadata sequence')
    cursor = 132
    while cursor < len(raw):
        tag, vr, length, start = element_header(cursor)
        if tag == (0x7fe0, 0x0010):
            if length == 0xffffffff: raise ValueError('Encapsulated pixels are not native uncompressed scalars')
            return raw[start:start + length], start
        if length == 0xffffffff:
            if vr != b'SQ': raise ValueError('Unsupported undefined non-sequence value')
            cursor = skip_sequence(start, 0)
        else: cursor = start + length
    raise ValueError('Native pixel element missing')


def primitive(value):
    if value is None: return None
    if isinstance(value, (str, int, float)): return value
    try: return [primitive(v) for v in value]
    except TypeError: return str(value)


def review(source, output):
    import numpy as np
    import pydicom
    output.mkdir(parents=True, exist_ok=True)
    receipt = json.loads((source / 'acquisition-review.json').read_text())
    if receipt['source_objects'] != 1359 or receipt['case_id'] != CASE or receipt['study_instance_uid'] != STUDY:
        raise ValueError('Complete original study identity differs')
    series_rows = []
    all_sops = set()
    selected_tags = ['PatientAge', 'PatientSex', 'BodyPartExamined', 'ImageType', 'SeriesDescription',
                     'AcquisitionNumber', 'AcquisitionTime', 'ContentTime', 'TemporalPositionIdentifier',
                     'NumberOfTemporalPositions', 'TriggerTime', 'TemporalResolution', 'DiffusionBValue',
                     'AcquisitionMatrix', 'RepetitionTime', 'EchoTime', 'EchoNumbers', 'InversionTime',
                     'MagneticFieldStrength', 'SequenceName', 'ScanningSequence', 'SequenceVariant',
                     'MRAcquisitionType', 'SliceThickness', 'SpacingBetweenSlices', 'ContrastBolusAgent',
                     'ContrastBolusStartTime', 'ContrastBolusTotalDose', 'RescaleSlope', 'RescaleIntercept',
                     'WindowCenter', 'WindowWidth', 'PixelPaddingValue', 'PixelPaddingRangeLimit',
                     'RealWorldValueMappingSequence']
    for receipt_name in receipt['series_receipts']:
        proof = json.loads((source / receipt_name).read_text())
        selection = proof['source_series']
        number = int(selection['SeriesNumber'])
        path = source / f'series-{number:04d}.zip'
        if sha(path.read_bytes()) != proof['archive_sha256']:
            raise ValueError('Audited archive changed')
        frames = []
        with zipfile.ZipFile(path) as archive:
            for record in proof['members']:
                raw = archive.read(record['member'])
                if sha(raw) != record['sha256']:
                    raise ValueError('Original DICOM object changed')
                data = pydicom.dcmread(io.BytesIO(raw))
                if str(data.PatientID) != CASE or str(data.StudyInstanceUID) != STUDY or str(data.SeriesInstanceUID) != selection['SeriesInstanceUID']:
                    raise ValueError('Actual DICOM identity differs from catalogue')
                if str(data.file_meta.TransferSyntaxUID) != '1.2.840.10008.1.2.1':
                    raise ValueError('Independent reader is limited to actual uncompressed explicit-VR LE')
                if (int(data.BitsAllocated), int(data.BitsStored), int(data.HighBit), int(data.PixelRepresentation), int(data.SamplesPerPixel)) != (16, 16, 15, 1, 1):
                    raise ValueError('Source integer representation needs a separate decoder')
                pixels, offset = explicit_vr_pixel_bytes(raw)
                shape = (int(data.Rows), int(data.Columns))
                if len(pixels) != shape[0] * shape[1] * 2:
                    raise ValueError('Original pixel byte extent changed')
                own = np.frombuffer(pixels, dtype='<i2').reshape(shape)
                reference = data.pixel_array
                if reference.dtype.kind != 'i' or not np.array_equal(own, reference) or reference.astype('<i2').tobytes() != pixels:
                    raise ValueError('Independent integer scalar decoding differs')
                sop = str(data.SOPInstanceUID)
                if sop in all_sops: raise ValueError('Duplicate original SOP identity')
                all_sops.add(sop)
                row = {'sop_instance_uid': sop, 'instance_number': int(data.InstanceNumber),
                       'member': record['member'], 'DICOM_sha256': record['sha256'],
                       'rows': shape[0], 'columns': shape[1], 'pixel_offset': offset,
                       'pixel_int16_le_sha256': sha(pixels), 'pixel_samples': own.size,
                       'raw_int16_min_max': [int(own.min()), int(own.max())],
                       'image_orientation_patient': [float(v) for v in data.ImageOrientationPatient],
                       'image_position_patient': [float(v) for v in data.ImagePositionPatient],
                       'pixel_spacing': [float(v) for v in data.PixelSpacing],
                       'frame_of_reference_uid': str(data.FrameOfReferenceUID),
                       'source_tags': {key: primitive(data.get(key)) for key in selected_tags}}
                frames.append(row)
        frames.sort(key=lambda f: (f['instance_number'], f['sop_instance_uid']))
        partitions = defaultdict(list)
        for frame in frames:
            key = (tuple(frame['image_orientation_patient']), tuple(frame['pixel_spacing']),
                   frame['rows'], frame['columns'], frame['frame_of_reference_uid'],
                   str(frame['source_tags']['TemporalPositionIdentifier']))
            partitions[key].append(frame)
        grids = []
        for key, group in partitions.items():
            orientation = np.asarray(key[0], dtype=float)
            normal = np.cross(orientation[:3], orientation[3:])
            direction_measures = [float(np.linalg.norm(orientation[:3])), float(np.linalg.norm(orientation[3:])),
                                  float(np.dot(orientation[:3], orientation[3:])), float(np.linalg.norm(normal))]
            if not np.isfinite(orientation).all() or min(direction_measures[0], direction_measures[1], direction_measures[3]) <= 0:
                raise ValueError('Nonfinite or degenerate original source directions')
            # Record rounded/nonorthogonal declarations without fitting them to
            # an ideal frame. Only the mathematical plane normal used for
            # distance projection is unit length; source directions stay exact.
            unit_normal = normal / direction_measures[3]
            positions = defaultdict(list)
            for frame in group: positions[tuple(frame['image_position_patient'])].append(frame)
            multiplicities = {len(v) for v in positions.values()}
            if len(multiplicities) != 1:
                raise ValueError('Irregular repeated source positions require explicit review')
            repeats = next(iter(multiplicities))
            ordered_positions = sorted(positions, key=lambda p: float(np.asarray(p) @ normal))
            for rank in range(repeats):
                ordered = [sorted(positions[pos], key=lambda f: f['instance_number'])[rank] for pos in ordered_positions]
                xyz = np.asarray([f['image_position_patient'] for f in ordered])
                step = np.diff(xyz, axis=0)
                distances = step @ unit_normal
                grids.append({'orientation': list(key[0]), 'pixel_spacing': list(key[1]),
                              'declared_row_column_norm_dot_and_cross_norm': direction_measures,
                              'source_direction_cosines_orthogonalized_or_repaired': False,
                              'rows': key[2], 'columns': key[3], 'source_frame_of_reference_uid': key[4],
                              'source_temporal_position_identifier': key[5], 'duplicate_plane_rank': rank + 1,
                              'duplicate_plane_rank_is_verified_acquisition_or_bvalue_identity': False,
                              'planes': len(ordered), 'ordered_sop_uids': [f['sop_instance_uid'] for f in ordered],
                              'source_positions_lps_mm': xyz.tolist(),
                              'observed_interplane_mm_min_max': [float(distances.min()), float(distances.max())] if len(distances) else None,
                              'source_stack_displacement_vectors_mm': step.tolist(),
                              'source_values_repaired_interpolated_averaged_or_dropped': False})
        if sum(g['planes'] for g in grids) != len(frames):
            raise ValueError('Some original frames were lost during grid accounting')
        row = {'series_number': number, 'series_instance_uid': selection['SeriesInstanceUID'],
               'source_description': selection['SeriesDescription'], 'archive_sha256': proof['archive_sha256'],
               'original_frame_count': len(frames), 'pixel_samples': sum(f['pixel_samples'] for f in frames),
               'independent_all_int16_scalar_decoding_verified': True, 'source_grids': grids, 'frames': frames}
        (output / f'series-{number:04d}-review.json').write_text(json.dumps(row, indent=2) + '\n')
        series_rows.append({key: value for key, value in row.items() if key != 'frames'})
        print(number, selection['SeriesDescription'], len(frames), 'frames;', len(grids), 'source grids', flush=True)
    summary = {'case_id': CASE, 'study_instance_uid': STUDY, 'source_series': len(series_rows),
               'source_objects': len(all_sops), 'source_pixel_samples': sum(r['pixel_samples'] for r in series_rows),
               'series': series_rows, 'all_original_scalars_independently_decoded': True,
               'source_sampling_equals_effective_anatomical_resolution': False,
               'same_declared_frame_proves_anatomical_timepoint_registration': False,
               'duplicate_diffusion_plane_identity_verified': False,
               'ADC_physical_units_verified_from_real_world_mapping': False,
               'contrast_bolus_absolute_start_time_verified': False,
               'VI_RADS_or_histological_stage_independently_assigned': False,
               'complete_reported_structure_geometry_verified': False,
               'original_source_values_changed': False, 'clinical_approval': False, 'runtime_promoted': False}
    (output / 'native-study-review.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    review(args.source, args.output)
