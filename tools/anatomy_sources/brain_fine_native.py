"""Lossless regional native MRI, label and probability inspection for MASSP.

The crop includes every voxel of the six source lentiform selections and a
four-voxel context margin. It does not claim to include complete neighbouring
structures or the nonzero tails of every probability map.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np

from tools.anatomy_sources.massp_probability_mesh import load_verified, LABELS

REPO = Path(__file__).resolve().parents[2]
OWNER = REPO.parent.parent
ATLAS = OWNER / ".research/massp-brain"
MRI = OWNER / ".research/ahead-templates"
OUTPUT = REPO / "web/anatomy/brain-fine-massp2"
REVIEW = REPO / "docs/brain-fine-fidelity-review-20261011"
BASE = "/app/anatomy/brain-fine-massp2/"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def native_raw(array, dtype):
    return np.asarray(array, dtype=dtype).tobytes(order="F")


def xor_shuffle(raw, nx):
    words = np.frombuffer(raw, dtype="<u4").reshape(-1, nx)
    transformed = words.copy()
    transformed[:, 1:] ^= words[:, :-1]
    return np.frombuffer(transformed.astype("<u4").tobytes(), np.uint8).reshape(-1, 4).T.copy().tobytes()


def unxor_unshuffle(raw, nx):
    words = np.frombuffer(raw, np.uint8).reshape(4, -1).T.copy().view("<u4").reshape(-1, nx)
    return np.bitwise_xor.accumulate(words, axis=1).astype("<u4").tobytes()


def write_payload(name, encoded_raw, source_raw, codec):
    compressed = gzip.compress(encoded_raw, mtime=0)
    (OUTPUT / name).write_bytes(compressed)
    return {"file": BASE + name, "codec": codec, "bytes": len(compressed),
            "sha256": sha(compressed), "encoded_raw_sha256": sha(encoded_raw),
            "decoded_sha256": sha(source_raw), "decoded_bytes": len(source_raw)}


def build():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    atlas_acquisition = json.loads((ATLAS / "acquisition.json").read_text())
    all_probabilities = json.loads((ATLAS / "all-probability-acquisition.json").read_text())
    mri_acquisition = json.loads((MRI / "acquisition.json").read_text())
    if atlas_acquisition["doi"] != "10.21942/uva.27291579.v2" or mri_acquisition["doi"] != "10.21942/uva.19646364.v3":
        raise ValueError("Unexpected pinned sources")
    label_name = "ahead-massp2_avg-bestlabel_decade-18to80.nii.gz"
    label_image = load_verified(ATLAS, label_name, atlas_acquisition)
    labels = np.asarray(label_image.dataobj)
    if not np.isfinite(labels).all() or not np.equal(labels, np.rint(labels)).all():
        raise ValueError("Invalid source label values")
    if nib.aff2axcodes(label_image.affine) != ("R", "P", "S"):
        raise ValueError("Unexpected native storage directions")
    selected = np.isin(labels, list(LABELS))
    coordinates = np.argwhere(selected)
    lo, hi = coordinates.min(0) - 4, coordinates.max(0) + 5
    if np.any(lo < 0) or np.any(hi > np.array(labels.shape)):
        raise ValueError("Context margin leaves original field")
    selection = tuple(slice(a, b) for a, b in zip(lo, hi))
    shape = hi - lo
    crop_affine = label_image.affine.copy()
    crop_affine[:3, 3] = nib.affines.apply_affine(label_image.affine, lo)
    record = {"schema_version": 1, "shape": shape.tolist(), "native_roi_start": lo.tolist(),
              "native_roi_stop_exclusive": hi.tolist(), "original_shape": list(labels.shape),
              "original_affine": label_image.affine.tolist(), "affine": crop_affine.tolist(),
              "storage_axes": ["R", "P", "S"], "flat_order": "i + nx*(j + ny*k)",
              "sampling_mm": [0.5, 0.5, 0.5], "margin_native_voxels": 4,
              "source_labels": {}, "contrasts": {}, "probabilities": {}, "targets": [],
              "clinical_approval": False, "runtime_binding_added": False,
              "source_intensity_changes": False, "source_coordinate_changes": False,
              "source_label_changes": False, "source_resampling": False}
    table = (ATLAS / "massp_2p0-label-list.txt").read_text()
    table_entry = next(x for x in atlas_acquisition["files"] if x["name"] == "massp_2p0-label-list.txt")
    if sha(table.encode()) != table_entry["sha256"]:
        raise ValueError("Source label table changed")
    for line in table.splitlines()[1:]:
        if not line.strip():
            continue
        number, name, code, hemisphere = (x.strip() for x in line.split(":"))
        record["source_labels"][number] = {"name": name, "code": code, "hemisphere": hemisphere}
    record["source_labels"]["0"] = {"name": "Background", "code": "background", "hemisphere": "none"}
    crop_labels = labels[selection].astype(np.uint8)
    if not np.array_equal(crop_labels, labels[selection]):
        raise ValueError("Label transport truncates original IDs")
    raw = native_raw(crop_labels, np.uint8)
    record["labels"] = write_payload("bestlabel.u8.gz", raw, raw, "native-u8-gzip")
    record["labels"]["source_file"] = label_name
    record["labels"]["source_file_sha256"] = next(x["sha256"] for x in atlas_acquisition["files"] if x["name"] == label_name)
    original_label_bits = native_raw(labels[selection], "<f4")
    if labels.dtype != np.dtype("float32") or native_raw(crop_labels.astype("<f4"), "<f4") != original_label_bits:
        raise ValueError("Integer-label encoding cannot reconstruct original float32 bits")
    record["labels"].update({"original_source_dtype": "float32", "transport_dtype": "uint8",
        "encoding_semantics": "Lossless original integer label IDs; storage dtype changes from float32 to uint8. Decoded SHA-256 covers uint8 IDs, not original float32 storage bytes.",
        "original_float32_crop_sha256": sha(original_label_bits),
        "float32_reconstruction_bit_identical": True})
    atlas_manifest_path = REPO / "web/anatomy/massp2-subcortex/manifest.json"
    atlas_manifest = json.loads(atlas_manifest_path.read_text())
    for label, (code, side) in LABELS.items():
        native_count = int(np.count_nonzero(labels == label))
        crop_count = int(np.count_nonzero(crop_labels == label))
        if native_count != crop_count:
            raise ValueError("Source target extent was cropped")
        part_id = "massp2-" + code + "-" + side
        part = atlas_manifest["parts"][part_id]
        mesh = REPO / "web" / part["file"].removeprefix("/app/")
        if sha(mesh.read_bytes()) != part["sha256"] or part["source_label"] != label:
            raise ValueError("Existing full source mesh changed")
        points = np.argwhere(crop_labels == label)
        center = np.rint(points.mean(0)).astype(int).tolist()
        record["targets"].append({"id": part_id, "label": label, "name": part["name"], "color": part["color"],
                                   "center_indices": center, "native_selected_voxels": native_count,
                                   "crop_selected_voxels": crop_count, "complete_original_selection": True,
                                   "mesh": {key: part[key] for key in ("file", "sha256", "decoded_sha256", "vertices", "triangles", "bounds", "source_surface_sha256")}})
    for source in mri_acquisition["files"]:
        image = load_verified(MRI, source["name"], mri_acquisition)
        if image.shape != label_image.shape or not np.array_equal(image.affine, label_image.affine):
            raise ValueError("Source grids differ: no unresampled comparison")
        data = np.asarray(image.dataobj)
        crop = data[selection]
        if crop.dtype != np.dtype("float32") or not np.isfinite(crop).all():
            raise ValueError("Invalid MRI native float32 crop")
        raw = native_raw(crop, "<f4")
        encoded_raw = xor_shuffle(raw, int(shape[0]))
        if unxor_unshuffle(encoded_raw, int(shape[0])) != raw:
            raise ValueError("Lossless MRI transport changed bits")
        contrast = next(x for x in ("r1map", "r2map", "qsmap") if "_" + x + "_" in source["name"])
        stat = "med" if "_med_" in source["name"] else "iqr"
        key = stat + "-" + contrast
        payload = write_payload(key + ".f32.gz", encoded_raw, raw, "native-f32-row-xor-byte-shuffle-gzip")
        payload.update({"source_file": source["name"], "source_file_sha256": source["sha256"],
                        "statistic": stat, "contrast": contrast, "display_window": np.percentile(crop, [2, 98]).tolist(),
                        "display_window_basis": "2nd and 98th percentile of unchanged full native regional crop",
                        "source_range": [float(crop.min()), float(crop.max())], "units": "source numerical units; independent quantitative calibration unverified",
                        "exact_original_shape_and_affine_match": True, "independent_clinical_registration_approval": False})
        record["contrasts"][key] = payload
        print(key, payload["bytes"], flush=True)
    for label, code, side in [(label, *value) for label, value in LABELS.items()] + [(0, "background", None)]:
        name = ("proba_ahead-massp2_avg-background_decade-18to80_n97.nii.gz" if not label else
                f"proba_ahead-massp2_avg-{code}_hem-{side}_decade-18to80_n97.nii.gz")
        image = load_verified(ATLAS, name, all_probabilities)
        if image.shape != label_image.shape or not np.array_equal(image.affine, label_image.affine):
            raise ValueError("Probability grid differs")
        data = np.asarray(image.dataobj)
        crop = data[selection].astype("<f4")
        if not np.isfinite(crop).all() or crop.min() < 0 or crop.max() > 1:
            raise ValueError("Invalid native probability values")
        flat = np.frombuffer(native_raw(crop, "<f4"), dtype="<u4")
        codebook, codes = np.unique(flat, return_inverse=True)
        if len(codebook) > 256:
            raise ValueError("Source probability cannot use lossless uint8 dictionary")
        encoded_raw = codebook.astype("<u4").tobytes() + codes.astype(np.uint8).tobytes()
        source_raw = flat.tobytes()
        if codebook[codes].astype("<u4").tobytes() != source_raw:
            raise ValueError("Probability dictionary changed source float bits")
        payload = write_payload(f"probability-{label}.f32.gz", encoded_raw, source_raw, "native-f32-dictionary-u8-gzip")
        payload.update({"label": label, "dictionary_entries": len(codebook), "source_file": name,
                        "source_file_sha256": next(x["sha256"] for x in all_probabilities["files"] if x["name"] == name),
                        "nonzero_source_voxels": int(np.count_nonzero(data)), "nonzero_crop_voxels": int(np.count_nonzero(crop)),
                        "complete_probability_tail_extent": False, "semantics": "97-subject source population region probability, not patient confidence or MRI IQR"})
        record["probabilities"][str(label)] = payload
    record["sources"] = {"atlas": {"doi": atlas_acquisition["doi"], "subjects": 97, "age_range_years": [18, 80]},
                         "mri": {"doi": mri_acquisition["doi"], "subjects": 105, "statistics": ["median", "interquartile range"]},
                         "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
                         "authors_atlas": "Bazin, Forstmann, Alkemade and Miletic",
                         "authors_mri": "Bazin, Forstmann, Alkemade, Miletić and Isherwood"}
    record["limits"] = [
        "Adult population templates, not an individual clinical examination; 97-subject segmentation atlas and separate 105-subject MRI cohort.",
        "Equal declared source grids provide native sampling correspondence, not independent clinical registration or boundary approval.",
        "Every original voxel selected as putamen, GPe or GPi is retained, with a 2 mm regional context margin. Adjacent structures and nonzero probability tails may continue outside this crop.",
        "Source best-label IDs preserve all neighbours in the crop. Gross caudate/thalamus/capsule labels do not supply reportable segments, nuclei or limbs.",
        "Model sections use full unchanged derived joint meshes. Their subvoxel tetrahedral interpolation does not add measured resolution; medullary laminae are not separately delineated.",
        "MRI IQR describes intersubject intensity spread. Region probabilities describe source atlas population membership. Neither is patient-level diagnostic certainty.",
        "Quantitative source units, independent registration precision, full clinical boundary accuracy, pathology and developmental coverage remain unverified."]
    record["total_payload_bytes"] = sum(x["bytes"] for x in [record["labels"], *record["contrasts"].values(), *record["probabilities"].values()])
    (OUTPUT / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    (REVIEW / "native-package.json").write_text(json.dumps({"manifest_sha256": sha((OUTPUT / "manifest.json").read_bytes()),
        "native_voxels_per_array": int(np.prod(shape)), "total_payload_bytes": record["total_payload_bytes"],
        "target_source_voxels": sum(x["native_selected_voxels"] for x in record["targets"]),
        "float32_fields_bit_identical": 13, "float32_native_bit_comparisons": int(np.prod(shape)) * 13,
        "lossless_label_ID_comparisons": int(np.prod(shape)), "original_label_source_dtype": "float32",
        "label_transport_dtype": "uint8", "label_float32_reconstruction_bit_identical": True,
        "source_edits": False, "clinical_approval": False,
        "runtime_binding_added": False}, indent=2) + "\n")
    (OUTPUT / "ATTRIBUTION.md").write_text("# Source-native lentiform MRI inspection\n\n"
        "Bazin, Forstmann, Alkemade and Miletic. [MASSP 2.0 lifespan atlas v2](https://doi.org/10.21942/uva.27291579.v2). "
        "Bazin, Forstmann, Alkemade, Miletić and Isherwood. [AHEAD quantitative MRI templates v3](https://doi.org/10.21942/uva.19646364.v3). "
        "Both pinned datasets: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).\n\n"
        "Adaptations: an unresampled native regional crop; reversible bit-preserving compression; display-only grayscale windows, crosshairs and explicit labels; plane intersections of existing complete joint source meshes. "
        "No stored source intensities, probabilities, labels, coordinates or meshes are modified. Full limits and original source hashes are in manifest.json. "
        "These are adult population references, not independently validated patient boundaries.\n")
    print("total_payload_bytes", record["total_payload_bytes"], flush=True)


if __name__ == "__main__":
    build()
