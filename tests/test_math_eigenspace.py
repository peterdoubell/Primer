"""Independent eigenpair and plotted-coordinate checks for the shipped helper."""
import hashlib
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_eigenpairs_subspaces_and_mounted_coordinates():
    p = subprocess.run(["node", "tools/check_math_eigenspace.js"], cwd=ROOT,
                       capture_output=True, text=True, timeout=30, check=False)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "185 eigen/projection states and 185 mounted coordinate states" in p.stdout


def test_eigenspace_helper_is_loaded_before_matrix_renderer_with_current_tags():
    from primer.server import app_shell
    html = app_shell().body.decode()
    assert html.index("/app/math-eigenspace.js") < html.index("/app/lesson-models.js")
    for name in ("math-eigenspace.js", "math-eigenspace.css"):
        digest = hashlib.sha256((ROOT / "web" / name).read_bytes()).hexdigest()[:10]
        assert "/app/" + name + "?v=" + digest in html
