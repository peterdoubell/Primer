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

STYLE_BEFORE = 'b2bd335332cb0c2fbad671d9542000c544603817acbd29f55683b120f9cd3660'
STYLE_AFTER = '677085893dee6d4d95b3573e2f1dc07944760d5782b1ff266791fd2ff51f508c'
STYLE_DELTA = 'docs/radiology-image-presentation-review-20261013/exact-style-delta.json'
STYLE_DELTA_SHA = 'e5934c6fb837cc867ca666767d3fafd34ce071cdf6d0fa205177168881c8c34f'

def restore_presentation_bytes(relative, raw):
    if relative == 'web/app.js':
        return restore_presentation_app(raw.decode()).encode()
    raw = restore_helper_bytes(relative, raw)
    if relative != 'web/styles.css' or hashlib.sha256(raw).hexdigest() != STYLE_AFTER:
        return raw
    evidence = (ROOT / STYLE_DELTA).read_bytes()
    if hashlib.sha256(evidence).hexdigest() != STYLE_DELTA_SHA:
        raise ValueError('Radiology style inverse evidence changed')
    proof = json.loads(evidence)
    if (proof['before_sha256'], proof['after_sha256']) != (STYLE_BEFORE, STYLE_AFTER) or any(
            proof[key] is not False for key in ('clinical_approval', 'fine_anatomical_approval', 'extends_any_historical_approval')):
        raise ValueError('Radiology style inverse leaves its exact scope')
    text = raw.decode()
    for change in reversed(proof['changes']):
        if text[change['start']:change['end']] != change['after']:
            raise ValueError('Radiology style inverse bytes differ')
        text = text[:change['start']] + change['before'] + text[change['end']:]
    if hashlib.sha256(text.encode()).hexdigest() != STYLE_BEFORE:
        raise ValueError('Radiology style inverse changed unrelated bytes')
    return text.encode()

HELPER_PATH = 'tools/anatomy_sources/pulmonary_ui_compatibility.py'
HELPER_AFTER = 'f8ed3040206e61a2fc3bbbea333287bc2a76e8f9913fef81420d560f5de04d59'
HELPER_BEFORE = '6b7fd6a58b90c5f4fe73421b189b568da819b4331e4ac8665c478dee6f1eefe0'
HELPER_DELTA = 'docs/radiology-image-presentation-review-20261013/exact-helper-delta.json'
HELPER_DELTA_SHA = 'c9786a543bd4cfc791a651b48d46267dc837a8ad05af0f64aa0b8e43461765c7'

def restore_helper_bytes(relative, raw):
    if relative != HELPER_PATH or hashlib.sha256(raw).hexdigest() != HELPER_AFTER:
        return raw
    evidence = (ROOT / HELPER_DELTA).read_bytes()
    if hashlib.sha256(evidence).hexdigest() != HELPER_DELTA_SHA:
        raise ValueError('Historical helper inverse evidence changed')
    proof = json.loads(evidence)
    text = raw.decode()
    for change in reversed(proof['changes']):
        if text[change['start']:change['end']] != change['after']:
            raise ValueError('Historical helper inverse bytes differ')
        text = text[:change['start']] + change['before'] + text[change['end']:]
    if hashlib.sha256(text.encode()).hexdigest() != HELPER_BEFORE:
        raise ValueError('Historical helper inverse changed unrelated bytes')
    return text.encode()
