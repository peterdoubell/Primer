"""Recover the reviewed state before salivary surface and section navigation."""
import hashlib
import json
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/zanatomy-salivary/runtime-inverse.json'
PIN = 'f9a1bc660950e084195401095e861882f9943b632c8528a34b0b33d69bbb5542'
PATHS = {'docs/radiology-fidelity-scope.json', 'primer/module_media.py', 'primer/server.py',
         'primer/source_native_inspectors.py', 'vercel.json', 'web/app.js', 'tests/test_spl_additional_reference.py'}


def before_surface_bytes(path, raw):
    from tools.ct_torso_compatibility import before_torso_bytes
    raw = before_torso_bytes(path, raw)
    from tools.structured_forms_runtime_compatibility import before_structured_forms_pack_bytes
    raw = before_structured_forms_pack_bytes(path, raw)
    from tools.bennu_source_delivery_compatibility import before_lesson_sources_bytes
    raw = before_lesson_sources_bytes(path, raw)
    from tools.acute_abdomen_panels_compatibility import before_acute_panel_bytes
    raw = before_acute_panel_bytes(path, raw)
    from tools.cervical_node_figure_compatibility import before_node_figure_bytes
    raw = before_node_figure_bytes(path, raw)
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_surface_bindings(bindings):
    from primer.salivary_surface_reference import ATLAS, references
    from tools.cervical_node_figure_compatibility import before_node_figure_bindings
    from tools.ct_torso_compatibility import before_torso_bindings
    previous = before_node_figure_bindings(before_torso_bindings(bindings))
    for exam, expected in references().items():
        items = previous.get(exam, [])
        matches = [item for item in items if item['id'] == ATLAS]
        if not matches:
            continue
        if matches != expected:
            raise ValueError('Unreviewed salivary surface binding')
        retained = [item for item in items if item['id'] != ATLAS]
        if retained:
            previous[exam] = retained
        else:
            del previous[exam]
    return previous


def before_surface_lesson(identifier, fields):
    from tools.cervical_node_figure_compatibility import before_node_figure_lesson
    from tools.ct_torso_compatibility import before_torso_lesson
    fields = before_node_figure_lesson(identifier, before_torso_lesson(identifier, fields))
    if identifier not in ('rad.5.deep-neck-spaces', 'rad.5.neck-nodes'):
        return fields
    raw = PROOF.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Salivary surface lesson evidence changed')
    row = json.loads(raw)['lessons'][identifier]
    rows = fields.get('lesson_media', [])
    matched = [item for item in rows if item['id'] == row['after']['id']]
    if not matched or (row['before'] and matched == [row['before']]):
        return fields
    if matched != [row['after']]:
        raise ValueError('Unreviewed salivary surface lesson')
    media = list(rows)
    at = media.index(matched[0])
    media[at:at+1] = [row['before']] if row['before'] else []
    return dict(fields, lesson_media=media)
