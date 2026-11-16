"""Recover exact shared files and lesson galleries before the pelvic CT references."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/recist-pelvic-nodes/runtime-inverse.json'
PIN = 'fd74f002d505a3a20b4b9e8f7eaf363f83d3522e39e34d01a3ce11abad958e63'


def before_recist_pelvic_delivery_bytes(path, raw):
    if str(path) not in {'primer/server.py', 'primer/source_native_inspectors.py', 'vercel.json', 'web/app.js'}:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_recist_pelvic_lesson_fields(identifier, fields):
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
