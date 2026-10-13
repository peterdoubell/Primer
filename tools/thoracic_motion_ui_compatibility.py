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
    from tools.anatomy_sources.radiology_presentation_compatibility import restore_presentation_app
    app = restore_presentation_app(app)
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


def validate_refresh(step):
    if (step.get('id') != '2026-10-13-source-motion-frame-status'
            or step.get('files') != {'web/app.js': {'before': BEFORE, 'after': AFTER}}
            or step.get('scoped_compatibility_amendment') != {'path': PROOF, 'sha256': PROOF_SHA}
            or step.get('native_presentation_change_scope') != 'sourceMotionReference_only'
            or step.get('native_presentation_code_touched') is not True
            or step.get('native_decoder_mesh_CT_renderer_code_touched') is not False
            or any(step.get(k) is not False for k in ['clinical_approval', 'fine_anatomical_approval', 'reopens_or_extends_any_review'])):
        raise ValueError('Motion refresh leaves its exact scope')
    restore_previous_motion_ui((ROOT / 'web/app.js').read_text())
    for path, pin in step['guarded_paths_sha256'].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != pin:
            raise ValueError('Motion refresh changes guarded native source')
    record = step['motion_reader_smoke']
    raw = (ROOT / record['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != record['sha256']:
        raise ValueError('Motion browser evidence changed')
    proof = json.loads(raw)
    combinations = {(r['width'], r['fallback'], r['clip']) for r in proof['rows']}
    if (combinations != {(width, fallback, clip) for width in [1440, 390] for fallback in [False, True] for clip in range(6)}
            or len(proof['rows']) != 24 or proof['errors'] or proof['clinicalApproval'] is not False
            or not all(all(row[k] for k in ['playback', 'seekFirstMiddleLast', 'previousFirstDisabled', 'nextFrame']) for row in proof['rows'])):
        raise ValueError('Motion browser coverage differs')
    return proof
