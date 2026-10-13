"""Exact offline inverse of the radiology image UI change; no approval extension."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BEFORE = '7e67a08f5a87983957418daf855069293ad6079c5375304c0dee83e1132029dc'
AFTER = '9410279e01f5813df22b50c661081f1933ed2626643af02db0f9ddd5071c699d'
DELTA = 'docs/radiology-image-presentation-review-20261013/exact-app-delta.json'
DELTA_SHA = '64bda55657dc74eda70deea5bb948089831b34fcc3d2406cd75ea27938a45802'


def restore_presentation_app(app):
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    if sha(app.encode()) != AFTER:
        return app
    raw = (ROOT / DELTA).read_bytes()
    if sha(raw) != DELTA_SHA:
        raise ValueError('Radiology presentation inverse evidence changed')
    proof = json.loads(raw)
    if proof['before_app_sha256'] != BEFORE or proof['after_app_sha256'] != AFTER or any(
            proof[key] is not False for key in ('clinical_approval', 'fine_anatomical_approval',
            'extends_any_historical_approval', 'native_decoder_mesh_CT_renderer_code_touched')):
        raise ValueError('Radiology presentation inverse leaves its exact scope')
    for change in reversed(proof['changes']):
        start, end = change['start'], change['end']
        if app[start:end] != change['after']:
            raise ValueError('Radiology presentation inverse bytes differ')
        app = app[:start] + change['before'] + app[end:]
    if sha(app.encode()) != BEFORE:
        raise ValueError('Radiology presentation inverse changed unrelated bytes')
    return app
