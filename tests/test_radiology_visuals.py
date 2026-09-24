"""Regression boundaries for the radiology visual-quality pass."""

from __future__ import annotations

import math
import copy
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def _radiology_modules():
    sys.path.insert(0, str(TOOLS))
    try:
        from radiology_illustrations import core, specs
        from radiology_illustrations import abdomen_breast_detail
        from radiology_illustrations import cardio_neuro_detail
        from radiology_illustrations import foundations_thorax_detail
        from radiology_illustrations import msk_paeds_nuclear_detail
    finally:
        sys.path.pop(0)
    return (
        foundations_thorax_detail,
        cardio_neuro_detail,
        abdomen_breast_detail,
        msk_paeds_nuclear_detail,
        specs,
        core,
    )


def test_biopsy_safe_arrow_stays_on_clear_side_of_target(monkeypatch):
    foundations, _, _, _, _, core = _radiology_modules()
    plate = core.RadiologyPlate("rad.5.biopsy-safety", "Biopsy", 5)
    arrows = []
    original = plate.arrow
    def capture(start, end, **kwargs):
        arrows.append((start, end, kwargs))
        return original(start, end, **kwargs)
    monkeypatch.setattr(plate, "arrow", capture)
    foundations._draw_biopsy_safety(plate, {})
    safe = [a for a in arrows if a[2].get("fill") == foundations.GREEN]
    assert len(safe) == 1
    start, end, _ = safe[0]
    # The vessel and bowel are left of x=335; the clear right-hand route
    # remains right of them for its whole straight segment.
    assert min(start[0], end[0]) > 335
    assert start[0] > end[0]


def test_vascular_diameters_exclude_plaque(monkeypatch):
    _, cardio, _, _, _, core = _radiology_modules()
    measurements = []
    original = cardio._measure

    def capture(plate, start, end, label, *args, **kwargs):
        measurements.append((start, end, label))
        return original(plate, start, end, label, *args, **kwargs)

    monkeypatch.setattr(cardio, "_measure", capture)
    for identifier, renderer, label, open_height in (
        ("rad.5.coronary-ct", cardio._draw_coronary_ct, "Dmin", 38),
        ("rad.5.peripheral-vascular", cardio._draw_peripheral_vascular,
         "normal plane", 52),
    ):
        measurements.clear()
        renderer(core.RadiologyPlate(identifier, "Measurement", 5), {})
        start, end, _ = next(m for m in measurements if m[2] == label)
        assert start[0] == end[0]  # orthogonal to horizontal vessel
        # Exclude the plaque depth, not the entire outer vessel diameter.
        assert end[1] - start[1] == open_height

    measurements.clear()
    cardio._draw_tavi_ct(core.RadiologyPlate("rad.5.tavi-ct", "TAVI", 5), {})
    start, end, _ = next(m for m in measurements if m[2] == "minimum lumen")
    assert start[1] == end[1]
    assert end[0] - start[0] == 58  # inset lumen, not 116px outer wall


def test_msk_heading_badges_fit_actual_bold_text(monkeypatch):
    _, _, _, msk, _, core = _radiology_modules()
    plate = core.RadiologyPlate("rad.5.msk-mri", "Heading dimensions", 5)
    boxes = []
    original = plate.draw.rounded_rectangle

    def capture(box, **kwargs):
        boxes.append(box)
        return original(box, **kwargs)

    monkeypatch.setattr(plate.draw, "rounded_rectangle", capture)
    for label in ("STRUCTURAL INJURY", "REACTIVE OEDEMA", "1  CLINICAL RULE"):
        msk._tag(plate, (800, 195), label, msk.BLUE)
        width = plate.draw.textlength(label, font=msk.font(21, bold=True))
        assert boxes[-1][2] - boxes[-1][0] >= width + 35


def test_every_generated_radiology_plate_has_a_lesson_specific_renderer():
    """No generator-owned clinical plate may use the generic fallback layout."""
    foundations, cardio_neuro, abdomen_breast, msk_paeds, specs, core = (
        _radiology_modules()
    )
    from radiology_illustrations.reference_expansion import RENDERERS as reference_renderers
    cohorts = (
        (foundations.RENDERERS, 18),
        (cardio_neuro.RENDERERS, 24),
        (abdomen_breast.RENDERERS, 22),
        (msk_paeds.RENDERERS, 19),
        (reference_renderers, 12),
    )

    expected_ids = set()
    renderers = []
    for cohort, expected_count in cohorts:
        assert len(cohort) == expected_count
        assert expected_ids.isdisjoint(cohort)
        expected_ids.update(cohort)
        renderers.extend(cohort.values())

    assert len(expected_ids) == 95
    assert expected_ids == set(specs.SPECS)
    assert expected_ids == set(specs.RADIOLOGY_RENDERERS)
    assert expected_ids == set(core.NODE_RENDERERS)
    assert len({id(renderer) for renderer in renderers}) == 95


def test_radiology_contact_sheet_reviews_authored_and_generated_plates(tmp_path):
    """The visual audit sheet includes the preserved CT plate and all new work."""
    destination = tmp_path / "radiology.webp"
    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS / "generate_radiology_illustrations.py"),
            "--contact-sheet",
            str(destination),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert destination.is_file()
    with Image.open(destination) as sheet:
        assert sheet.size == (5 * 320, math.ceil(96 / 5) * (200 + 38))


def test_clinical_plate_sync_preserves_nonclinical_foundations(tmp_path, monkeypatch):
    """A clinical-only generator must still save the complete field document."""
    sys.path.insert(0, str(TOOLS))
    try:
        import generate_radiology_illustrations as generator
    finally:
        sys.path.pop(0)
    curriculum = generator.load_curriculum()
    foundation = {
        "id": "img.0.sync-preservation", "stage": 0,
        "title": "A nonclinical fixture", "lesson": {"overview": "Keep this lesson."},
        "lesson_media": [{"kind": "illustration", "id": "foundation-owned"}],
    }
    curriculum["nodes"].append(copy.deepcopy(foundation))
    expected_foundations = [copy.deepcopy(node) for node in curriculum["nodes"]
                            if not node["id"].startswith("rad.")]
    specs = generator.bound_specs(curriculum)
    assert len(generator.clinical_nodes(curriculum)) == 96
    # Force a real write by removing one generator-owned clinical illustration.
    selected = next(node for node in curriculum["nodes"] if node["id"] in specs)
    selected["lesson_media"] = [item for item in selected["lesson_media"]
                                if item["kind"] != "illustration"]
    destination = tmp_path / "radiology.json"
    monkeypatch.setattr(generator, "CURRICULUM_PATH", destination)
    assert generator.sync_curriculum(curriculum, specs) >= 1
    saved = json.loads(destination.read_text())
    assert [node for node in saved["nodes"] if not node["id"].startswith("rad.")] == expected_foundations
