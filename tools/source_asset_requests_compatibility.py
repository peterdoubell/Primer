"""Recover only the reviewed source request transport changes for prior checks."""
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/source-asset-requests/runtime-inverse.json'
PIN = '7f5142f38ce0a9460c62d51505c71dd418da3035c8fbccc32be5e0eca5d3877c'


def before_source_requests_bytes(path, raw):
    if str(path) not in {'web/anatomy/segthy-001/native-volume.mjs', 'web/anatomy/segthy-001/delivery.json'}:
        return raw
    return _restore(path, raw, PROOF, PIN)
