"""Recover the exact shared bytes and lesson media before the LNQ reference."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from tools.colonvessels_compatibility import _restore

PROOF = Path(__file__).resolve().parents[1] / 'docs/lnq-nodal-source-review/runtime-inverse.json'
PIN = '51698460c2b5d1abd9c9171d0877e80e4d3ac01a1e51f99eaa07891af1b3d990'
REVIEWED_FILES = frozenset({
    'primer/server.py', 'primer/source_native_inspectors.py', 'vercel.json', 'web/app.js',
    'docs/radiology-fidelity-scope.json',
})
LESSONS = frozenset({'rad.4.lung-cancer', 'rad.5.mediastinum'})


def before_lnq_nodal_bytes(path, raw):
    from tools.lynos_pat9_runtime_compatibility import before_lynos_pat9_bytes
    raw = before_lynos_pat9_bytes(path, raw)
    from tools.learning_games_compatibility import before_learning_games_bytes
    raw = before_learning_games_bytes(path, raw)
    if str(path) not in REVIEWED_FILES:
        return raw
    if str(path) == 'web/app.js':
        from tools.report_layout_compatibility import before_dictation_blanks_bytes
        raw = before_dictation_blanks_bytes(path, raw)
    return _restore(path, raw, PROOF, PIN)


def before_lnq_nodal_lesson_fields(identifier, fields):
    if identifier not in LESSONS:
        return fields
    raw = PROOF.read_bytes()
    if sha256(raw).hexdigest() != PIN:
        raise ValueError('LNQ lesson integration evidence differs')
    addition = json.loads(raw)['lessons'][identifier]
    result = deepcopy(fields)
    media = result.get('lesson_media', [])
    matches = [row for row in media if row.get('id') == addition['id']]
    if matches:
        if matches != [addition]:
            raise ValueError('Unreviewed LNQ lesson source gallery')
        media.remove(matches[0])
    return result
