"""Restore only the exact native-manuscript URL allowance for historical checks."""
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/address-drafts/hosted-runtime-inverse.json'
PIN = '86655fb37f17ab295fbfbe39991353b614118e99114741d17e8dead33b6f88ac'


def before_manuscript_native_bytes(path, raw):
    if str(path) != 'primer/curriculum.py':
        return raw
    return _restore(path, raw, PROOF, PIN)
