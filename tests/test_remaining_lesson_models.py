import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_every_remaining_curriculum_model_interacts_and_resets():
    """Execute all model renderers omitted by the physics and biology harnesses."""
    result = subprocess.run(
        ["node", str(ROOT / "tools" / "check_remaining_models.js")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        "28 models, 29 exercised control changes, 28 verified resets"
        in result.stdout
    )
    covered = {
        line.split(" = ", 1)[0].removeprefix("COVER ")
        for line in result.stdout.splitlines()
        if line.startswith("COVER ")
    }
    assert covered == {
        "arts.0.colors", "arts.1.elements", "chem.2.atoms",
        "cs.0.instructions", "cs.1.algorithms", "cs.3.data-structures",
        "cs.4.networks", "cs.5.complexity", "earth.0.sky",
        "earth.1.seasons", "hist.0.family", "hist.1.timelines",
        "lang.0.alphabet", "lang.1.reading", "math.0.counting",
        "math.0.shapes", "math.1.addition", "math.2.fractions",
        "math.2.negatives", "math.3.functions", "math.4.linalg",
        "math.5.pde", "mind.2.logic-intro", "mind.3.logic",
        "phys.0.light-shadow", "phys.1.light", "phys.4.fluids",
        "rad.3.ct-image",
    }
