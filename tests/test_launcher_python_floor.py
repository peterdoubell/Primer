import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_unsupported_existing_environment_is_refused_without_changing_reader_records(tmp_path):
    shutil.copy(ROOT/'run.sh',tmp_path/'run.sh')
    bin_dir=tmp_path/'.venv/bin';bin_dir.mkdir(parents=True)
    python=bin_dir/'python';python.write_text('#!/bin/sh\nexit 1\n');python.chmod(0o755)
    content=tmp_path/'content';content.mkdir();record=content/'primer.db';record.write_bytes(b'existing reader record')
    result=subprocess.run(['bash','run.sh'],cwd=tmp_path,capture_output=True,text=True)
    assert result.returncode==1 and 'Python 3.10+' in result.stderr
    assert record.read_bytes()==b'existing reader record'
    assert not (bin_dir/'uvicorn').exists()

def test_supported_existing_environment_passes_launch_arguments(tmp_path):
    shutil.copy(ROOT/'run.sh',tmp_path/'run.sh')
    bin_dir=tmp_path/'.venv/bin';bin_dir.mkdir(parents=True)
    (bin_dir/'python').symlink_to(sys.executable)
    launcher=bin_dir/'uvicorn';launcher.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > launch-arguments.txt\n');launcher.chmod(0o755)
    result=subprocess.run(['bash','run.sh','--log-level','warning'],cwd=tmp_path,env={**os.environ,'PORT':'8891'},capture_output=True,text=True)
    assert result.returncode==0
    assert (tmp_path/'launch-arguments.txt').read_text().splitlines()==['primer.server:app','--host','127.0.0.1','--port','8891','--log-level','warning']
