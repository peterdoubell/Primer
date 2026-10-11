"""Actual runtime native decoder, complete geometry and provenance regressions."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "web/anatomy/brain-fine-massp2"
REVIEW = ROOT / "docs/brain-fine-fidelity-review-20261011"


def test_actual_runtime_decodes_all_source_payloads_and_checks_geometry():
    result = subprocess.run(["node", str(ROOT / "tools/anatomy_sources/brain_fine_check.cjs")],
                            cwd=ROOT, capture_output=True, text=True, check=True, timeout=90)
    checks = json.loads(result.stdout)
    assert checks["decoded_arrays"] == 14
    assert checks["complete_model_section_fixtures"] == 90
    assert checks["coordinate_checks"] == 30964
    assert checks["original_triangles"] == 329192
    assert checks["analytic_coplanar_cube_checks"] == 4
    assert checks["negative_transport_fixture_count"] == 3
    assert checks["compressed_mesh_response_checks"] == 6
    assert checks["decoded_mesh_response_checks"] == 6
    assert checks["negative_mesh_response_checks"] == 24
    assert checks["runtime_javascript_sha256"] == hashlib.sha256((FOLDER / "reference.js").read_bytes()).hexdigest()


def test_label_dtype_provenance_and_independent_original_source_comparisons():
    manifest = json.loads((FOLDER / "manifest.json").read_text())
    proof = json.loads((REVIEW / "runtime-source-comparison.json").read_text())
    label = manifest["labels"]
    assert label["original_source_dtype"] == "float32"
    assert label["transport_dtype"] == "uint8"
    assert label["float32_reconstruction_bit_identical"]
    assert label["decoded_sha256"] != label["original_float32_crop_sha256"]
    assert proof["manifest_sha256"] == hashlib.sha256((FOLDER / "manifest.json").read_bytes()).hexdigest()
    assert proof["actual_javascript_checks"]["runtime_javascript_sha256"] == hashlib.sha256((FOLDER / "reference.js").read_bytes()).hexdigest()
    assert proof["float32_fields_bit_identical"] == 13
    assert proof["float32_native_bit_comparisons"] == 12644736
    assert proof["lossless_label_ID_comparisons"] == 972672
    source_label = proof["original_source_array_comparisons"][0]
    assert source_label["lossless_original_label_ID_values"]
    assert source_label["float32_reconstruction_bit_identical_including_zero_signs"]
    assert source_label["original_negative_zero_voxels"] == 0
    assert source_label["original_float32_crop_sha256"] == label["original_float32_crop_sha256"]
    assert sum(x["bit_identical"] for x in proof["original_source_array_comparisons"] if "bit_identical" in x) == 13
    assert manifest["clinical_approval"] is False
    assert proof["clinical_approval"] is False
