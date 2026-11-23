"""Recover exact shared source views before the LyNoS station links."""
from pathlib import Path

from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/lynos-pat9-source-review/station-locator-inverse.json'
PIN = 'a337dd6bda12e3305090049f1134f912636e2b038547e02abaefb611da17c58f'
PATHS = frozenset({
    'docs/radiology-fidelity-scope.json',
    'primer/lynos_pat9_reference.py',
    'web/app.js',
    'web/radiology/structure-atlas/index.html',
    'web/radiology/structure-atlas/index.json',
    'web/radiology/structure-atlas/lab.js',
    'web/radiology/structure-atlas/locators/ct-lung-cancer.json',
    'web/radiology/structure-atlas/locators/ct-mediastinum.json',
    'web/radiology/structure-atlas/page.css',
})


def before_lynos_station_locator_bytes(path, raw):
    from tools.pulmonary_lobe_runtime_compatibility import before_pulmonary_lobe_bytes
    raw = before_pulmonary_lobe_bytes(path, raw)
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)
