"""Lossless full CT, all original XML marks, and every standardized SEG cell.

No clinical diagnosis, reader consensus, resampling, smoothing, or anatomical
segmentation is inferred. CT and SEG coordinates remain separate source facts.
"""
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import shutil
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / '.research/pulmonary-intake-20261011'
sys.path.insert(0, str(PRIVATE / 'python-deps'))
import pydicom

OUT = ROOT / 'web/anatomy/lidc-idri-0525'
REVIEW = ROOT / 'docs/pulmonary-nodule-source-review-20261011'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def write(name, raw, compressed=False):
    body = gzip.compress(raw, mtime=0) if compressed else raw
    (OUT / name).write_bytes(body)
    row = dict(file=name, bytes=len(body), sha256=sha(body))
    if compressed:
        row.update(codec='gzip', decoded_bytes=len(raw), decoded_sha256=sha(raw))
    return row


def tag(e):
    return e.tag.rsplit('}', 1)[-1]


def text(e, name):
    return next((x.text for x in e.iter() if tag(x) == name), None)


def xml_marks(raw, by_sop):
    root = ET.fromstring(raw)
    assert text(root, 'SeriesInstanceUid') == '1.3.6.1.4.1.14519.5.2.1.6279.6001.716498695101447665580610403574'
    marks, ids = [], {}
    for session_i, session in enumerate(x for x in root if tag(x) == 'readingSession'):
        for item in session:
            kind = tag(item)
            if kind not in ('unblindedReadNodule', 'nonNodule'):
                continue
            char = next((x for x in item if tag(x) == 'characteristics'), None)
            nid = text(item, 'noduleID') or text(item, 'nonNoduleID')
            rois = []
            for r in item:
                if tag(r) != 'roi':
                    continue
                sop = text(r, 'imageSOP_UID')
                points = [[int(text(p, 'xCoord')), int(text(p, 'yCoord'))] for p in r if tag(p) == 'edgeMap']
                assert sop in by_sop
                assert all(0 <= x < 512 and 0 <= y < 512 for x, y in points)
                rois.append(dict(source_sop=sop, ct_slice=by_sop[sop],
                                 imageZposition=text(r, 'imageZposition'),
                                 inclusion=text(r, 'inclusion'), points=points))
            if kind == 'nonNodule':
                sop = text(item, 'imageSOP_UID')
                assert sop in by_sop
                rois.append(dict(source_sop=sop, ct_slice=by_sop[sop], points=[[int(text(item, 'xCoord')), int(text(item, 'yCoord'))]], source_locus_only=True))
            row = dict(session_index=session_i, source_id=nid, kind=kind,
                       characteristics={tag(x): x.text for x in char} if char is not None else {}, rois=rois,
                       complete_contour=char is not None, centroid_only=char is None)
            marks.append(row)
            if kind == 'unblindedReadNodule' and char is not None:
                assert nid not in ids
                ids[nid] = row
    return marks, ids


def sr_tree(item):
    name = getattr(item, 'ConceptNameCodeSequence', [])
    codes = getattr(item, 'ConceptCodeSequence', [])
    row = dict(value_type=str(getattr(item, 'ValueType', 'ROOT')),
               name=str(name[0].CodeMeaning) if name else '',
               children=[sr_tree(c) for c in getattr(item, 'ContentSequence', [])])
    if codes:
        row['coded_value'] = dict(meaning=str(codes[0].CodeMeaning), value=str(codes[0].CodeValue), scheme=str(codes[0].CodingSchemeDesignator))
    if hasattr(item, 'MeasuredValueSequence'):
        q = item.MeasuredValueSequence[0]
        row['measurement'] = dict(value=str(q.NumericValue), unit=str(q.MeasurementUnitsCodeSequence[0].CodeValue))
    if hasattr(item, 'TextValue'):
        row['text'] = str(item.TextValue)
    return row


def boundary(mask, origins, spacing, half_z):
    """All exposed cells with exact frame centres and midpoint inter-frame faces.

    The source DICOM positions are rounded independently; do not replace them
    with a fitted affine. Midpoint sampling cells are an explicitly identified
    display adaptation, not a histological surface or acquired continuous tissue.
    """
    z_positions = np.asarray([o[2] for o in origins])
    assert np.all(np.diff(z_positions) > 0)
    z_faces = np.r_[z_positions[0] - half_z, (z_positions[1:] + z_positions[:-1]) / 2, z_positions[-1] + half_z]
    vertices, faces, exposed, indices = [], [], [], {}
    for axis in range(3):
        for sign in (-1, 1):
            for p in np.argwhere(mask):
                q = p.copy(); q[axis] += sign
                if 0 <= q[axis] < mask.shape[axis] and mask[tuple(q)]:
                    continue
                other = [i for i in range(3) if i != axis]
                keys = []
                for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    v = 2 * p.copy(); v[axis] += sign; v[other[0]] += a; v[other[1]] += b
                    keys.append(tuple(map(int, v)))
                if np.cross(np.array(keys[1]) - keys[0], np.array(keys[2]) - keys[0])[axis] * sign < 0:
                    keys.reverse()
                # Storage coordinates are z/y/x; convert every face to LPS x/y/z.
                point_ids = []
                for key in keys:
                    if key not in indices:
                        z2, y2, x2 = key
                        z_face = (z2 + 1) // 2
                        # This fixed source orientation is identity; differing
                        # origins in x/y would require a separate geometry rule.
                        point = [origins[0][0] + x2 * spacing[1] / 2,
                                 origins[0][1] + y2 * spacing[0] / 2, z_faces[z_face]]
                        indices[key] = len(vertices); vertices.append(point)
                    point_ids.append(indices[key])
                # z/y/x to x/y/z reverses handedness.
                faces.extend([[point_ids[0], point_ids[2], point_ids[1]], [point_ids[0], point_ids[3], point_ids[2]]])
                exposed.append([*map(int, p), axis, sign])
    return np.asarray(vertices, dtype='<f8'), np.asarray(faces, dtype='<u4'), np.asarray(exposed, dtype='<i4')


def main():
    OUT.mkdir(parents=True, exist_ok=True); REVIEW.mkdir(parents=True, exist_ok=True)
    (OUT / 'original-ct').mkdir(exist_ok=True)
    # Large source ZIPs are archival intake, never future Git/runtime units.
    old_zip = OUT / 'LIDC-IDRI-0525-complete-with-license.zip'
    if old_zip.exists():
        assert sha(old_zip.read_bytes()) == sha((PRIVATE / old_zip.name).read_bytes())
        old_zip.unlink()
    manifest = dict(schema_version=1, id='lidc-idri-0525', case='LIDC-IDRI-0525',
        dataset_doi='https://doi.org/10.7937/K9/TCIA.2015.LO9QL9SX',
        annotation_doi='https://doi.org/10.7937/TCIA.2018.h7umfurq',
        license='CC BY 3.0', license_url='https://creativecommons.org/licenses/by/3.0/',
        clinical_approval=False, fine_anatomical_approval=False, structure_coverage_granted=False,
        source_sample_changes=False, source_resampling=False, source_smoothing=False,
        histology_verified=False, current_patient_registration=False, original_files=[], annotations=[],
        source_dates_deidentified_not_followup=True, ct_seg_coordinates_identical=False,
        lobes_or_bronchopulmonary_segments_annotated=False,
        source_ct_full_extent=True, source_xml_all_marks=True, source_seg_all_objects=True)
    md5_rows = list(csv.DictReader((PRIVATE / 'md5hashes.csv').read_text().splitlines()))
    md5 = {r['Filename']: r['MD5Hash'] for r in md5_rows}
    source_zip = PRIVATE / 'LIDC-IDRI-0525-complete-with-license.zip'
    files, images = [], []
    with zipfile.ZipFile(source_zip) as z:
        for name in z.namelist():
            raw = z.read(name)
            if name == 'LICENSE':
                manifest['archive_license'] = write('LICENSE', raw)
                assert b'CC BY 3.0' in raw and b'DACs must provide attribution' in raw
                continue
            assert name.endswith('.dcm') and hashlib.md5(raw).hexdigest() == md5[name]
            d = pydicom.dcmread(io.BytesIO(raw))
            assert d.PatientID == manifest['case'] and d.Modality == 'CT'
            images.append((d, raw, name))
        assert len(images) == 429 and len(md5) == 429
    images.sort(key=lambda x: float(x[0].ImagePositionPatient[2]))
    by_sop = {str(d.SOPInstanceUID): j for j, (d, _, _) in enumerate(images)}
    assert len(by_sop) == 429
    sample_arrays = []
    for j, (d, raw, name) in enumerate(images):
        assert list(map(float, d.ImageOrientationPatient)) == [1, 0, 0, 0, 1, 0]
        assert [int(d.Rows), int(d.Columns), int(d.BitsStored), int(d.PixelRepresentation)] == [512, 512, 12, 0]
        assert float(d.RescaleSlope) == 1 and float(d.RescaleIntercept) == -1024
        a = d.pixel_array
        assert np.array_equal(a, np.frombuffer(d.PixelData, dtype='<u2').reshape(512, 512))
        sample_arrays.append(a)
        manifest['original_files'].append(write('original-ct/' + name, raw))
        files.append(dict(filename=name, ct_slice=j, bytes=len(raw), sha256=sha(raw), md5=hashlib.md5(raw).hexdigest(),
            sop_uid=str(d.SOPInstanceUID), instance_number=int(d.InstanceNumber),
            position_LPS_mm=list(map(float, d.ImagePositionPatient)), orientation=list(map(float, d.ImageOrientationPatient)),
            pixel_spacing_mm=list(map(float, d.PixelSpacing)), thickness_mm=float(d.SliceThickness),
            slope=float(d.RescaleSlope), intercept=float(d.RescaleIntercept), kernel=str(d.ConvolutionKernel)))
    array = np.stack(sample_arrays); del sample_arrays
    positions = [f['position_LPS_mm'] for f in files]
    delta = np.diff(np.asarray(positions)[:, 2]); assert np.all((delta > .6999) & (delta < .7001))
    raw = array.astype('<u2').tobytes(order='C')
    previous_transport = OUT/'ct.native.gz'
    if previous_transport.exists():
        assert sha(gzip.decompress(previous_transport.read_bytes())) == sha(raw)
        shutil.move(previous_transport,PRIVATE/'first-unpublished-transport.ct.native.gz')
    chunks=[]
    for first in range(0,429,64):
        stop=min(first+64,429)
        chunk_raw=raw[first*512*512*2:stop*512*512*2]
        chunks.append(dict(**write('ct.native.'+str(first).zfill(3)+'-'+str(stop-1).zfill(3)+'.gz',chunk_raw,True),first_native_slice=first,stop_native_slice_exclusive=stop))
    manifest['ct'] = dict(chunks=chunks,decoded_bytes=len(raw),decoded_sha256=sha(raw),
        complete_buffer_transport='seven lossless contiguous original CT storage chunks; every sample retained',
        shape=[512, 512, 429], storage_order='x_fast_then_y_then_z',
        dtype='<u2', source_samples=int(array.size), slope=1, intercept=-1024, HU_calibration='original per-instance DICOM slope/intercept',
        pixel_spacing_mm=files[0]['pixel_spacing_mm'], thickness_mm=.75, positions_LPS_mm=positions,
        orientation=[1, 0, 0, 0, 1, 0], slice_spacing_range_mm=[float(delta.min()), float(delta.max())],
        source_kernel='B30f', min_stored=int(array.min()), max_stored=int(array.max()), slices=files)
    manifest['original_files'].append(write('ct-source-md5.csv', (PRIVATE / 'md5hashes.csv').read_bytes()))
    xml_raw = (PRIVATE / '0525-original.xml').read_bytes()
    marks, ids = xml_marks(xml_raw, by_sop)
    manifest['original_files'].append(write('original-0525.xml', xml_raw))
    manifest['xml_marks'] = marks
    receipt = json.loads((PRIVATE / 'annotations-download-receipt.json').read_text())
    sr = {}
    for row in receipt:
        source = PRIVATE / 'standardized-annotations' / row['archive_name']
        manifest['original_files'].append(write(row['archive_name'], source.read_bytes()))
        with zipfile.ZipFile(source) as z:
            original_name = next(n for n in z.namelist() if n.endswith('.dcm'))
            original_raw = z.read(original_name)
            checks = {r['Filename']: r['MD5Hash'] for r in csv.DictReader(z.read('md5hashes.csv').decode().splitlines())}
            assert hashlib.md5(original_raw).hexdigest() == checks[original_name]
            d = pydicom.dcmread(io.BytesIO(original_raw))
        if d.Modality == 'SR':
            key = str(d.SeriesDescription).removesuffix(' evaluations')
            sr[key] = dict(source_sop=str(d.SOPInstanceUID), full_content_tree=sr_tree(d),
                           original_dicom_sha256=sha(original_raw), original_archive=row['archive_name'])
    for row in receipt:
        if row['series']['Modality'] != 'SEG':
            continue
        with zipfile.ZipFile(PRIVATE / 'standardized-annotations' / row['archive_name']) as z:
            original_raw = z.read(next(n for n in z.namelist() if n.endswith('.dcm')))
        d = pydicom.dcmread(io.BytesIO(original_raw)); s = d.SharedFunctionalGroupsSequence[0]
        assert str(d.SegmentationType) == 'BINARY' and len(d.SegmentSequence) == 1
        assert list(map(float, s.PlaneOrientationSequence[0].ImageOrientationPatient)) == [1, 0, 0, 0, 1, 0]
        pixel = list(map(float, s.PixelMeasuresSequence[0].PixelSpacing))
        step = float(s.PixelMeasuresSequence[0].SpacingBetweenSlices)
        mask = d.pixel_array.astype(np.uint8)
        label = str(d.SegmentSequence[0].SegmentLabel); key = 'annotation-' + label.split('Annotation ')[1]
        mark = ids[key.removeprefix('annotation-')]
        origins, ct_slices, frame_sources = [], [], []
        for group in d.PerFrameFunctionalGroupsSequence:
            origin = list(map(float, group.PlanePositionSequence[0].ImagePositionPatient)); origins.append(origin)
            source = str(group.DerivationImageSequence[0].SourceImageSequence[0].ReferencedSOPInstanceUID)
            assert source in by_sop
            ct_slices.append(by_sop[source]); frame_sources.append(source)
        assert len(origins) == mask.shape[0]
        assert np.all(np.diff(ct_slices) == 1)
        assert all(o[:2] == origins[0][:2] for o in origins)
        # XML includes separate inclusion/exclusion contours on the same SOP;
        # source SEG stores one raster frame after applying those contours.
        assert set(frame_sources) == {r['source_sop'] for r in mark['rois']}
        difference = np.asarray(origins) - np.asarray([positions[k] for k in ct_slices])
        assert np.max(np.abs(difference)) < .0006
        coords, triangles, face_records = boundary(mask.astype(bool), origins, pixel, step / 2)
        mesh_raw = b'LPC1' + struct.pack('<II', len(coords), len(triangles)) + coords.tobytes() + triangles.tobytes()
        connected = ndimage.label(mask, ndimage.generate_binary_structure(3, 1))[1]
        part = dict(id=key, label=label, xml_session_index=mark['session_index'], source_content_creator=str(getattr(d,'ContentCreatorName','')),
            source_algorithm_type=str(d.SegmentSequence[0].SegmentAlgorithmType),
            source_dicom_sha256=sha(original_raw), source_sop=str(d.SOPInstanceUID), source_archive=row['archive_name'],
            source_CT_slice_indices=ct_slices, source_CT_sop_uids=frame_sources,
            source_frame_origins_LPS_mm=origins, pixel_spacing_mm=pixel, source_spacing_mm=step,
            source_thickness_mm=float(s.PixelMeasuresSequence[0].SliceThickness),
            CT_SEG_position_difference_range_mm=[difference.min(axis=0).tolist(),difference.max(axis=0).tolist()],
            CT_SEG_pixel_spacing_difference_mm=(np.asarray(pixel)-files[0]['pixel_spacing_mm']).tolist(),
            source_samples=int(mask.size), occupied_voxels=int(mask.sum()), six_connected_components=int(connected),
            source_shape=[512,512,len(origins)], mask=write(key+'.mask.gz',mask.tobytes(order='C'),True),
            mesh=dict(**write(key+'.mesh.gz',mesh_raw,True),vertices=len(coords),triangles=len(triangles),
                bounds_LPS_mm=[coords.min(axis=0).tolist(),coords.max(axis=0).tolist()],
                complete_exposed_faces=len(face_records), geometry='literal source sampling-cell boundary; exact source frame centres; midpoint inter-frame faces'),
            face_records=write(key+'.faces.gz',face_records.tobytes(),True),
            characteristics=mark['characteristics'], source_SR=sr[label])
        part['original_XML_ROI_count'] = len(mark['rois'])
        part['original_XML_exclusion_contours'] = sum(r['inclusion'] == 'FALSE' for r in mark['rois'])
        manifest['annotations'].append(part)
    manifest['annotations'].sort(key=lambda x: (int(x['label'].split()[1]),x['xml_session_index']))
    assert len(manifest['annotations']) == 8
    manifest['source_limits'] = [
        'Four XML sessions remain separate. Standardized SEG ContentCreatorName is Reader1 in every object; use explicit original XML session index, not that reused value, to distinguish this case’s original reading sessions. Session identities cannot be compared across cases.',
        'The collection documents inconsistent spiculation/lobulation coding in about100 early cases; this case was selected after inspecting native metadata, but selection alone does not prove corrected clinical ratings.',
        'No histology, diagnosis, exact eligibility, longitudinal CT, PET, solid-component-specific mask, lobe or bronchopulmonary segment annotation is asserted for this case.',
        'SEG original decimal coordinate/spacing rounding differs from CT. Overlay links discrete pixels by original referenced SOP; original SEG and CT coordinate values are both preserved. No affine is fitted or positions snapped.',
        'CT planes retain every stored voxel and per-slice position. Orthogonal native index views are display-only nearest-neighbour sampling, not new diagnostic reconstructions.',
        '3D cells are an explicit display adaptation of released binary SEG masks. Every source component/face is retained; cells use exact original frame centres and midpoint inter-frame sampling faces. Block boundaries are neither histology nor a clinician-approved nodule surface.',
        'XML outlines describe the first outside pixel, exclusions remain exclusions, and sub3mm/non-nodule marks are loci only. They are not silently filled or promoted to full surfaces.',
    ]
    (OUT / 'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    proof = dict(manifest_sha256=sha((OUT/'manifest.json').read_bytes()), source_CT_samples=int(array.size),
        source_SEG_objects=8,source_SR_objects=8,original_XML_marks=len(marks),original_XML_sessions=4,
        source_SEG_samples=sum(x['source_samples'] for x in manifest['annotations']),
        occupied_SEG_voxels=sum(x['occupied_voxels'] for x in manifest['annotations']),
        complete_cell_triangles=sum(x['mesh']['triangles'] for x in manifest['annotations']),
        original_files=len(manifest['original_files']),source_and_transport_files=9+len(manifest['original_files'])+24,
        source_arrays_match_all_original_DICOM_pixel_data=True,source_archive_md5_checks=429+16,
        ct_license_archive_present=True,clinical_approval=False,structure_coverage_granted=False,
        fine_anatomical_approval=False,source_resampling=False, source_smoothing=False,
        scope='this complete source CT case and every original released XML/SEG/SR annotation; not full module completion')
    (REVIEW/'native-build-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))


if __name__ == '__main__':
    main()
