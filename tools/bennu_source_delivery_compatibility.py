"""Recover only the reviewed addition of the large lesson-source static directory."""
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/bennu-sections/runtime-inverse.json'
PIN = 'b402e5f31739ae92482d461a3b8a4c9aa79c0853939953c821c7051f5df5ad47'


def before_lesson_sources_bytes(path, raw):
    if str(path) not in {'primer/server.py', 'vercel.json'}:
        return raw
    return _restore(path, raw, PROOF, PIN)
