"""Recover the exact prior runtime without projecting salivary source approval."""
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/salivary-ultrasound-2025/runtime-inverse.json'
PIN = '7804aadefb06c1ff946d3990a3bc2714450d548f2478592603dc24cbcc49504c'
PATHS = frozenset({'data/radiology/radiology-static-rasters.json', 'primer/server.py',
                   'primer/source_native_inspectors.py', 'web/app.js'})


def before_salivary_bytes(path, raw):
    from tools.salivary_surface_compatibility import before_surface_bytes
    raw = before_surface_bytes(path, raw)
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_salivary_bindings(bindings):
    from primer.salivary_ultrasound_reference import NECK, IDENTIFIER, references

    from tools.salivary_surface_compatibility import before_surface_bindings
    previous = before_surface_bindings(bindings)
    items = previous.get(NECK, [])
    matches = [item for item in items if item.get('id') == IDENTIFIER]
    if not matches:
        return previous
    if matches != references()[NECK]:
        raise ValueError('Unreviewed salivary source card')
    remaining = [item for item in items if item.get('id') != IDENTIFIER]
    if remaining:
        previous[NECK] = remaining
    else:
        del previous[NECK]
    return previous
