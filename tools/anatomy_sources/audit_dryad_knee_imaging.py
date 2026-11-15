#!/usr/bin/env python3
"""Inspect the actual S192803 imaging export; never infer a diagnostic pair.

Requires NumPy/Matplotlib and an Info-ZIP unzip with Deflate64 support. Extracts
only the named MRI scan and masks after verifying the full archive.
No downloaded code runs and no resampling, fitting or image repair is applied.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile
import zlib

import numpy as np


EXPECTED_SHA = "aa3fa1453cf20491494ef69dd02ed6bc92eb01e272159a5f3e4cdf6b2a5f9831"
EXPECTED_SIZE = 637706876
SELECTION = {
    "scan": "Imaging/MRI/Imaging/S192803_MRI_Scan",
    "acl_mask": "Imaging/MRI/Segmentation/S192803_ACL",
    "patella_mask": "Imaging/MRI/Segmentation/S192803_Patella_Left",
    "pcl_mask": "Imaging/MRI/Segmentation/S192803_PCL",
    "mcl_mask": "Imaging/MRI/Segmentation/S192803_MCL",
    "lcl_mask": "Imaging/MRI/Segmentation/S192803_LCL",
    "femur_mask": "Imaging/MRI/Segmentation/S192803_Femur_Left",
    "tibfib_mask": "Imaging/MRI/Segmentation/S192803_TibFib_Left",
    "femoral_cartilage_mask": "Imaging/MRI/Segmentation/S192803_Femur_Cartilage",
    "medial_tibial_cartilage_mask": "Imaging/MRI/Segmentation/S192803_Tibia_Cartilage_Medial",
    "lateral_tibial_cartilage_mask": "Imaging/MRI/Segmentation/S192803_Tibia_Cartilage_Lateral",
    "medial_meniscus_mask": "Imaging/MRI/Segmentation/S192803_Mensicus_Medial",
    "lateral_meniscus_mask": "Imaging/MRI/Segmentation/S192803_Mensicus_Lateral",
}


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def extract_checked(archive, member, info, destination):
    """Use native Deflate64, then independently verify count and ZIP CRC."""
    if not 0 < info.file_size <= 250_000_000 or info.compress_type not in {0, 8, 9}:
        raise ValueError("Unexpected selected member size or compression")
    process = subprocess.Popen(
        ["/usr/bin/unzip", "-p", str(archive), member],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    count, crc = 0, 0
    try:
        with destination.open("wb") as target:
            while True:
                block = process.stdout.read(1024 * 1024)
                if not block:
                    break
                count += len(block)
                if count > info.file_size:
                    raise ValueError("Uncompressed member exceeds declared size")
                crc = zlib.crc32(block, crc)
                target.write(block)
        error = process.stderr.read().decode("utf-8", errors="replace")
        if process.wait() or count != info.file_size or crc & 0xffffffff != info.CRC:
            raise ValueError("Member extraction/CRC failed: " + member + " " + error)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    return {"archive_member": member, "bytes": count,
            "crc32": format(crc & 0xffffffff, "08x"), "sha256": digest(destination)}


def header(path):
    fields = dict(line.split(" = ", 1) for line in path.read_text().splitlines()
                  if " = " in line)
    for name, value in {"NDims": "3", "ElementType": "MET_UCHAR",
                        "CompressedData": "False", "BinaryData": "True"}.items():
        if fields.get(name) != value:
            raise ValueError("Unsupported header value " + name)
    return {
        "fields": fields,
        "size_xyz": [int(x) for x in fields["DimSize"].split()],
        "spacing_xyz_mm": [float(x) for x in fields["ElementSpacing"].split()],
        "offset": [float(x) for x in fields["Offset"].split()],
        "transform_matrix_row_major": [float(x) for x in fields["TransformMatrix"].split()],
    }


def statistics(volume):
    histogram = np.bincount(volume.reshape(-1), minlength=256)
    nonzero = np.nonzero(volume)
    bounds = [[int(axis.min()), int(axis.max())] for axis in nonzero] if len(nonzero[0]) else None
    return {"voxel_count": int(volume.size), "nonzero_voxels": int(volume.size - histogram[0]),
            "nonzero_fraction": float(1 - histogram[0] / volume.size),
            "nonzero_bounds_zyx": bounds, "histogram_uint8": histogram.tolist()}


def render(volume, statistics_record, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    bounds = statistics_record["nonzero_bounds_zyx"]
    if bounds is None:
        return
    center = [int(np.median(axis)) for axis in np.nonzero(volume)]
    slices = [slice(max(0, low - 8), min(volume.shape[i], high + 9))
              for i, (low, high) in enumerate(bounds)]
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    for axis in range(3):
        axes[0, axis].imshow(np.max(volume, axis=axis), cmap="gray", vmin=0, vmax=255,
                             origin="lower", interpolation="nearest")
        axes[0, axis].set_title("Whole-grid maximum projection: axis " + str(axis))
        selection = list(slices)
        selection[axis] = center[axis]
        axes[1, axis].imshow(volume[tuple(selection)], cmap="gray", vmin=0, vmax=255,
                             origin="lower", interpolation="nearest")
        axes[1, axis].set_title("Native slice: axis %d, index %d" % (axis, center[axis]))
    for row in axes:
        for plot in row:
            plot.set_xlabel("Source index (cropped in bottom row)")
    fig.suptitle("Dryad S192803 export labelled MRI Scan: source-byte review\n"
                 "%s nonzero voxels / %s; no clinical approval" %
                 (format(statistics_record["nonzero_voxels"], ","), format(volume.size, ",")))
    fig.tight_layout()
    fig.savefig(destination, dpi=140)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--geometry-audit", type=Path)
    args = parser.parse_args()
    if args.archive.stat().st_size != EXPECTED_SIZE or digest(args.archive) != EXPECTED_SHA:
        raise ValueError("Full original archive differs from published size/SHA-256")
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "status": "source_audit_no_clinical_approval",
              "source_doi": "10.5061/dryad.zkh1893gw", "archive_sha256": EXPECTED_SHA,
              "archive_bytes": EXPECTED_SIZE, "source_geometry_changed": False,
              "diagnostic_pair_established": False, "registration_established": False,
              "volumes": {}}
    with zipfile.ZipFile(args.archive) as archive, tempfile.TemporaryDirectory(prefix="dryad-mri-audit-") as tmp:
        volumes = {}
        for key, name in SELECTION.items():
            mhd = args.output / (Path(name).name + ".mhd")
            h_info = extract_checked(args.archive, name + ".mhd", archive.getinfo(name + ".mhd"), mhd)
            meta = header(mhd)
            raw = Path(tmp) / (key + ".raw")
            raw_info = extract_checked(args.archive, name + ".raw", archive.getinfo(name + ".raw"), raw)
            if raw_info["bytes"] != int(np.prod(meta["size_xyz"])):
                raise ValueError("Header dimensions and bytes disagree")
            volumes[key] = np.memmap(raw, mode="r", dtype=np.uint8, shape=tuple(reversed(meta["size_xyz"])))
            report["volumes"][key] = {"header": meta, "header_source": h_info,
                                      "raw_source": raw_info, **statistics(volumes[key])}
        scan = volumes["scan"]
        for mask_key in (key for key in SELECTION if key != "scan"):
            for grid_key in ("size_xyz", "spacing_xyz_mm", "offset", "transform_matrix_row_major"):
                if report["volumes"][mask_key]["header"][grid_key] != report["volumes"]["scan"]["header"][grid_key]:
                    raise ValueError("Export grids differ: " + grid_key)
            report["volumes"][mask_key]["scan_nonzero_overlap_voxels"] = int(np.count_nonzero((scan != 0) & (volumes[mask_key] != 0)))
        render(scan, report["volumes"]["scan"], args.output / "mri-export-content-review.png")
        if args.geometry_audit:
            geometry = json.loads(args.geometry_audit.read_text())
            acl = next(part for part in geometry["parts"] if part["source_key"] == "ACL")
            meta = report["volumes"]["acl_mask"]["header"]
            corners = np.array(list(itertools.product(*reversed(report["volumes"]["acl_mask"]["nonzero_bounds_zyx"]))))
            matrix = np.array(meta["transform_matrix_row_major"]).reshape(3, 3)
            spacing, offset = np.array(meta["spacing_xyz_mm"]), np.array(meta["offset"])
            standard = offset + (corners * spacing) @ matrix.T
            candidate = (offset + corners * spacing) @ matrix
            report["acl_frame_comparison"] = {
                "basis": "Nonzero mask voxel centers versus smoothed source STL bounds; not a registration proof.",
                "stl_bounds": acl["bounds_native"],
                "standard_offset_plus_matrix_times_scaled_index_bounds": [standard.min(0).tolist(), standard.max(0).tolist()],
                "unvalidated_transpose_times_offset_plus_scaled_index_bounds": [candidate.min(0).tolist(), candidate.max(0).tolist()],
                "decision": "No transform adopted. Numerical proximity under another convention does not establish the documented source frame.",
            }
        del scan
        volumes.clear()
    report["limitations"] = [
        "The exported scan contains only a small nonzero region; it does not establish a complete knee MRI reference.",
        "Nominal sampling is anisotropic; source labels and dense smoothed triangles do not establish high-fidelity component anatomy.",
        "The source STL coordinate interpretation is not established by the MHD header alone.",
        "No image, mask or geometry has been repaired, resampled, fitted or promoted to clinical runtime by this audit.",
    ]
    (args.output / "imaging-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"archive_verified": True, "scan_nonzero_voxels": report["volumes"]["scan"]["nonzero_voxels"],
                      "scan_voxels": report["volumes"]["scan"]["voxel_count"],
                      "patella_overlap": report["volumes"]["patella_mask"]["scan_nonzero_overlap_voxels"],
                      "acl_overlap": report["volumes"]["acl_mask"]["scan_nonzero_overlap_voxels"],
                      "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
