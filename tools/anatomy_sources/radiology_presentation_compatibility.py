"""Exact offline UI/compatibility inverses; no historical approval extension."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
FILES = {'web/app.js': {'before': '69189a56aced8f418531721c981bc36a5eae5a08dfda019289a9cc8a8ca4ca28', 'after': 'f9753958f03a65a08cfbe9d4dfb8b80e72513761381a8fda342aabeefb11ad27', 'evidence': 'docs/radiology-image-presentation-review-20261013/exact-app-delta.json', 'evidence_sha256': '49f734e2f296cf383a52261954d5c236423878cb56c9405e7a14f2bf07ddd1b5'}, 'web/styles.css': {'before': 'b2bd335332cb0c2fbad671d9542000c544603817acbd29f55683b120f9cd3660', 'after': '677085893dee6d4d95b3573e2f1dc07944760d5782b1ff266791fd2ff51f508c', 'evidence': 'docs/radiology-image-presentation-review-20261013/exact-style-delta.json', 'evidence_sha256': 'f770625f43555aeca676e03297d53b8f963235e4f42452b62dcc789a558d79fd'}, 'tools/anatomy_sources/pulmonary_ui_compatibility.py': {'before': '47cc1421b7a245e896f6d3ea09f509bfa2cd906485733fbc3f1af20d07d5fd07', 'after': '6c5e19cfc50a11294f2e2e4918785e0cddb8701ee3b52832c2a51c5f419bc4c5', 'evidence': 'docs/radiology-image-presentation-review-20261013/tools__anatomy_sources__pulmonary_ui_compatibility.py.json', 'evidence_sha256': 'b3b933c7d1cfc33f7fe4e439addf364ae1c95bebaed31a40ed7b85916e294352'}, 'tools/anatomy_sources/ui_refresh.py': {'before': '4d0dc54125ea506ac1407ea9b0783aca82a5c125af98dbe376c3376164dcaf5c', 'after': 'eabf3dc4ecafca64c76ea58cebb8103071bfbf4bb459d129117753b26598284a', 'evidence': 'docs/radiology-image-presentation-review-20261013/tools__anatomy_sources__ui_refresh.py.json', 'evidence_sha256': '27dff02f30a79c341bd36f11398d0072e87e4f6b57ef20d8655a0f5aee489930'}, 'tools/qft_runtime_compatibility.py': {'before': '83e2851fe1a2909dcfc875286e2cf0ff5adcc79588c42a2c3d814931eca4d06d', 'after': '6b7710b3d735ea8ea98088674f8764510ecff1bee53624909ccb305704e2f12b', 'evidence': 'docs/radiology-image-presentation-review-20261013/tools__qft_runtime_compatibility.py.json', 'evidence_sha256': 'a660bd2343843278b410c6ccf2aaf71acc78d17462309a84e16120d06ab6fa82'}, 'tools/thoracic_motion_ui_compatibility.py': {'before': '12484a5157adc9bce082084bb8de0004038195b13cb9f79e2b92319c46fe56a8', 'after': 'c55e09f2f09a23e8c9f3e74f1e33a7da6a18acdf7cf7f782146ccf336119912e', 'evidence': 'docs/radiology-image-presentation-review-20261013/tools__thoracic_motion_ui_compatibility.py.json', 'evidence_sha256': '5354d2a9da0ddfd6724b21b45a15313c1f6ce2060fcc679342282ddefbc2ac3c'}, 'tools/thoracic_data_compatibility.py': {'before': '8fb4650e31c7518e901d276740dea4eb110908e60053eaae4b52a0c7930f9ad4', 'after': '8e0c63d213d23b75484510e162e55bf460ce99473bb2c635ec7dec839ae6b34f', 'evidence': 'docs/radiology-image-presentation-review-20261013/tools__thoracic_data_compatibility.py.json', 'evidence_sha256': '5006eeada6fd4b6875111a54d348fc7d4de8171113e19f2079f32598001a4f69'}}
BEFORE = FILES['web/app.js']['before']
AFTER = FILES['web/app.js']['after']
STYLE_BEFORE = FILES['web/styles.css']['before']
HELPER_PATH = 'tools/anatomy_sources/pulmonary_ui_compatibility.py'
HELPER_BEFORE = FILES[HELPER_PATH]['before']


def restore_presentation_bytes(relative, raw):
    from tools.thoracic_native_runtime_compatibility import previous_runtime_bytes
    raw = previous_runtime_bytes(relative, raw, allow_older=True)
    row = FILES.get(relative)
    sha = lambda value: hashlib.sha256(value).hexdigest()
    if not row or sha(raw) != row['after']:
        return raw
    evidence = (ROOT / row['evidence']).read_bytes()
    if sha(evidence) != row['evidence_sha256']:
        raise ValueError('UI inverse evidence changed')
    proof = json.loads(evidence)
    if (proof['path'], proof['before'], proof['after']) != (relative, row['before'], row['after']) or any(
            proof[key] is not False for key in ('clinical_approval', 'fine_anatomical_approval', 'extends_any_historical_approval')):
        raise ValueError('UI inverse leaves its exact scope')
    text = raw.decode()
    for change in reversed(proof['changes']):
        if text[change['start']:change['end']] != change['after']:
            raise ValueError('UI inverse literal bytes differ')
        text = text[:change['start']] + change['before'] + text[change['end']:]
    if sha(text.encode()) != row['before']:
        raise ValueError('UI inverse changed unrelated bytes')
    return text.encode()


def restore_presentation_app(app):
    return restore_presentation_bytes('web/app.js', app.encode()).decode()
