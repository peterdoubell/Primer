"""Recover exact shared files and lesson galleries before the pelvic CT references."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/recist-pelvic-nodes/runtime-inverse.json'
PIN = '9e0aa7638d1299ee06cbe44ac8e34f136557c666cb8deebc4c6edbe4297a7d98'


LONGITUDINAL_PROOF = PROOF.parents[1] / 'recist-pelvic-longitudinal/runtime-inverse.json'
LONGITUDINAL_PIN = '4da5d83292552bce2f22b8bb1d3e3b034d5ffabfefde22d7209743d5302a7f86'
LONGITUDINAL_PATHS = {
    'vercel.json',
    'primer/recist_pelvic_reference.py',
    'primer/server.py',
    'web/anatomy/recist-pelvic-023/delivery.json',
    'web/anatomy/recist-pelvic-viewer.js',
    'web/anatomy/recist-pelvic-viewer.css',
}


def before_recist_longitudinal_bytes(path, raw):
    if str(path) not in LONGITUDINAL_PATHS:
        return raw
    return _restore(path, raw, LONGITUDINAL_PROOF, LONGITUDINAL_PIN)


def before_recist_pelvic_delivery_bytes(path, raw):
    if str(path) == 'web/app.js':
        from tools.report_layout_compatibility import before_rich_report_format_bytes
        raw = before_rich_report_format_bytes(path, raw)
    else:
        from tools.lnq_nodal_runtime_compatibility import before_lnq_nodal_bytes
        raw = before_recist_longitudinal_bytes(path, before_lnq_nodal_bytes(path, raw))
    if str(path) not in {
        'primer/server.py', 'primer/source_native_inspectors.py', 'vercel.json', 'web/app.js',
        'docs/radiology-fidelity-scope.json', 'tests/test_pulmonary_source_delivery.py',
        'tools/check_pulmonary_delivery.py',
    }:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_recist_pelvic_lesson_fields(identifier, fields):
    from tools.lnq_nodal_runtime_compatibility import before_lnq_nodal_lesson_fields
    fields = before_lnq_nodal_lesson_fields(identifier, fields)
    if identifier not in {'rad.5.bladder-virads', 'rad.4.oncology-response'}:
        return fields
    raw = PROOF.read_bytes()
    if sha256(raw).hexdigest() != PIN:
        raise ValueError('Pelvic source integration evidence changed')
    addition = json.loads(raw)['lessons'][identifier]
    result = deepcopy(fields)
    media = result.get('lesson_media', [])
    matches = [row for row in media if row.get('id') == addition['id']]
    if matches:
        if matches != [addition]:
            raise ValueError('Unreviewed pelvic source lesson gallery')
        media.remove(matches[0])
    return result


def before_recist_pelvic_bindings(bindings):
    from tools.lynos_pat9_runtime_compatibility import before_lynos_pat9_bindings
    from primer.lnq_nodal_reference import references as lnq_references
    from primer.recist_pelvic_reference import references

    previous = before_lynos_pat9_bindings(bindings)
    additions_by_investigation = {**references(), **lnq_references()}
    for identifier, additions in additions_by_investigation.items():
        if identifier not in previous:
            continue
        added_ids = {item['id'] for item in additions}
        existing = previous[identifier]
        present = [item for item in existing if item['id'] in added_ids]
        if present != additions:
            raise ValueError('Unreviewed nodal source bindings')
        retained = [item for item in existing if item['id'] not in added_ids]
        if retained:
            previous[identifier] = retained
        else:
            del previous[identifier]
    return previous
