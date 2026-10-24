"""Exact pre-MSK reporting byte view; historical source approvals are not extended."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/msk-reporting-release-20261023/runtime-inverse.json'
PROOF_SHA256 = '8336c3d0d1fdf974e822872bc054bcf0fca5c768add09c8499f45274a441a708'
BASE_COMMIT = 'd1b98cd84c407e5f237eaf409192ca3a449db212'
PATHS = frozenset({'.vercelignore', 'primer/server.py', 'primer/reporting_bridge.py', 'web/app.js',
                   'web/radiology-structured.js', 'web/radiology-structured.css'})
FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'extends_historical_approval',
         'native_decoder_mesh_CT_renderer_code_touched', 'canonical_lesson_data_changed',
         'new_reporting_workflow_validated_by_this_inverse')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('MSK reporting compatibility evidence changed')
    proof = json.loads(raw)
    from tools.structured_reporting_runtime_compatibility import reviewed as structured_reviewed
    prior = structured_reviewed()
    if (set(proof['files']) != PATHS or proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'msk_anatomic_reporting_controls_bridge_and_packaging_only'
            or proof['guarded_paths_sha256'] != prior['guarded_paths_sha256']
            or proof['canonical_contract_files_sha256'] != prior['canonical_contract_files_sha256']
            or any(proof[key] is not False for key in FLAGS)):
        raise ValueError('MSK reporting inverse leaves its exact scope')
    return proof


def before_msk_bytes(path, raw, allow_older=False):
    """Undo only the hash-bound current delta; unrelated paths are untouched.

    Historical callers may pass through earlier bytes, then check their own exact
    receipt. The direct inverse rejects all unrecorded bytes by default.
    """
    from tools.holiatlas_runtime_compatibility import before_holiatlas_bytes
    raw = before_holiatlas_bytes(path, raw, allow_older=True)
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw
        raise ValueError('Unreviewed MSK reporting runtime byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('MSK reporting inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('MSK reporting inverse changes unrelated baseline bytes')
    return restored


def validate_refresh(step):
    """Verify this UI step without approving clinical content or native anatomy."""
    proof = reviewed()
    row = proof['files']['web/app.js']
    if (step.get('id') != '2026-10-23-msk-anatomic-reporting'
            or step.get('files') != {'web/app.js': {'before': row['before_sha256'], 'after': row['after_sha256']}}
            or step.get('native_presentation_change_scope') != 'anatomic_report_choices_and_reporting_only_catalogue_entries'
            or step.get('scoped_compatibility_amendment') != {'path': PROOF, 'sha256': PROOF_SHA256}
            or step.get('guarded_paths_sha256') != proof['guarded_paths_sha256']
            or any(step.get(key) is not False for key in ('clinical_approval', 'fine_anatomical_approval',
                'reopens_or_extends_any_review', 'native_presentation_code_touched',
                'native_decoder_mesh_CT_renderer_code_touched', 'canonical_lesson_data_changed',
                'new_reporting_workflow_validated_by_this_inverse'))):
        raise ValueError('MSK reporting refresh leaves its exact scope')
    from tools.holiatlas_runtime_compatibility import before_holiatlas_bytes
    for path, row in proof['files'].items():
        raw = before_holiatlas_bytes(path, (ROOT / path).read_bytes(), allow_older=True)
        if (sha(raw) != row['after_sha256']
                or sha(before_msk_bytes(path, raw)) != row['before_sha256']):
            raise ValueError('MSK reporting current runtime differs')
    for path, expected in {**proof['guarded_paths_sha256'], **proof['canonical_contract_files_sha256']}.items():
        if sha(before_holiatlas_bytes(path, (ROOT / path).read_bytes(), allow_older=True)) != expected:
            raise ValueError('MSK reporting refresh changes a guarded source file')
    return proof
