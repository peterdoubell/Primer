"""Remove only the reviewed MedSeg native CT delivery additions."""
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/medseg-liver-001/runtime-inverse.json'
PIN = '2bb4f094d570bf8ae913f8e1e2419b45e5df2f0479c4a87717bd828fc7216d6f'
PATHS = frozenset(['primer/server.py', 'vercel.json'])


def before_medseg_liver_bytes(path, raw):
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)
