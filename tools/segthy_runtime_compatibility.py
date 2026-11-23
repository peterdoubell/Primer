"""Restore each shared file only from its verified SegThy integration revision."""
from hashlib import sha256
import json
from pathlib import Path

from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/segthy-ultrasound/runtime-inverse.json'
PIN = 'ac73ee0cac7a121f013d878b8b95c8c43f34a5eb3098f000ab8878b6c864b5a1'
PATHS = frozenset(['docs/radiology-fidelity-scope.json', 'primer/module_media.py', 'primer/server.py', 'primer/source_native_inspectors.py', 'vercel.json', 'web/app.js'])


def before_segthy_bytes(path, raw):
    from tools.salivary_ultrasound_compatibility import before_salivary_bytes
    raw = before_salivary_bytes(path, raw)
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_segthy_bindings(bindings):
    from primer.segthy_reference import NECK, THYROID, study as segthy_study

    from tools.salivary_ultrasound_compatibility import before_salivary_bindings
    previous = before_salivary_bindings(bindings)
    for identifier in (THYROID, NECK):
        items = previous.get(identifier, [])
        matches = [item for item in items if item['id'] == 'segthy-001']
        if not matches:
            continue
        if matches != [segthy_study()]:
            raise ValueError('Unreviewed SegThy source binding')
        remaining = [item for item in items if item['id'] != 'segthy-001']
        if remaining:
            previous[identifier] = remaining
        else:
            del previous[identifier]
    return previous


def before_segthy_lesson_fields(identifier, fields):
    from tools.salivary_surface_compatibility import before_surface_lesson
    fields = before_surface_lesson(identifier, fields)
    if identifier != 'rad.5.thyroid-tirads':
        return fields
    media = fields.get('lesson_media', [])
    additions = [row for row in media if row.get('id') == 'module-native-inspectors-rad.5.thyroid-tirads']
    if not additions:
        return fields
    if len(additions) != 1 or sha256(json.dumps(additions[0], sort_keys=True, separators=(',', ':')).encode()).hexdigest() != 'a737fc8b2435fbb32436c6b421084079b58debb4e98a70ed3efefe62c1950178':
        raise ValueError('Unreviewed thyroid source lesson gallery')
    return dict(fields, lesson_media=[row for row in media if row is not additions[0]])
