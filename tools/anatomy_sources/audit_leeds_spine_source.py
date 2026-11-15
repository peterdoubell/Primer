#!/usr/bin/env python3
"""Audit original Leeds spine DICOM sampling without inventing anatomy.

Dependencies: pydicom, numpy, Pillow. Raw identifiers are not serialized. The
public README supplies donor context separately from the measured image grid.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pydicom
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.anatomy_sources.dicom_ct_units import resolve_ct_units

SOURCES = {
    3: dict(bytes=1252310016, md5='f114c0c0b541506be5d2cf2ae954148c', doi='10.5518/1923', url='https://archive.researchdata.leeds.ac.uk/1618/'),
    1: dict(bytes=13325473922, md5='bdf6b02ec6d6965f0f13a6f735769efc', doi='10.5518/1921', url='https://archive.researchdata.leeds.ac.uk/1620/'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--donor', type=int, choices=(1,3), default=3)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source_info = SOURCES[args.donor]
    require(args.archive.stat().st_size == source_info['bytes'], 'Archive incomplete or changed')
    md5, sha = hashlib.md5(), hashlib.sha256()
    with args.archive.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            md5.update(block); sha.update(block)
    require(md5.hexdigest() == source_info['md5'], 'Repository Content-MD5 mismatch')
    frames = []
    with zipfile.ZipFile(args.archive) as archive:
        require(archive.testzip() is None, 'Member CRC mismatch')
        for member in archive.infolist():
            if member.is_dir():
                continue
            with archive.open(member) as source:
                ds = pydicom.dcmread(source, stop_before_pixels=True)
            require(ds.Modality == 'CT', "Source integrity condition failed: ds.Modality == 'CT'")
            image_type = [str(v) for v in getattr(ds,'ImageType',[])]
            multi_energy = getattr(ds,'MultiEnergyCTAcquisition',None)
            units = resolve_ct_units(str(ds.SOPClassUID), image_type,
                                     getattr(ds,'RescaleType',None), multi_energy)
            frames.append(dict(
                member=member.filename, bytes=member.file_size, crc32=f'{member.CRC:08x}',
                rows=int(ds.Rows), columns=int(ds.Columns), instance=int(ds.InstanceNumber),
                position_mm=[float(v) for v in ds.ImagePositionPatient],
                orientation=[float(v) for v in ds.ImageOrientationPatient],
                pixel_spacing_mm=[float(v) for v in ds.PixelSpacing],
                slice_thickness_mm=float(ds.SliceThickness),
                rescale_slope=float(ds.RescaleSlope),rescale_intercept=float(ds.RescaleIntercept),
                rescale_type=str(getattr(ds,'RescaleType','not_reported')),
                sop_class_uid=str(ds.SOPClassUID), image_type=image_type,
                multi_energy_ct=multi_energy, rescale_units=units,
                patient_position=str(getattr(ds,'PatientPosition','not_reported')),
                series_sha256=hashlib.sha256(str(ds.SeriesInstanceUID).encode()).hexdigest(),
                frame_uid_sha256=hashlib.sha256(str(ds.SOPInstanceUID).encode()).hexdigest()))
        first = frames[0]
        normal = np.cross(first['orientation'][:3],first['orientation'][3:])
        require(np.isclose(np.linalg.norm(normal), 1), 'Source integrity condition failed: np.isclose(np.linalg.norm(normal), 1)')
        require(all((np.allclose(f['orientation'], first['orientation']) for f in frames)), "Source integrity condition failed: all((np.allclose(f['orientation'], first['orientation']) for f in frames))")
        require(all((f['pixel_spacing_mm'] == first['pixel_spacing_mm'] and (f['rows'], f['columns']) == (first['rows'], first['columns']) for f in frames)), "Source integrity condition failed: all((f['pixel_spacing_mm'] == first['pixel_spacing_mm'] and (f['rows'], f['columns']) == (first['rows'], first['columns']) for f in frames))")
        require(len({f['series_sha256'] for f in frames}) == 1, "Source integrity condition failed: len({f['series_sha256'] for f in frames}) == 1")
        require(len({f['frame_uid_sha256'] for f in frames}) == len(frames), "Source integrity condition failed: len({f['frame_uid_sha256'] for f in frames}) == len(frames)")
        frames.sort(key=lambda f: float(np.dot(f['position_mm'],normal)))
        positions = np.array([f['position_mm'] for f in frames])
        steps = np.diff(positions @ normal)
        require(np.all(steps > 0), 'Source integrity condition failed: np.all(steps > 0)')
        regular = bool(np.allclose(steps,steps[0],rtol=0,atol=1e-5))
        residual = positions-positions[0] - ((positions-positions[0])@normal)[:,None]*normal
        samples=[]
        for index in [0,len(frames)//2,len(frames)-1]:
            f=frames[index]
            with archive.open(f['member']) as source: ds=pydicom.dcmread(source)
            pixels=ds.pixel_array
            require(len(ds.PixelData) == pixels.size * 2, 'Source integrity condition failed: len(ds.PixelData) == pixels.size * 2')
            require(str(ds.file_meta.TransferSyntaxUID) in {'1.2.840.10008.1.2', '1.2.840.10008.1.2.1'}, "Source integrity condition failed: str(ds.file_meta.TransferSyntaxUID) in {'1.2.840.10008.1.2', '1.2.840.10008.1.2.1'}")
            require(ds.PixelRepresentation == 1 and ds.BitsAllocated == ds.BitsStored == 16, 'Source integrity condition failed: ds.PixelRepresentation == 1 and ds.BitsAllocated == ds.BitsStored == 16')
            independent=np.frombuffer(ds.PixelData,dtype='<i2').reshape(ds.Rows,ds.Columns)
            require(np.array_equal(pixels, independent), 'Independent native decode mismatch')
            values=pixels.astype(np.float32)*f['rescale_slope']+f['rescale_intercept']
            # Display only; raw DICOM bytes and pixel values are not altered.
            low,high=-1100,500
            preview=np.rint(np.clip((values-low)/(high-low),0,1)*255).astype(np.uint8)
            path=args.output/f'plane-{index:03d}.png';Image.fromarray(preview).save(path)
            samples.append(dict(index=index,member=f['member'],raw_min=int(pixels.min()),raw_max=int(pixels.max()),raw_sha256=hashlib.sha256(pixels.tobytes()).hexdigest(),independent_little_endian_decode_matches=True,rescaled_min=float(values.min()),rescaled_max=float(values.max()),preview=path.name,preview_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),display_window=[low,high],display_units=f['rescale_units'],physical_calibration_independently_verified=False))
    report=dict(source_doi=source_info['doi'],source_url=source_info['url'],license='CC BY 4.0',archive=dict(bytes=source_info['bytes'],md5=md5.hexdigest(),sha256=sha.hexdigest(),all_member_crcs_valid=True),frame_count=len(frames),geometry=dict(rows=first['rows'],columns=first['columns'],pixel_spacing_mm=first['pixel_spacing_mm'],slice_thickness_mm=first['slice_thickness_mm'],minimum_plane_step_mm=float(steps.min()),maximum_plane_step_mm=float(steps.max()),regular_grid=regular,in_plane_origin_drift_mm=float(np.linalg.norm(residual,axis=1).max()),first_position_mm=frames[0]['position_mm'],last_position_mm=frames[-1]['position_mm'],slice_center_span_mm=float((positions[-1]-positions[0])@normal),through_plane_cell_extent_mm=float((positions[-1]-positions[0])@normal+first['slice_thickness_mm']),orientation=first['orientation']),frames=frames,samples=samples,clinical_approval=False,runtime_promoted=False,complete_anatomical_extent_proven=False)
    (args.output/'native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['frame_count','geometry','complete_anatomical_extent_proven']},indent=2))


if __name__ == '__main__':
    main()
