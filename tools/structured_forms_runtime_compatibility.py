"""Recover the exact runtime bridge and build list before lossless form packing."""
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/structured-reporting-runtime/inverse.json'
PIN = '013c8a2d4ef8b47a0a05f6a83aa564ce2335a8405ecb76c8026546516d3c6cd4'


def before_structured_forms_pack_bytes(path, raw):
    if str(path) not in {'primer/reporting_bridge.py', 'vercel.json'}:
        return raw
    return _restore(path, raw, PROOF, PIN)
