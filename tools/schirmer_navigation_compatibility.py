"""Recover the exact pre-navigation source descriptor and shared bytes."""
from copy import deepcopy
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/schirmer-source-links-20261122/runtime-inverse.json'
PIN = 'f82bd297b4384c12d5921c42c72f8b746c1ab422678b7a7af3dd86542111508e'
PATHS = frozenset({'data/radiology/schirmer-vascular-reference.json',
                   'primer/schirmer_vascular_reference.py',
                   'web/anatomy/schirmer-vascular/viewer.js', 'web/app.js',
                   'docs/radiology-fidelity-scope.json'})


def before_schirmer_navigation_bytes(path, raw):
    from tools.segthy_runtime_compatibility import before_segthy_bytes
    raw = before_segthy_bytes(path, raw)
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_schirmer_navigation_reference_fields(identifier, fields):
    from primer.schirmer_territory_context import CASE, examples
    from primer.schirmer_vascular_reference import IDENTIFIER

    result = deepcopy(fields)
    for row in result.get('source_native_inspectors', []):
        if row.get('id') != IDENTIFIER or 'source_territory_contexts' not in row:
            continue
        if identifier != CASE or row['source_territory_contexts'] != examples():
            raise ValueError('Unreviewed vascular source navigation descriptor')
        del row['source_territory_contexts']
    return result
