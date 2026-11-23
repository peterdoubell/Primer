"""Recover exact prior pulmonary source views without extending their review."""
from copy import deepcopy
from pathlib import Path

from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/pulmonary-lobe-context-20261119/runtime-inverse.json'
PIN = '6362415b1ea6cb58291e90219593f1f9c78ef32cd04dd17b94e49b79031bea78'


def before_pulmonary_lobe_bytes(path, raw):
    from tools.schirmer_navigation_compatibility import before_schirmer_navigation_bytes
    raw = before_schirmer_navigation_bytes(path, raw)
    if str(path) not in {'primer/source_native_inspectors.py', 'web/app.js', 'docs/radiology-fidelity-scope.json'}:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_pulmonary_lobe_reference_fields(identifier, fields):
    from primer.pulmonary_lobe_reference import CASE, references

    if identifier != CASE:
        return fields
    expected, = references()[CASE]
    result = deepcopy(fields)
    entries = result.get('source_native_inspectors', [])
    matches = [item for item in entries if item.get('id') == expected['id']]
    if matches:
        if matches != [expected]:
            raise ValueError('Unreviewed pulmonary lobe source descriptor')
        entries.remove(matches[0])
    return result


def before_pulmonary_lobe_lesson_fields(identifier, fields):
    from primer.pulmonary_lobe_reference import CASE, NODE

    if identifier != NODE:
        return fields
    result = deepcopy(fields)
    if result.get('radiology_reference'):
        result['radiology_reference'] = before_pulmonary_lobe_reference_fields(CASE, result['radiology_reference'])
    for item in result.get('lesson_media', []):
        props = item.get('props', {})
        if props.get('native_inspectors'):
            previous = before_pulmonary_lobe_reference_fields(
                CASE, {'source_native_inspectors': props['native_inspectors']})
            props['native_inspectors'] = previous['source_native_inspectors']
    return result
