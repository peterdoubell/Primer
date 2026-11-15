#!/usr/bin/env python3
"""Review original MRI echo partitions and native planes without resampling or masks."""
import argparse
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path
import zipfile
import textwrap


def partition_echoes(records):
    """Keep each echo separate and reject repeated planes within an echo."""
    import numpy as np
    groups = defaultdict(list)
    for record in records:
        groups[(record['echo_number'], record['echo_time_ms'])].append(record)
    result = []
    for (echo, te), rows in sorted(groups.items()):
        first = rows[0]
        orientation = np.asarray(first['orientation_lps'], float)
        column, row = orientation[:3], orientation[3:]
        if not np.allclose([np.linalg.norm(column), np.linalg.norm(row), np.dot(column, row)], [1, 1, 0], atol=1e-6, rtol=0):
            raise ValueError('Nonorthonormal source directions')
        normal = np.cross(column, row)
        for item in rows:
            for key in ('rows', 'columns', 'pixel_spacing_mm', 'orientation_lps', 'frame_of_reference_uid'):
                if item[key] != first[key]:
                    raise ValueError('Geometry differs within source echo')
        positions = [tuple(item['position_lps_mm']) for item in rows]
        if len(set(positions)) != len(positions):
            raise ValueError('Repeated source plane within one echo')
        rows.sort(key=lambda item: float(np.dot(item['position_lps_mm'], normal)))
        xyz = np.asarray([item['position_lps_mm'] for item in rows], float)
        offsets = xyz @ normal
        steps = np.diff(offsets)
        residual = np.diff(xyz, axis=0) - steps[:, None] * normal
        result.append({'echo_number': echo, 'echo_time_ms': te, 'records': rows,
                       'normal_lps': normal.tolist(), 'source_plane_offsets_mm': offsets.tolist(),
                       'source_interplane_spacings_mm': steps.tolist(),
                       'maximum_inplane_step_mm': float(np.max(np.linalg.norm(residual, axis=1))) if len(residual) else 0,
                       'uniform_interplane_spacing': bool(len(steps) > 0 and np.allclose(steps, steps[0], atol=1e-5, rtol=0)),
                       'source_slice_thicknesses_mm': sorted({item['slice_thickness_mm'] for item in rows}),
                       'single_thick_slab_is_volume': False})
    return result


def pair_echo_planes(a, b):
    """Exact declared physical geometry correspondence; no alignment fitting."""
    def key(item):
        return tuple(item['position_lps_mm'])
    left = {key(item): item for item in a['records']}
    right = {key(item): item for item in b['records']}
    if left.keys() != right.keys():
        raise ValueError('Echo plane sets differ')
    pairs = []
    for item in a['records']:
        other = right[key(item)]
        for field in ('orientation_lps', 'pixel_spacing_mm', 'rows', 'columns', 'frame_of_reference_uid', 'slice_thickness_mm'):
            if item[field] != other[field]:
                raise ValueError('Echo plane geometry differs')
        pairs.append((item, other))
    return pairs


def review(root, output):
    import numpy as np
    import pydicom
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    receipt = json.loads((root / 'dicoms.zip.acquisition.json').read_text())
    publisher = json.loads((root / 'record.json').read_text())
    expected = next(item for item in publisher['files'] if item['key'] == 'dicoms.zip')
    metadata = {}; pixels = {}; series = defaultdict(list)
    with (root / 'dicoms.zip').open('rb') as source:
        md5 = hashlib.md5(); sha = hashlib.sha256()
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            md5.update(chunk); sha.update(chunk)
        if not receipt['publisher_md5_verified'] or 'md5:' + md5.hexdigest() != expected['checksum'] or sha.hexdigest() != receipt['sha256']:
            raise ValueError('Original DICOM archive changed')
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            for name in archive.namelist():
                if 'TCGA-BC-A3KG' not in name or not name.endswith('.dcm') or name.startswith('__MACOSX/'):
                    continue
                data = archive.read(name); d = pydicom.dcmread(io.BytesIO(data))
                number = int(d.SeriesNumber)
                if number not in (2, 3, 4, 6, 11):
                    continue
                item = {'source_member': name, 'source_member_sha256': hashlib.sha256(data).hexdigest(), 'crc_verified': True,
                        'sop_instance_uid': str(d.SOPInstanceUID), 'series_instance_uid': str(d.SeriesInstanceUID),
                        'frame_of_reference_uid': str(d.FrameOfReferenceUID), 'series_number': number,
                        'echo_number': int(d.EchoNumbers), 'echo_time_ms': float(d.EchoTime),
                        'repetition_time_ms': float(d.RepetitionTime), 'magnetic_field_strength_t': float(d.MagneticFieldStrength),
                        'orientation_lps': list(map(float, d.ImageOrientationPatient)), 'position_lps_mm': list(map(float, d.ImagePositionPatient)),
                        'pixel_spacing_mm': list(map(float, d.PixelSpacing)), 'rows': int(d.Rows), 'columns': int(d.Columns),
                        'slice_thickness_mm': float(d.SliceThickness), 'declared_spacing_between_slices_mm': float(d.SpacingBetweenSlices) if hasattr(d, 'SpacingBetweenSlices') else None,
                        'source_description': str(d.SeriesDescription), 'source_sequence_name': str(d.SequenceName),
                        'scanning_sequence': str(d.ScanningSequence), 'scan_options': str(d.ScanOptions),
                        'source_acquisition_time': str(d.AcquisitionTime), 'source_acquisition_number': int(d.AcquisitionNumber)}
                metadata[name] = item; series[number].append(item)
                pixels[name] = d.pixel_array.astype(float) * float(getattr(d, 'RescaleSlope', 1)) + float(getattr(d, 'RescaleIntercept', 0))
    partitions = {number: partition_echoes(rows) for number, rows in sorted(series.items())}
    if set(partitions) != {2, 3, 4, 6, 11} or len(partitions[3]) != 2:
        raise ValueError('Expected source series/echo set changed')
    paired = pair_echo_planes(*partitions[3])
    repeat_pairs = pair_echo_planes(partitions[2][0], partitions[11][0])
    repeat_review = {'series_numbers': [2, 11], 'exact_geometry_paired_planes': len(repeat_pairs),
                     'pixel_identical_planes': sum(np.array_equal(pixels[a['source_member']], pixels[b['source_member']]) for a, b in repeat_pairs),
                     'source_descriptions': [series[n][0]['source_description'] for n in (2, 11)],
                     'source_scanning_sequences': [series[n][0]['scanning_sequence'] for n in (2, 11)],
                     'source_echo_times_ms': [series[n][0]['echo_time_ms'] for n in (2, 11)],
                     'description_conflict_resolved': False, 'series_11_granted_t1_coverage': False}
    output.mkdir(parents=True, exist_ok=True)
    figures = []
    def draw(name, grid, title):
        fig, axes = plt.subplots(len(grid), len(grid[0]), figsize=(max(10, 5 * len(grid[0])), max(6.4, 4.8 * len(grid))), squeeze=False)
        display_rows = []
        for row_axes, items in zip(axes, grid):
            # A shared numeric window within each paired-echo row is only a display aid.
            window = np.percentile(np.concatenate([pixels[item['source_member']].ravel() for item in items]), [2, 98])
            for ax, item in zip(row_axes, items):
                image = pixels[item['source_member']]; sy, sx = item['pixel_spacing_mm']
                ax.imshow(image, cmap='gray', interpolation='nearest', vmin=window[0], vmax=window[1], origin='upper',
                          extent=(-sx/2, (item['columns']-.5)*sx, (item['rows']-.5)*sy, -sy/2), aspect='equal')
                pos = ', '.join(f'{v:.2f}' for v in item['position_lps_mm'])
                ax.set_title(f"Series {item['series_number']} | echo {item['echo_number']} | TE {item['echo_time_ms']:g} ms\n"
                             f"IPP LPS ({pos}) mm | thickness {item['slice_thickness_mm']:g} mm", fontsize=9)
                ax.set_xlabel('Source column distance (mm)', fontsize=8); ax.set_ylabel('Source row distance (mm)', fontsize=8)
                display_rows.append({'source_member': item['source_member'], 'sop_instance_uid': item['sop_instance_uid'],
                                     'window_percentiles_2_98': window.tolist()})
        heading = 'TCGA-BC-A3KG | ' + title
        if len(grid[0]) == 1:
            heading = '\n'.join(textwrap.wrap(heading, width=90))
        fig.suptitle(heading + '\nNative acquired planes; source index directions retained; no mask overlay or clinical approval', fontsize=11)
        fig.tight_layout(rect=(0, 0, 1, .94)); path = output / (name + '.png'); fig.savefig(path, dpi=140); plt.close(fig)
        figures.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'display_planes': display_rows,
                        'resampled': False, 'display_orientation': 'Original DICOM column/row directions; no inferred anatomical reformat'})
    selected = [7, 15, 22]
    draw('paired-echo-native', [[*paired[i]] for i in selected], 'Paired original echoes (source names describe opposed/in phase)')
    draw('spin-echo-native', [[partitions[n][0]['records'][i] for n in (2, 4, 11)] for i in selected],
         'Original spin-echo planes | series 11 description conflicts with sequence parameters')
    draw('thick-slab-native', [[partitions[6][0]['records'][0]]], 'Single original 50 mm thick slab; no fine-volume claim')
    result = {'case_id': 'TCGA-BC-A3KG', 'source_doi': '10.5281/zenodo.8179129', 'source_archive_sha256': receipt['sha256'],
              'publisher_archive_md5_verified': True, 'series_echo_partitions': partitions,
              'paired_echo_exact_geometry_planes': len(paired), 'source_series_2_11_comparison': repeat_review,
              'figures': figures, 'source_values_changed': False, 'source_echoes_interleaved': False,
              'arterial_masks_transferred': False, 'registered_derivatives_used': False, 'clinical_approval': False, 'runtime_promoted': False,
              'limits': ['Matching echo geometry does not prove motion-free anatomical correspondence or quantitative fat fraction.',
                         'Source slice thickness and interplane spacing remain distinct; interslice gaps cannot be filled as acquired anatomy.',
                         'Description conflicts require review; series 11 is not credited as T1 from its name.',
                         'No DWI/ADC, hepatobiliary timing, phase adequacy, diagnostic finding or complete anatomical boundary is approved.']}
    (output / 'sequence-review.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Reviewed', len(metadata), 'source planes;', len(paired), 'exact declared echo pairs; repeated-series pixel-identical planes:', repeat_review['pixel_identical_planes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); review(args.source_root, args.output)
