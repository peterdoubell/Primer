"""Recover the reviewed state before native torso CT inspection."""
import hashlib
import json
from pathlib import Path
from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/ct-torso-s0028/runtime-inverse.json'
PIN = 'a8b4dda8d03b5c44906fbb65a5e2b0d7aa8b055b17e98e400fc31379fc0fbff2'
PATHS = frozenset(['docs/radiology-fidelity-scope.json', 'primer/curriculum.py', 'primer/module_media.py', 'primer/server.py', 'primer/source_native_inspectors.py', 'vercel.json', 'web/app.js', 'web/anatomy/segthy-001/delivery.json', 'web/anatomy/segthy-001/native-volume.mjs', 'web/anatomy/segthy-001/mesh-view.mjs'])


def before_torso_bytes(path, raw):
    from tools.source_asset_requests_compatibility import before_source_requests_bytes
    raw = before_source_requests_bytes(path, raw)
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_torso_bindings(bindings):
    from primer.ct_torso_reference import ATLAS, references
    previous = dict(bindings)
    for exam, expected in references().items():
        items = previous.get(exam, [])
        matches = [item for item in items if item['id'] == ATLAS]
        if not matches:
            continue
        if matches != expected:
            raise ValueError('Unreviewed torso CT binding')
        retained = [item for item in items if item['id'] != ATLAS]
        if retained:
            previous[exam] = retained
        else:
            del previous[exam]
    return previous


def before_torso_lesson(identifier, fields):
    if identifier not in ('rad.4.oncology-response', 'rad.5.abdominal-trauma'):
        return fields
    raw = PROOF.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Torso CT lesson evidence changed')
    row = json.loads(raw)['lessons'][identifier]
    rows = fields.get('lesson_media', [])
    matched = [item for item in rows if item['id'] == row['after']['id']]
    if not matched or (row['before'] and matched == [row['before']]):
        return fields
    if matched != [row['after']]:
        raise ValueError('Unreviewed torso CT lesson')
    media = list(rows)
    at = media.index(matched[0])
    media[at:at+1] = [row['before']] if row['before'] else []
    return dict(fields, lesson_media=media)
