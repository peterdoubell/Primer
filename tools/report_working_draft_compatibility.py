"""Recover the reviewed paste, working-editor handoff and blank-label formatting changes."""
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/report-working-draft/runtime-inverse.json'
PIN = '3fe501e4a52083d5fe6c94c32ad22078254841b80e4864d75116b94d5f254f6c'


def before_working_draft_bytes(path, raw):
    if str(path) not in {'web/app.js', 'web/radiology-structured.js'}:
        return raw
    return _restore(path, raw, PROOF, PIN)
