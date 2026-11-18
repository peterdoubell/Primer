"""Recover exact shared bytes before the LyNoS Pat9 reader binding."""
from pathlib import Path

from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/lynos-pat9-source-review/runtime-inverse.json'
PIN = '266c0711c367a4f8b65a3e29041ef6cb300bb852946ef655665d204fca80ae56'
PATHS = frozenset({
    'primer/server.py', 'primer/source_native_inspectors.py', 'vercel.json', 'web/app.js',
    'docs/radiology-fidelity-scope.json',
})


def before_lynos_pat9_bytes(path, raw):
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_lynos_pat9_bindings(bindings):
    from primer.lynos_pat9_reference import references

    previous = dict(bindings)
    for identifier, additions in references().items():
        if identifier not in previous:
            continue
        added_ids = {item['id'] for item in additions}
        items = previous[identifier]
        if [item for item in items if item['id'] in added_ids] != additions:
            raise ValueError('Unreviewed LyNoS source bindings')
        retained = [item for item in items if item['id'] not in added_ids]
        if retained:
            previous[identifier] = retained
        else:
            del previous[identifier]
    return previous
