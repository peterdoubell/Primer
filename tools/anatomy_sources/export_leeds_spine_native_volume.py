#!/usr/bin/env python3
"""Export an audited original CT to a native, unresampled research array.

Requires NumPy and pydicom. Does not segment tissues, assign anatomical labels,
or promote an array to the application. Incomplete output is never finalized.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pydicom

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.native_dicom_geometry import validate_geometry
from tools.anatomy_sources.dicom_ct_units import resolve_ct_units


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(8*1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text())
    require(audit['archive']['all_member_crcs_valid'] is True, "Source integrity condition failed: audit['archive']['all_member_crcs_valid'] is True")
    require(args.archive.stat().st_size == audit['archive']['bytes'], "Source integrity condition failed: args.archive.stat().st_size == audit['archive']['bytes']")
    require(sha256(args.archive) == audit['archive']['sha256'], 'Audited archive changed')
    geometry = validate_geometry(audit['frames'])
    frames = [audit['frames'][i] for i in geometry['source_frame_order']]
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output/'native-int16.npy'
    temporary = args.output/'native-int16.partial.npy'
    if target.exists() or temporary.exists():
        raise ValueError('Output already exists; inspect the previous export before proceeding')
    frame_records = []
    with zipfile.ZipFile(args.archive) as archive:
        members = [i for i in archive.infolist() if not i.is_dir()]
        require(len(members) == len(frames), 'Source integrity condition failed: len(members) == len(frames)')
        require({i.filename for i in members} == {f['member'] for f in frames}, 'Frame audit omits source files')
        array = np.lib.format.open_memmap(temporary, mode='w+', dtype='<i2', shape=tuple(geometry['shape']))
        for index, frame in enumerate(frames):
            # Reading the complete member also verifies its ZIP CRC.
            raw = archive.read(frame['member'])
            ds = pydicom.dcmread(io.BytesIO(raw))
            image_type = [str(v) for v in getattr(ds,'ImageType',[])]
            multi_energy = getattr(ds,'MultiEnergyCTAcquisition',None)
            units = resolve_ct_units(str(ds.SOPClassUID), image_type,
                                     getattr(ds,'RescaleType',None), multi_energy)
            require(str(ds.SOPClassUID) == frame['sop_class_uid'] and image_type == frame['image_type']
                    and multi_energy == frame['multi_energy_ct'] and units == frame['rescale_units'],
                    'Audited intensity-unit context differs from DICOM')
            require([float(v) for v in ds.ImagePositionPatient] == frame['position_mm'], 'Audited position differs from DICOM')
            require([float(v) for v in ds.ImageOrientationPatient] == frame['orientation'], 'Audited orientation differs from DICOM')
            require([float(v) for v in ds.PixelSpacing] == frame['pixel_spacing_mm'], 'Audited pixel spacing differs from DICOM')
            require(float(ds.RescaleSlope) == frame['rescale_slope'] and float(ds.RescaleIntercept) == frame['rescale_intercept'], 'Audited calibration differs from DICOM')
            require(str(getattr(ds, 'RescaleType', 'not_reported')) == frame['rescale_type'], "Source integrity condition failed: str(getattr(ds, 'RescaleType', 'not_reported')) == frame['rescale_type']")
            require(str(ds.file_meta.TransferSyntaxUID) in {'1.2.840.10008.1.2', '1.2.840.10008.1.2.1'}, "Source integrity condition failed: str(ds.file_meta.TransferSyntaxUID) in {'1.2.840.10008.1.2', '1.2.840.10008.1.2.1'}")
            require(ds.PixelRepresentation == 1 and ds.BitsAllocated == ds.BitsStored == 16, 'Source integrity condition failed: ds.PixelRepresentation == 1 and ds.BitsAllocated == ds.BitsStored == 16')
            pixels = ds.pixel_array
            independent = np.frombuffer(ds.PixelData, dtype='<i2').reshape(ds.Rows, ds.Columns)
            require(np.array_equal(pixels, independent), 'Source integrity condition failed: np.array_equal(pixels, independent)')
            array[index] = independent
            require(np.array_equal(array[index], independent), 'Native voxel copy changed')
            frame_records.append(dict(member=frame['member'], raw_pixel_sha256=hashlib.sha256(ds.PixelData).hexdigest(),
                                      rescale_slope=frame['rescale_slope'],rescale_intercept=frame['rescale_intercept'],
                                      rescale_type=frame['rescale_type'],rescale_units=units))
            if (index+1)%128 == 0:
                print(f'Preserved {index+1}/{len(frames)} native planes', flush=True)
        array.flush()
        del array
    reopened = np.load(temporary, mmap_mode='r', allow_pickle=False)
    for index, record in enumerate(frame_records):
        require(hashlib.sha256(reopened[index].tobytes()).hexdigest() == record['raw_pixel_sha256'], "Source integrity condition failed: hashlib.sha256(reopened[index].tobytes()).hexdigest() == record['raw_pixel_sha256']")
    del reopened
    digest = sha256(temporary)
    temporary.replace(target)
    manifest = dict(source_doi=audit['source_doi'], source_archive_sha256=audit['archive']['sha256'],
                    source_audit_sha256=sha256(args.audit), array_file=target.name, array_sha256=digest,
                    geometry=geometry, stored_values='Original signed 16-bit samples; no intensity rescaling applied',
                    frame_records=frame_records, clinical_approval=False, runtime_promoted=False)
    (args.output/'native-volume.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('Native array preserved and independently reloaded: '+digest, flush=True)


if __name__ == '__main__':
    main()
