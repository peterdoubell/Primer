"""Supplementary movie provenance does not become VFSS/native anatomy proof."""
import copy
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/swallowing-dynamic-source-review"
SPEC = importlib.util.spec_from_file_location(
    "swallowing_movie_review", ROOT / "tools/anatomy_sources/review_swallowing_dynamic_movie.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def proof():
    return json.loads((REVIEW / "original-movie-review.json").read_text())


def test_original_identity_and_all_display_timestamps_are_complete():
    report = proof()
    MODULE.validate_report(report)
    assert report["source"]["bytes"] == 1322019
    assert report["source"]["source_XML_sha256"] == MODULE.XML_SHA256
    assert report["source"]["authors"] == [
        "Luuk Voskuilen", "Jasper Schoormans", "Oliver J. Gurney-Champion",
        "Alfons J. M. Balm", "Gustav J. Strijkers", "Ludi E. Smeele", "Aart J. Nederveen",
    ]
    assert report["source"]["license_URL"] == "https://creativecommons.org/licenses/by/4.0/"
    assert report["encoded_stream"]["codec"] == "mpeg4"
    assert report["encoded_stream"]["pixel_format"] == "yuv420p"
    assert report["encoded_stream"]["duration_fraction_seconds"] == str(Fraction(64000, 12346))
    assert report["frames"][-1]["presentation_timestamp_fraction_seconds"] == str(Fraction(63000, 12346))
    assert not report["encoded_stream"]["audio_stream_present"]


def test_complete_montage_review_derivatives_have_bound_hashes():
    report = proof()
    assert len(report["contact_sheets"]) == 4
    for i, row in enumerate(report["contact_sheets"]):
        assert row["ordinals"] == [i * 16 + 1, (i + 1) * 16]
        path = REVIEW / row["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
        with Image.open(path) as image:
            assert image.mode == "RGB" and image.size == (1600, 1520)
        assert row["review_preview_only"]
    assert not report["decoded_display"]["RGB_decodes_are_raw_MRI_intensities"]
    assert not report["decoded_display"]["additional_crop_resize_enhancement_in_frame_decodes"]


def test_visual_review_records_observations_without_assigning_physiological_boundaries():
    report = proof()
    visual = json.loads((REVIEW / "visual-review.json").read_text())
    assert visual["source_movie_sha256"] == report["source"]["sha256"]
    assert visual["all_64_decoded_frames_visually_inspected"]
    assert visual["source_montage"]["rows"] == [2, 3, 2]
    assert visual["source_montage"]["panels"] == 7
    assert not visual["source_montage"]["source_panel_to_patient_affine_reconstructed"]
    assert visual["complete_original_MRI_teaching_movie_supported"]
    for row in visual["coarse_visual_observations"]:
        assert not row["physiological_phase_boundary_established"]
        first, last = row["ordinals"]
        assert row["first_last_encoded_PTS_seconds"] == [
            report["frames"][first - 1]["presentation_timestamp_seconds_rounded"],
            report["frames"][last - 1]["presentation_timestamp_seconds_rounded"],
        ]
    assert not visual["source_MRI_is_VFSS"]
    assert not visual["native_3D_volume_or_surface_supported"]
    assert not visual["clinical_function_or_aspiration_validation_established"]
    assert not visual["anatomical_leaf_coverage_approved"]


@pytest.mark.parametrize("flag", [
    "independent_12_fps_sampling_verified", "MRI_movie_is_VFSS",
    "raw_MRI_arrays_or_patient_affine_available", "individual_age_or_sex_verified",
    "exact_physiological_phase_boundaries_verified", "normal_function_certified",
    "aspiration_absence_established", "native_3D_model_approved",
    "anatomical_leaf_coverage_approved",
])
def test_source_display_does_not_allow_clinical_or_sampling_inflation(flag):
    report = copy.deepcopy(proof())
    report["limits"][flag] = True
    with pytest.raises(AssertionError):
        MODULE.validate_report(report)


@pytest.mark.parametrize("mutation", ["missing_frame", "wrong_timestamp", "duplicate_frame", "lost_numbering_discrepancy"])
def test_incomplete_or_retimed_evidence_fails(mutation):
    report = copy.deepcopy(proof())
    if mutation == "missing_frame":
        report["frames"].pop()
    elif mutation == "wrong_timestamp":
        report["frames"][31]["presentation_timestamp_ticks"] += 1
    elif mutation == "duplicate_frame":
        report["frames"][31]["decoded_RGB_sha256"] = report["frames"][30]["decoded_RGB_sha256"]
    else:
        report["source_numbering"]["numbering_discrepancy_retained"] = False
    with pytest.raises(AssertionError):
        MODULE.validate_report(report)


@pytest.mark.parametrize("field,value", [
    ("individual_movie_subject_ID", "volunteer1"),
    ("individual_movie_age_years", 28),
    ("individual_movie_sex", "male"),
])
def test_cohort_does_not_assign_movie_identity(field, value):
    report = copy.deepcopy(proof())
    report["source_cohort"][field] = value
    with pytest.raises(AssertionError):
        MODULE.validate_report(report)


def test_user_file_paths_never_become_subprocess_arguments(tmp_path, monkeypatch):
    source = tmp_path / "-i source; --frames:v 999.mp4"
    source.write_bytes(b"original movie fixture")
    decodes = tmp_path / "https:output --ffmpeg arbitrary"
    monkeypatch.setattr(MODULE, "SOURCE_SHA256", hashlib.sha256(source.read_bytes()).hexdigest())
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: "/reviewed-tools/" + name)
    calls = []

    def check_output(command, **kwargs):
        calls.append((command, kwargs))
        assert kwargs["cwd"].is_absolute() and kwargs["cwd"] != tmp_path
        assert (kwargs["cwd"] / "original-source.mp4").read_bytes() == source.read_bytes()
        assert "shell" not in kwargs
        if command == ["/reviewed-tools/ffmpeg", "-version"]:
            return "ffmpeg reviewed fixture\n"
        assert command[0] == "/reviewed-tools/ffprobe"
        assert command[-1] == "original-source.mp4"
        return '{"probe": "fixture"}'

    def run(command, **kwargs):
        calls.append((command, kwargs))
        assert command == [
            "/reviewed-tools/ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i",
            "original-source.mp4", "-fps_mode", "passthrough", "-frames:v", "64", "frame-%03d.png",
        ]
        assert kwargs["check"] and "shell" not in kwargs
        for ordinal in range(1, 65):
            (kwargs["cwd"] / f"frame-{ordinal:03d}.png").write_bytes(f"frame {ordinal}".encode())

    monkeypatch.setattr(MODULE.subprocess, "check_output", check_output)
    monkeypatch.setattr(MODULE.subprocess, "run", run)
    probe, version = MODULE.decode_original_movie(source, decodes)
    assert probe == {"probe": "fixture"} and version == "ffmpeg reviewed fixture"
    assert len(calls) == 3
    assert len(list(decodes.glob("frame-*.png"))) == 64
    assert all((decodes / f"frame-{i:03d}.png").read_bytes() == f"frame {i}".encode() for i in range(1, 65))
    assert all(str(source) not in command and str(decodes) not in command for command, _ in calls)
    assert all(not options["cwd"].exists() for _, options in calls)


def test_unreviewed_private_movie_copy_fails_before_any_command(tmp_path, monkeypatch):
    source = tmp_path / "source.mp4"
    source.write_bytes(b"changed source")
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: "/reviewed-tools/" + name)

    def unexpected_command(*args, **kwargs):
        pytest.fail("A source digest mismatch must fail before running a tool")

    monkeypatch.setattr(MODULE.subprocess, "check_output", unexpected_command)
    monkeypatch.setattr(MODULE.subprocess, "run", unexpected_command)
    with pytest.raises(ValueError, match="private copy differs"):
        MODULE.decode_original_movie(source, tmp_path / "decodes")
