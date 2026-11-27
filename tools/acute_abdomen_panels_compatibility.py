"""Restore only the recorded acute-abdomen panel links and partial source candidates."""
from pathlib import Path

from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/acute-abdomen-source-panels/inverse.json'
PIN = 'f8a7e97cb23764078d1360b24e6a4e0aee999b00d8a2a63298a5d1ea35209961'
PATHS = frozenset(['data/radiology/radiology-asset-evidence.json', 'web/app.js', 'web/radiology-structured.js', 'web/radiology/structure-atlas/index.html', 'web/radiology/structure-atlas/index.json', 'web/radiology/structure-atlas/lab.js', 'web/radiology/structure-atlas/locators/acute-abdomen.json'])


def before_liver_row_sources(path, raw):
    from tools.report_working_draft_compatibility import before_working_draft_bytes
    raw = before_working_draft_bytes(path, raw)
    if str(path) == 'web/radiology-structured.js':
        liver = PROOF.parent.parent / 'liver-report-source-navigation/inverse.json'
        raw = _restore(str(path), raw, liver, '5ef29e985dc2188d5f532a5c8957c1b80119ab5895cae16e14ad16276f309062')
    return raw


def before_acute_panel_bytes(path, raw):
    raw = before_liver_row_sources(path, raw)
    if str(path) not in PATHS:
        return raw
    return _restore(str(path), raw, PROOF, PIN)


def before_acute_panel_evidence(raw):
    return before_acute_panel_bytes('data/radiology/radiology-asset-evidence.json', raw)
