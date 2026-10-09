"""Independent integral/flux and actual renderer interaction checks."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_double_integral_flux_and_mounted_controls():
    result = subprocess.run(
        ["node", str(ROOT / "tools" / "check_math_field_lab.js")],
        cwd=ROOT, capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1944 rectangle states, 7776 independently integrated boundary sides" in result.stdout
    assert "29 mounted control states" in result.stdout
