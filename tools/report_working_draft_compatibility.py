"""Recover the reviewed paste, working-editor handoff and blank-label formatting changes."""
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/report-working-draft/runtime-inverse.json'
PIN = '25373a93bae4478439941d17774930c145e94c4a6cf02dc77907d203d3a85cf6'


def before_working_draft_bytes(path, raw):
    if str(path) not in {'web/app.js', 'web/radiology-structured.js'}:
        return raw
    return _restore(path, raw, PROOF, PIN)
