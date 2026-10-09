#!/usr/bin/env python3
"""Build a complete native-plane source-study viewer; no segmentations or diagnostic scoring."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import zipfile


def package(source, review, output):
    summary = json.loads((review / 'native-study-review.json').read_text())
    if summary['source_objects'] != 1359 or not summary['all_original_scalars_independently_decoded']:
        raise ValueError('Complete independently verified source study required')
    output.mkdir(parents=True, exist_ok=True)
    series = []; sample_count = 0
    for s in summary['series']:
        number = s['series_number']; record = json.loads((review / f'series-{number:04d}-review.json').read_text())
        frames = []; buffer = bytearray()
        with zipfile.ZipFile(source / f'series-{number:04d}.zip') as archive:
            for frame in record['frames']:
                original = archive.read(frame['member'])
                if hashlib.sha256(original).hexdigest() != frame['DICOM_sha256']:
                    raise ValueError('Original DICOM object changed')
                count = frame['pixel_samples'] * 2; pixels = original[frame['pixel_offset']:frame['pixel_offset'] + count]
                if hashlib.sha256(pixels).hexdigest() != frame['pixel_int16_le_sha256']:
                    raise ValueError('Original verified scalar span changed')
                tags = frame['source_tags']; wc = tags['WindowCenter']; ww = tags['WindowWidth']
                if isinstance(wc, list): wc = wc[0]
                if isinstance(ww, list): ww = ww[0]
                frames.append({'sop': frame['sop_instance_uid'], 'instance': frame['instance_number'],
                               'offset': len(buffer), 'rows': frame['rows'], 'columns': frame['columns'],
                               'spacing': frame['pixel_spacing'], 'orientation': frame['image_orientation_patient'],
                               'position': frame['image_position_patient'], 'window_center': float(wc), 'window_width': float(ww),
                               'temporal': str(tags['TemporalPositionIdentifier']) if tags['TemporalPositionIdentifier'] is not None else 'not supplied',
                               'acquisition_time': tags['AcquisitionTime'], 'trigger_time': tags['TriggerTime'],
                               'image_type': tags['ImageType'], 'source_pixel_int16_le_sha256': frame['pixel_int16_le_sha256']})
                buffer.extend(pixels)
        raw = bytes(buffer); compressed = gzip.compress(raw, mtime=0)
        if gzip.decompress(compressed) != raw:
            raise ValueError('Complete source scalar transport differs')
        filename = f'series-{number:04d}.bin.gz'
        (output / filename).write_bytes(compressed)
        sample_count += len(raw) // 2
        series.append({'number': number, 'description': s['source_description'], 'uid': s['series_instance_uid'],
                       'frames': frames, 'file': filename, 'decoded_bytes': len(raw),
                       'decoded_int16_le_sha256': hashlib.sha256(raw).hexdigest(),
                       'compressed_sha256': hashlib.sha256(compressed).hexdigest()})
    if sample_count != summary['source_pixel_samples']:
        raise ValueError('Complete study source sample accounting differs')
    data = {'source_frames': 1359, 'source_pixel_samples': sample_count, 'series': series}
    here = Path(__file__).parent
    script = (here / 'bladder_native_mri_viewer.js').read_bytes(); (output / 'mri-reference.js').write_bytes(script)
    template = (here / 'bladder_native_mri_template.html').read_text()
    text = template.replace('__DATASET_JSON__', json.dumps(data, separators=(',', ':')).replace('<', '\\u003c'))
    text = text.replace('__SCRIPT_URL__', './mri-reference.js')
    (output / 'mri-reference.html').write_text(text)
    proof = {'source_frames': 1359, 'source_series': len(series), 'source_pixel_samples': sample_count,
             'series_transport': [{k: s[k] for k in ['number', 'file', 'decoded_bytes', 'decoded_int16_le_sha256', 'compressed_sha256']} for s in series],
             'html_sha256': hashlib.sha256(text.encode()).hexdigest(), 'html_bytes': len(text.encode()),
             'script_sha256': hashlib.sha256(script).hexdigest(),
             'all_source_frames_and_scalars_retained': True, 'source_values_modified_interpolated_or_averaged': False,
             'native_surface_models_or_segmentations_invented': False, 'clinical_approval': False, 'runtime_promoted': False}
    (output / 'transport-review.json').write_text(json.dumps(proof, indent=2) + '\n')
    print('Complete viewer:', len(series), 'series;', proof['source_pixel_samples'], 'int16 samples;', proof['html_bytes'], 'HTML bytes')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--review', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); package(args.source, args.review, args.output)
