"""Exact inverse of the reviewed motion-status UI change for historical evidence."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/thoracic-ultrasound-source-review-20261013/evidence/motion-ui-delta.json'
PROOF_SHA = 'feccbddf1b4a8e1f8949086d8739484690fec0c24b60936e70387b0465684dfe'
BEFORE = '7e67a08f5a87983957418daf855069293ad6079c5375304c0dee83e1132029dc'
AFTER = '69189a56aced8f418531721c981bc36a5eae5a08dfda019289a9cc8a8ca4ca28'


def restore_previous_motion_ui(app):
    raw = (ROOT / PROOF).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROOF_SHA:
        raise ValueError('Motion UI inverse proof changed')
    proof = json.loads(raw)
    if (hashlib.sha256(app.encode()).hexdigest() != AFTER
            or proof['before_sha256'] != BEFORE or proof['after_sha256'] != AFTER
            or proof['scope'] != 'sourceMotionReference_only'
            or proof['clinical_approval'] is not False
            or proof['all_other_app_bytes_unchanged'] is not True
            or app.count(proof['after_function']) != 1):
        raise ValueError('Unreviewed motion UI change')
    restored = app.replace(proof['after_function'], proof['before_function'], 1)
    if hashlib.sha256(restored.encode()).hexdigest() != BEFORE:
        raise ValueError('Motion UI inverse changes unrelated bytes')
    return restored
