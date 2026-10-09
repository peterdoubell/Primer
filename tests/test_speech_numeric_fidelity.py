"""The shared reader must not turn decimal data into separate integers."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is required')
def test_real_splitter_preserves_numeric_readouts_and_chunk_limits():
    r = subprocess.run(['node','tools/check_speech_chunks.js'],cwd=ROOT,capture_output=True,text=True,timeout=20,check=False)
    assert r.returncode == 0, r.stdout+r.stderr
    assert '12 actual speech splitter cases' in r.stdout
