import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')
def test_reader_picture_controls_and_failure_states():
    result = subprocess.run(
        ['node', str(ROOT / 'tools' / 'check_reader_pictures.js')],
        cwd=ROOT, capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'Verified reader picture names' in result.stdout
