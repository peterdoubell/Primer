"""Independent original-NIfTI comparisons against the actual JavaScript decoder."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

import nibabel as nib
import numpy as np

from tools.anatomy_sources.audit_massp_mesh_voxels import section

REPO = Path(__file__).resolve().parents[2]
OWNER = REPO.parent.parent
OUTPUT = REPO / ".research/brain-fine-runtime-decoded-20261011"
REVIEW = REPO / "docs/brain-fine-fidelity-review-20261011"


def run():
    runtime = subprocess.run(["node", str(REPO / "tools/anatomy_sources/brain_fine_check.cjs")], cwd=REPO, capture_output=True, text=True, check=True)
    node_summary = json.loads(runtime.stdout)
    manifest_path = REPO / "web/anatomy/brain-fine-massp2/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    selection = tuple(slice(a, b) for a, b in zip(manifest["native_roi_start"], manifest["native_roi_stop_exclusive"]))
    rows = []
    for payload in [manifest["labels"], *manifest["contrasts"].values(), *manifest["probabilities"].values()]:
        root = OWNER / ".research" / ("ahead-templates" if payload in manifest["contrasts"].values() else "massp-brain")
        source = root / payload["source_file"]
        if hashlib.sha256(source.read_bytes()).hexdigest() != payload["source_file_sha256"]:
            raise ValueError("Original source file changed")
        original = nib.load(source)
        if original.shape != tuple(manifest["original_shape"]) or not np.array_equal(original.affine, manifest["original_affine"]):
            raise ValueError("Original source grid changed")
        source_crop = np.asarray(original.dataobj)[selection]
        if source_crop.dtype != np.dtype("float32"):
            raise ValueError("Original source float32 storage changed")
        decoded = (OUTPUT / (Path(payload["file"]).name + ".decoded")).read_bytes()
        source_bits = source_crop.astype("<f4").tobytes(order="F")
        row = {"source_file": source.name, "compared_native_voxels": source_crop.size,
               "original_source_dtype": "float32", "runtime_decoded_sha256": hashlib.sha256(decoded).hexdigest()}
        if payload == manifest["labels"]:
            decoded_labels = np.frombuffer(decoded, dtype=np.uint8).reshape(tuple(manifest["shape"]), order="F")
            if not np.array_equal(decoded_labels, source_crop):
                raise ValueError("Decoded integer label IDs differ from original source values")
            reconstructed = decoded_labels.astype("<f4").tobytes(order="F")
            if reconstructed != source_bits:
                raise ValueError("Decoded label IDs cannot reconstruct original float32 bits, including signed zero")
            if hashlib.sha256(reconstructed).hexdigest() != payload["original_float32_crop_sha256"]:
                raise ValueError("Original reconstructed label float32 provenance changed")
            row.update({"transport_dtype": "uint8", "lossless_original_label_ID_values": True,
                "float32_reconstruction_bit_identical_including_zero_signs": True,
                "original_negative_zero_voxels": int(np.count_nonzero((source_crop == 0) & np.signbit(source_crop))),
                "original_float32_crop_sha256": hashlib.sha256(source_bits).hexdigest()})
        else:
            if decoded != source_bits:
                raise ValueError("Runtime float32 crop differs from original source bits")
            row.update({"transport_dtype": "float32", "bit_identical": True})
        rows.append(row)
    model_triangles = {}
    for target in manifest["targets"]:
        path = REPO / "web" / target["mesh"]["file"].removeprefix("/app/")
        import gzip
        data = gzip.decompress(path.read_bytes())
        signature, n, indices = struct.unpack_from("<4sII", data)
        if signature != b"BP3D":
            raise ValueError("Unexpected mesh")
        positions = np.frombuffer(data, "<f4", n * 3, 12).reshape(-1, 3).astype(float)
        faces = np.frombuffer(data, "<u4", indices, 12 + 24 * n).reshape(-1, 3)
        model_triangles[target["id"]] = positions[faces]
    sections = json.loads((OUTPUT / "runtime-sections.json").read_text())
    section_records = []
    for fixture in sections:
        horizontal, vertical = {0: (1, 2), 1: (0, 2), 2: (0, 1)}[fixture["axis"]]
        expected = section(model_triangles[fixture["id"]], fixture["axis"], fixture["coordinate"], horizontal, vertical)
        actual = np.asarray(fixture["lines"], dtype=float).reshape(-1, 2, 2)
        def canonical(lines):
            canonical = []
            for line in lines:
                p, q = line.tolist()
                canonical.append(tuple(p + q) if p < q else tuple(q + p))
            return np.array(sorted(canonical), dtype=float).reshape(-1, 4)
        expected, actual = canonical(expected), canonical(actual)
        if expected.shape != actual.shape or not np.allclose(expected, actual, rtol=0, atol=1e-12):
            raise ValueError("Runtime triangle/plane section differs from independent geometry")
        section_records.append({key: value for key, value in fixture.items() if key != "lines"} | {"segments": len(expected), "independent_match_1e-12_mm": True})
    labels = nib.load(OWNER / ".research/massp-brain" / manifest["labels"]["source_file"])
    original_labels = np.asarray(labels.dataobj)
    source_extent = []
    for target in manifest["targets"]:
        original_count = int(np.count_nonzero(original_labels == target["label"]))
        crop_count = int(np.count_nonzero(original_labels[selection] == target["label"]))
        if original_count != crop_count or original_count != target["native_selected_voxels"]:
            raise ValueError("Whole original target selection omitted")
        source_extent.append({"id": target["id"], "original_source_voxels": original_count,
                              "retained_source_voxels": crop_count, "complete_original_selection": True})
    result = {"manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
              "actual_javascript_checks": node_summary, "original_source_array_comparisons": rows,
              "whole_original_target_extent": source_extent, "independent_model_sections": section_records,
              "float32_fields_bit_identical": 13,
              "float32_native_bit_comparisons": sum(x["compared_native_voxels"] for x in rows if x.get("bit_identical")),
              "lossless_label_ID_comparisons": rows[0]["compared_native_voxels"],
              "zero_original_value_or_label_disagreements": True, "clinical_approval": False,
              "limits": "Verifies source transport, native coordinates and actual displayed geometry section algorithms. Does not independently establish anatomical accuracy, cohort registration, fine laminae or clinical coverage."}
    (REVIEW / "runtime-source-comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"arrays": len(rows), "float32_native_bit_comparisons": result["float32_native_bit_comparisons"],
                      "lossless_label_ID_comparisons": result["lossless_label_ID_comparisons"],
                      "independent_model_sections": len(section_records), "complete_target_voxels": sum(x["original_source_voxels"] for x in source_extent)}))


if __name__ == "__main__":
    run()
