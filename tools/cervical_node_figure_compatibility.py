"""Recover the reviewed state before cervical ultrasound figure navigation."""
import hashlib
import json
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/cervical-node-ultrasound/runtime-inverse.json'
PIN = '1d91273ce1f324d9b4dee839887e668031f6cbdfb8a3e4153c1f884f03f09ef9'
PATHS = {'docs/radiology-fidelity-scope.json', 'primer/module_media.py', 'primer/server.py',
         'primer/source_native_inspectors.py', 'data/radiology/radiology-static-rasters.json',
         'tools/check_static_raster_inventory.py'}


def before_node_figure_bytes(path, raw):
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_node_figure_bindings(bindings):
    from primer.cervical_node_figures import references
    previous = dict(bindings)
    for exam, expected in references().items():
        ids = {image['id'] for image in expected}
        items = previous.get(exam, [])
        matches = [item for item in items if item['id'] in ids]
        if not matches:
            continue
        if matches != expected:
            raise ValueError('Unreviewed cervical ultrasound figure binding')
        retained = [item for item in items if item['id'] not in ids]
        if retained:
            previous[exam] = retained
        else:
            del previous[exam]
    return previous


def before_node_figure_lesson(identifier, fields):
    if identifier not in ('rad.5.paeds-masses-neuro', 'rad.5.neck-nodes'):
        return fields
    raw = PROOF.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Cervical ultrasound lesson evidence changed')
    row = json.loads(raw)['lessons'][identifier]
    rows = fields.get('lesson_media', [])
    matched = [item for item in rows if item['id'] == row['after']['id']]
    if not matched or (row['before'] and matched == [row['before']]):
        return fields
    if matched != [row['after']]:
        raise ValueError('Unreviewed cervical ultrasound lesson')
    media = list(rows)
    at = media.index(matched[0])
    media[at:at+1] = [row['before']] if row['before'] else []
    return dict(fields, lesson_media=media)
