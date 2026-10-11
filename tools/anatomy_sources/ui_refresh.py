"""Follow recorded UI-only refreshes of shared front-end files.

web/app.js and web/styles.css are bound by hash into independently reviewed
radiology presentation records. data/radiology/ui-presentation-refreshes.json
records changes to those two files that left every native presentation file
byte-identical. A check that compares a reviewed hash with the current file
asks `advance` for the hash the file is expected to have now. Only the two
refreshable paths ever advance; every other file stays bound to its reviewed
hash exactly.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / 'data/radiology/ui-presentation-refreshes.json'


def load():
    return json.loads(LEDGER.read_text())


def advance(path, reviewed_sha256, ledger=None):
    """The expected current hash of `path`, following the recorded refreshes in order."""
    ledger = ledger or load()
    if path not in ledger['refreshable_paths']:
        return reviewed_sha256
    current = reviewed_sha256
    for step in ledger['refreshes']:
        change = step['files'].get(path)
        if change and change['before'] == current:
            current = change['after']
    return current
