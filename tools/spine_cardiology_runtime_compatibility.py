"""Exact inverse for additive spine/cardiology references; no approval extension."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/spine-cardiology-release-20261022/runtime-inverse.json'
PROOF_SHA256 = 'eb7b2192251cd23ca5e642914ca799a217e5eff8189a9af9dbb22431715b66e8'
PATHS = frozenset({'web/app.js', 'web/styles.css', 'primer/radiology_catalog.py'})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Spine/cardiology compatibility evidence changed')
    data = json.loads(raw)
    if (set(data['files']) != PATHS or data['base_commit'] != '97acb71e612b47f87699ce0be7a4570c1c20b8ce'
            or data['scope'] != 'spine_neurology_and_cardiology_reference_additions_only'
            or any(data[k] is not False for k in ['clinical_approval', 'fine_anatomical_approval',
                'extends_historical_approval', 'native_decoder_mesh_CT_renderer_code_touched'])):
        raise ValueError('Spine/cardiology inverse leaves its exact scope')
    return data


def before_reference_bytes(path, raw, allow_older=False):
    from tools.structured_reporting_runtime_compatibility import before_structured_bytes
    raw = before_structured_bytes(path, raw, allow_older=True)
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # Earlier consumers still validate their own exact fingerprints.
        raise ValueError('Unreviewed spine/cardiology runtime byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('Spine/cardiology inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Spine/cardiology inverse changes unrelated bytes')
    return restored


def validate_refresh(step):
    proof = reviewed()
    expected = {path: {'before': row['before_sha256'], 'after': row['after_sha256']}
                for path, row in proof['files'].items() if path.startswith('web/')}
    if (step.get('id') != '2026-10-22-spine-cardiology-references'
            or step.get('files') != expected
            or step.get('scoped_compatibility_amendment') != {'path': PROOF, 'sha256': PROOF_SHA256}
            or any(step.get(k) is not False for k in ['clinical_approval', 'fine_anatomical_approval',
                'reopens_or_extends_any_review', 'native_presentation_code_touched',
                'native_decoder_mesh_CT_renderer_code_touched'])):
        raise ValueError('Spine/cardiology refresh leaves its exact scope')
    for path in PATHS:
        row = proof['files'][path]
        from tools.structured_reporting_runtime_compatibility import before_structured_bytes
        raw = before_structured_bytes(path, (ROOT / path).read_bytes(), allow_older=True)
        if sha(raw) != row['after_sha256'] or sha(before_reference_bytes(path, raw)) != row['before_sha256']:
            raise ValueError('Spine/cardiology current runtime differs')
    for path, expected_sha in step['guarded_paths_sha256'].items():
        if sha((ROOT / path).read_bytes()) != expected_sha:
            raise ValueError('Spine/cardiology refresh changes guarded native source')
    return proof
