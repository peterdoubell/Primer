"""Physical invariants of the three shipped dedicated physics renderers."""
import shutil
import subprocess
from pathlib import Path
import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_dedicated_physics_coordinates_obey_physical_laws():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(["node", str(root / "tools/check_physics_dedicated_models.js")],
                            cwd=root, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
