"""Recover exact shared bytes before the LyNoS Pat9 reader binding."""
from pathlib import Path

from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/lynos-pat9-source-review/runtime-inverse.json'
PIN = 'd4a8f2b9537a30cfa82adaebc6cb61cae8a439f4085ca957e77fb9ce9086b646'
PATHS = frozenset({
    'primer/server.py', 'primer/source_native_inspectors.py', 'vercel.json', 'web/app.js',
    'docs/radiology-fidelity-scope.json',
})


def before_lynos_pat9_bytes(path, raw):
    from tools.lynos_station_locator_compatibility import before_lynos_station_locator_bytes
    raw = before_lynos_station_locator_bytes(path, raw)
    from tools.anatomy_sources.structure_display_names import before_structure_display_name_bytes
    raw = before_structure_display_name_bytes(path, raw)
    # The later BodyParts3D liver correction restores its own recorded lines first.
    from tools.liver_atlas_compatibility import before_liver_correction_bytes
    raw = before_liver_correction_bytes(path, raw)
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_lynos_pat9_bindings(bindings):
    from primer.lynos_pat9_reference import references

    from tools.segthy_runtime_compatibility import before_segthy_bindings

    previous = before_segthy_bindings(bindings)
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
