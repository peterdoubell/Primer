"""Regression boundaries for the Language and Computer Science visual pass."""

from __future__ import annotations

import math
from pathlib import Path
import subprocess
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def _modules():
    sys.path.insert(0, str(TOOLS))
    try:
        from language_cs_illustrations import computer_science, core, language
    finally:
        sys.path.pop(0)
    return language, computer_science, core


def test_every_generated_language_and_cs_plate_has_a_lesson_specific_renderer():
    language, computer_science, core = _modules()

    assert len(language.SPECS) == len(language.LANGUAGE_RENDERERS) == 38
    assert len(computer_science.SPECS) == len(
        computer_science.COMPUTER_SCIENCE_RENDERERS
    ) == 31
    assert set(language.SPECS) == set(language.LANGUAGE_RENDERERS)
    assert set(computer_science.SPECS) == set(
        computer_science.COMPUTER_SCIENCE_RENDERERS
    )
    expected_ids = set(language.SPECS) | set(computer_science.SPECS)
    assert set(core.NODE_RENDERERS) == expected_ids
    assert len(expected_ids) == 69
    assert len({id(renderer) for renderer in core.NODE_RENDERERS.values()}) == 69


def test_language_cs_contact_sheet_reviews_authored_and_generated_plates(tmp_path):
    destination = tmp_path / "language-cs.webp"
    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS / "generate_language_cs_illustrations.py"),
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
        assert sheet.size == (5 * 320, math.ceil(74 / 5) * (200 + 40))
