#!/usr/bin/env python3
"""Audit the acquired Leeds DOI 10.5518/981 Knee 2 DESS source offline.

Requires pydicom, NumPy and Pillow. No downloads, source changes, resampling,
registration or clinical promotion occur. Identifying DICOM values are never
serialized: metadata output uses an explicit acquisition/geometry allowlist.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import zlib

import numpy as np
import pydicom
from PIL import Image, ImageDraw, __version__ as pillow_version


ARCHIVES = {
    "1-LTKN8941_FE_model_INP_files.zip": {
        "bytes": 71895079,
        "sha256": "5ebb964179fd12b337b36bd29438c102db05c1300a1f8b70e7368608bd62a03d",
    },
    "6-Knee_MR_preview_slices.zip": {
        "bytes": 12924914,
        "sha256": "9d0db0742ab39ef22f1ee8237d6c2b4b2deaca76e78298078eba242fc02d8a8f",
    },
    "6-LTKN8941_MR_DESS.zip": {
        "bytes": 19682907,
        "sha256": "932f42f6312c57c8574bf03a343344c1a408b6f54df07dae433cb315adc31ad3",
    },
}
DICOM_MEMBER = "LTKN8941_MR_Series_7_DESS_PC_Knee2/87390321"
PRESENCE_ONLY = (
    "PatientName", "PatientID", "PatientBirthDate", "PatientSex", "PatientAge",
    "PatientWeight", "PatientSize", "AccessionNumber", "InstitutionName",
    "InstitutionAddress", "ReferringPhysicianName", "OperatorsName", "StudyDate",
    "SeriesDate", "AcquisitionDateTime", "StationName", "DeviceSerialNumber",
    "StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "FrameOfReferenceUID",
)


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_archives(root):
    """Recheck local pinned bytes, download records and every uncompressed CRC."""
    records = []
    for name, expected in ARCHIVES.items():
        path = root / name
        previous = json.loads((root / (name + ".integrity.json")).read_text())
        size, sha, md5 = path.stat().st_size, digest(path), digest(path, "md5")
        assert (size, sha) == (expected["bytes"], expected["sha256"]), name
        assert (size, sha, md5) == (previous["bytes"], previous["sha256"], previous["md5"]), name
        assert int(previous["response_headers"]["Content-Length"]) == size
        assert previous["response_headers"]["ETag"].strip('"') == md5
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None, name
            members = [{"name": x.filename, "bytes": x.file_size,
                        "compressed_bytes": x.compress_size,
                        "crc32": f"{x.CRC:08x}", "compression": x.compress_type}
                       for x in archive.infolist()]
        assert members == previous["entries"], name
        records.append({"file": name, "source_url": previous["url"], "bytes": size,
                        "sha256": sha, "md5": md5,
                        "downloaded_utc": previous["retrieved_utc"],
                        "all_member_crcs_pass": True, "members": members,
                        "download_content_length_matches": True,
                        "download_etag_matches_md5": True,
                        "hash_basis": "Locally computed SHA-256 pin; repository response ETag matched MD5. No published SHA-256 claimed."})
    return records


def verify_documentation(root):
    records = json.loads((root / "documentation-downloads.json").read_text())
    for record in records:
        path = root / record["file"]
        assert path.stat().st_size == record["bytes"]
        assert digest(path) == record["sha256"]
        assert digest(path, "md5") == record["headers"]["ETag"].strip('"')
    readme = (root / "README_Cooper-etal_2023.txt").read_text()
    assert "This dataset is licensed under a Creative Commons Attribution" in readme
    assert "4.0 International Licence: https://creativecommons.org/licenses/by/4.0/" in readme
    return [{"file": r["file"], "source_url": r["url"], "bytes": r["bytes"],
             "sha256": r["sha256"]} for r in records]


def value(ds, name):
    v = ds.get(name)
    if v is None:
        return None
    if isinstance(v, (list, tuple, pydicom.multival.MultiValue)):
        return [str(x) for x in v]
    return str(v)


def one(group, sequence):
    return group.get(sequence, [pydicom.dataset.Dataset()])[0]


def frame_record(group, index):
    orientation = one(group, "PlaneOrientationSequence")
    position = one(group, "PlanePositionSequence")
    measures = one(group, "PixelMeasuresSequence")
    rescale = one(group, "PixelValueTransformationSequence")
    voi = one(group, "FrameVOILUTSequence")
    content = one(group, "FrameContentSequence")
    return {
        "index_zero_based": index,
        "in_stack_position": int(content.InStackPositionNumber),
        "dimension_index_values": [int(x) for x in content.DimensionIndexValues],
        "temporal_position": int(content.TemporalPositionIndex),
        "iop": [float(x) for x in orientation.ImageOrientationPatient],
        "ipp_mm": [float(x) for x in position.ImagePositionPatient],
        "pixel_spacing_row_column_mm": [float(x) for x in measures.PixelSpacing],
        "slice_thickness_mm": float(measures.SliceThickness),
        "spacing_between_slices_mm": (float(measures.SpacingBetweenSlices)
                                       if "SpacingBetweenSlices" in measures else None),
        "rescale_slope": float(rescale.RescaleSlope),
        "rescale_intercept": float(rescale.RescaleIntercept),
        "rescale_type": str(rescale.RescaleType),
        "source_window_center": float(voi.WindowCenter),
        "source_window_width": float(voi.WindowWidth),
        "source_voi_lut_function": str(voi.get("VOILUTFunction", "LINEAR (default)")),
        "effective_echo_time_ms": float(one(group, "MREchoSequence").EffectiveEchoTime),
    }


def geometry(frames):
    positions = np.array([f["ipp_mm"] for f in frames])
    iops = np.array([f["iop"] for f in frames])
    assert np.allclose(iops, iops[0], atol=1e-6)
    assert [f["in_stack_position"] for f in frames] == list(range(1, len(frames) + 1))
    assert all(f["dimension_index_values"] == [1, i + 1, 1] for i, f in enumerate(frames))
    right, down = iops[0, :3], iops[0, 3:]
    normal = np.cross(right, down)
    norm = normal / np.linalg.norm(normal)
    steps = np.diff(positions, axis=0)
    signed = steps @ norm
    off_normal = steps - np.outer(signed, norm)
    mean_step = steps.mean(axis=0)
    residual = positions - (positions[0] + np.arange(len(frames))[:, None] * mean_step)
    assert np.all(signed < 0), "Unexpected frame progression; audit before using labels"
    assert abs(np.dot(right, down)) < 1e-5
    assert np.allclose([np.linalg.norm(right), np.linalg.norm(down)], 1, atol=1e-5)
    spacing = np.array([f["pixel_spacing_row_column_mm"] for f in frames])
    assert np.allclose(spacing, spacing[0], atol=1e-6)
    # DICOM human/default BIPED coordinates: +X left, +Y posterior, +Z head.
    assert np.argmax(np.abs(right)) == 1 and right[1] > 0
    assert np.argmax(np.abs(down)) == 2 and down[2] < 0
    return {
        "coordinate_system": "DICOM patient LPS; BIPED default when AnatomicalOrientationType is absent",
        "all_iop_and_pixel_spacing_equal": True,
        "all_stack_positions_contiguous_1_to_144": True,
        "all_dimension_indices_single_spatial_stack": True,
        "array_column_increase_patient_direction": right.tolist(),
        "array_row_increase_patient_direction": down.tolist(),
        "cross_column_row_direction": normal.tolist(),
        "mean_array_frame_step_patient_mm": mean_step.tolist(),
        "signed_step_along_iop_cross_normal_mm_range": [float(signed.min()), float(signed.max())],
        "step_length_mm_range": [float(np.linalg.norm(steps, axis=1).min()),
                                 float(np.linalg.norm(steps, axis=1).max())],
        "maximum_off_normal_step_mm": float(np.linalg.norm(off_normal, axis=1).max()),
        "maximum_linear_grid_position_residual_mm": float(np.linalg.norm(residual, axis=1).max()),
        "first_ipp_mm": positions[0].tolist(), "last_ipp_mm": positions[-1].tolist(),
        "first_to_last_center_distance_mm": float(np.linalg.norm(positions[-1] - positions[0])),
        "slice_plane": "oblique sagittal; not cardinal sagittal reformat",
        "orientation_labels": "Image right is predominantly posterior, down predominantly inferior. Increasing frame index is predominantly leftward. Full vectors retained; no pure-cardinal-axis claim.",
        "native_index_to_patient_formula": "P(k,r,c) = IPP[k] + c*PixelSpacing[1]*IOP[0:3] + r*PixelSpacing[0]*IOP[3:6]",
        "resampling_applied": False, "image_to_fe_transform_established": False,
    }


def privacy(ds):
    states = {key: ("absent" if key not in ds else "empty" if ds.data_element(key).is_empty else "populated")
              for key in PRESENCE_ONLY}
    return {
        "PatientIdentityRemoved": value(ds, "PatientIdentityRemoved"),
        "BurnedInAnnotation": value(ds, "BurnedInAnnotation"),
        "RecognizableVisualFeatures": value(ds, "RecognizableVisualFeatures"),
        "DeidentificationMethod_present": "DeidentificationMethod" in ds,
        "presence_only_no_values": states,
        "private_elements_recursive_count": sum(e.tag.is_private for e in ds.iterall()),
        "release_deidentification_complete": False,
        "limitation": "Flags and tag presence are indicators only. Populated values are deliberately not disclosed or verified as donor identifiers. Public repository availability and CC BY do not establish DICOM de-identification. Raw DICOM remains staged; no raw identifying/private tags are copied to this report or PNGs.",
    }


def render(pixels, frames, out, center, width):
    assert width > 1
    chosen = [16, 40, 64, 88, 112, 128]
    # DICOM default LINEAR VOI formula; round the resulting grayscale to uint8.
    # This changes display intensities only; each saved array is 384x384 unchanged
    # in position/orientation, and no image resampling or filtering occurs.
    rendered = []
    board = Image.new("RGB", (1280, 1000), (20, 24, 30))
    draw = ImageDraw.Draw(board)
    draw.text((18, 12), "Leeds Knee 2 / LTKN8941: native DESS-labelled Enhanced MR source frames", fill="white")
    draw.text((18, 33), f"Fixed DICOM LINEAR display: center={center:g}, width={width:g}; native 384x384 pixels; no resampling", fill="white")
    draw.text((18, 54), "DICOM geometry: oblique sagittal. Image right ~ posterior; image down ~ inferior. LPS vectors in audit JSON.", fill="white")
    draw.text((18, 75), "Acquired cadaver research source; review images do not establish clinical approval or normality.", fill="white")
    for panel, k in enumerate(chosen):
        f = frames[k]
        x = pixels[k].astype(np.float64) * f["rescale_slope"] + f["rescale_intercept"]
        windowed = np.clip((x - (center - 0.5)) / (width - 1) + 0.5, 0, 1)
        array = np.rint(windowed * 255).astype(np.uint8)
        name = f"native-frame-{k + 1:03d}-fixed-window.png"
        image = Image.fromarray(array)
        image.save(out / name)
        # A 1:1 paste, not a resize. Labels live outside source image pixels.
        left, top = 18 + panel % 3 * 420, 132 + panel // 3 * 434
        board.paste(image.convert("RGB"), (left, top))
        draw.text((left, top - 22), f"Frame {k + 1}/144 (array index {k}) | native pixels", fill="white")
        draw.text((left, top + 390), "right ~ P (oblique); down ~ I (oblique)", fill=(195, 205, 215))
        rendered.append({"filename": name, "frame_zero_based": k,
                         "in_stack_position": k + 1,
                         "png_sha256": digest(out / name),
                         "pixel_sha256_uint8_c_order": hashlib.sha256(array.tobytes()).hexdigest(),
                         "clipped_below_voxels": int(np.count_nonzero(x < center - 0.5 - (width - 1) / 2)),
                         "clipped_above_voxels": int(np.count_nonzero(x > center - 0.5 + (width - 1) / 2))})
    contact_name = "native-source-frames-contact-sheet.png"
    board.save(out / contact_name)
    return {"center": center, "width": width, "function": "DICOM LINEAR",
            "black_value": center - 0.5 - (width - 1) / 2,
            "white_value": center - 0.5 + (width - 1) / 2,
            "output_bits": 8, "quantization": "round to nearest via numpy.rint",
            "full_stored_value_range_default": [0, 614],
            "source_window_values_retained_but_not_applied": True,
            "interpolation_resampling_flipping_rotation_or_ai_edits": False,
            "contact_sheet_pixels_pasted_at_one_to_one": True,
            "contact_sheet": contact_name, "contact_sheet_sha256": digest(out / contact_name),
            "native_frames": rendered}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--window-center", type=float, default=307.5)
    parser.add_argument("--window-width", type=float, default=615)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "source_doi": "10.5518/981",
              "source_record": "https://archive.researchdata.leeds.ac.uk/1082/",
              "status": "acquired_research_candidate_no_clinical_approval",
              "archives": verify_archives(args.source_root),
              "documentation": verify_documentation(args.source_root),
              "license": {"id": "CC-BY-4.0", "url": "https://creativecommons.org/licenses/by/4.0/",
                          "basis": "README_Cooper-etal_2023.pdf p2 Terms of Use; source grant covers this dataset. Attribution and modification disclosure remain required."},
              "runtime": {"python": sys.version.split()[0], "pydicom": pydicom.__version__,
                          "numpy": np.__version__, "pillow": pillow_version}}
    path = args.source_root / "dicom-originals" / "87390321"
    payload = path.read_bytes()
    with zipfile.ZipFile(args.source_root / "6-LTKN8941_MR_DESS.zip") as archive:
        info = archive.getinfo(DICOM_MEMBER)
        assert len(payload) == info.file_size
        assert zlib.crc32(payload) & 0xffffffff == info.CRC
        assert payload == archive.read(DICOM_MEMBER)
    report["dicom_member"] = {"name": DICOM_MEMBER, "bytes": len(payload),
                              "crc32": f"{info.CRC:08x}", "sha256": digest(path),
                              "matches_complete_archive_member_byte_for_byte": True}
    ds = pydicom.dcmread(path)
    assert str(ds.SOPClassUID) == "1.2.840.10008.5.1.4.1.1.4.1"
    assert str(ds.file_meta.TransferSyntaxUID) == "1.2.840.10008.1.2.1"
    assert (ds.Rows, ds.Columns, int(ds.NumberOfFrames)) == (384, 384, 144)
    assert (ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation) == (16, 12, 11, 0)
    assert ds.PhotometricInterpretation == "MONOCHROME2" and ds.SamplesPerPixel == 1
    acquisition_keys = (
        "Modality", "Manufacturer", "ManufacturerModelName", "MagneticFieldStrength",
        "ImageType", "PixelPresentation", "VolumetricProperties", "ComplexImageComponent",
        "AcquisitionContrast", "MRAcquisitionType", "EchoPulseSequence", "SteadyStatePulseSequence",
        "EchoPlanarPulseSequence", "SpectrallySelectedSuppression", "AnatomicalOrientationType",
        "PatientPosition", "Laterality", "ImageLaterality", "LossyImageCompression", "PresentationLUTShape",
    )
    shared = ds.SharedFunctionalGroupsSequence[0]
    report["acquisition"] = {k: value(ds, k) for k in acquisition_keys}
    report["acquisition"].update({
        "sop_class": str(ds.SOPClassUID), "sop_class_name": ds.SOPClassUID.name,
        "transfer_syntax": str(ds.file_meta.TransferSyntaxUID),
        "transfer_syntax_name": ds.file_meta.TransferSyntaxUID.name,
        "receive_coil_name": value(one(shared, "MRReceiveCoilSequence"), "ReceiveCoilName"),
        "repetition_time_ms": value(one(shared, "MRTimingAndRelatedParametersSequence"), "RepetitionTime"),
        "flip_angle_degrees": value(one(shared, "MRTimingAndRelatedParametersSequence"), "FlipAngle"),
        "spectrally_selected_excitation": value(one(shared, "MRModifierSequence"), "SpectrallySelectedExcitation"),
        "sequence_text_token_checks_no_raw_text": {
            key: {"present": key in ds, "contains_DESS": "DESS" in str(ds.get(key, "")).upper()}
            for key in ["SeriesDescription", "ProtocolName", "SequenceName", "PulseSequenceName"]},
        "sequence_interpretation": "Repository names/README and DESS text tokens identify this series as DESS. Standard fields confirm 3D gradient-echo magnitude MR with water excitation; AcquisitionContrast UNKNOWN and SteadyStatePulseSequence NONE do not independently fully characterize DESS.",
        "scanner_resolution": "Selected Knee 2 acquisition records MAGNETOM Vida and TxRx_Knee_18, supporting README p7. Methods p2 generalization to Prisma/15-channel does not describe this stored acquisition; no correction inferred for other series.",
        "frame_laterality": value(one(shared, "FrameAnatomySequence"), "FrameLaterality"),
        "anatomic_region": [
            {key: value(region, key) for key in ("CodeValue", "CodingSchemeDesignator", "CodeMeaning")}
            for region in one(shared, "FrameAnatomySequence").get("AnatomicRegionSequence", [])],
    })
    frames = [frame_record(f, k) for k, f in enumerate(ds.PerFrameFunctionalGroupsSequence)]
    assert len(frames) == 144
    assert all(f["rescale_slope"] == 1 and f["rescale_intercept"] == 0 for f in frames)
    pixels = ds.pixel_array
    raw_pixels = np.frombuffer(ds.PixelData, dtype="<u2").reshape((144, 384, 384))
    assert np.array_equal(raw_pixels, pixels)
    assert pixels.max() < 2**12
    report["frames"] = frames
    report["geometry"] = geometry(frames)
    report["pixels"] = {
        "shape_frame_row_column": list(pixels.shape), "dtype": str(pixels.dtype),
        "bits_allocated": int(ds.BitsAllocated), "bits_stored": int(ds.BitsStored),
        "photometric_interpretation": str(ds.PhotometricInterpretation),
        "stored_pixel_bytes": len(ds.PixelData),
        "stored_pixel_sha256": hashlib.sha256(ds.PixelData).hexdigest(),
        "pydicom_matches_independent_little_endian_uint16_decode": True,
        "voxels": int(pixels.size), "nonzero_voxels": int(np.count_nonzero(pixels)),
        "minimum": int(pixels.min()), "maximum": int(pixels.max()),
        "quantiles": dict(zip(["p1", "p25", "p50", "p75", "p95", "p99", "p99_9"],
                              np.percentile(pixels, [1, 25, 50, 75, 95, 99, 99.9]).tolist())),
        "all_frames_nonempty": bool(np.all(np.any(pixels != 0, axis=(1, 2)))),
        "frame_nonzero_counts": np.count_nonzero(pixels, axis=(1, 2)).tolist(),
        "source_window_center_range": [min(f["source_window_center"] for f in frames), max(f["source_window_center"] for f in frames)],
        "source_window_width_range": [min(f["source_window_width"] for f in frames), max(f["source_window_width"] for f in frames)],
        "rescale_all_frames": {"slope": 1, "intercept": 0, "type": "US (unspecified units; not Hounsfield units)"},
    }
    report["deidentification_indicators"] = privacy(ds)
    report["review_rendering"] = render(pixels, frames, args.output, args.window_center, args.window_width)
    report["limitations"] = [
        "Full knee pixels and consistent DICOM geometry do not establish segmentation or clinical fidelity of individual reportable structures.",
        "One DESS-labelled MR series audited; other MR sequences and multi-GB microCT archives not acquired in this pass.",
        "Knee 2 is a left male61 cadaver specimen; methods only report no meniscal extrusion, not a globally normal knee.",
        "Methods derive bone/cartilage from post-meniscectomy CT and adjust MRI-derived menisci for contact conformity. No MRI-to-FE transform is provided or fitted here.",
        "De-identification, research-to-clinical applicability and anatomical component approval remain unestablished.",
        "No source pixels or geometry changed, no runtime/catalog/ledger promotion made.",
    ]
    (args.output / "imaging-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"archives_verified": len(report["archives"]), "frames": len(frames),
                      "pixel_shape": report["pixels"]["shape_frame_row_column"],
                      "scanner": report["acquisition"]["ManufacturerModelName"],
                      "deidentification_complete": False, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
