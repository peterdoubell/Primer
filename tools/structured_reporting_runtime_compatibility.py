"""Exact pre-structured-reporting view; never extends a native-source approval."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/structured-reporting-release-20261022/runtime-inverse.json'
PROOF_SHA256 = '13941f0dfd70716c05751470f42ae59f0b5610463b399e163b356972bb25001b'
PATHS = frozenset({'primer/server.py', 'web/app.js', 'web/index.html'})
ADDED_PATHS = frozenset({'primer/reporting_bridge.py', 'web/radiology-structured.js',
                         'web/radiology-structured.css', 'data/radiology/structured-reporting.json'})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Structured reporting compatibility evidence changed')
    proof = json.loads(raw)
    if (set(proof['files']) != PATHS or set(proof['added_files_sha256']) != ADDED_PATHS
            or proof['base_commit'] != '79622fbc2003022c5c882b7cc26893e02468c60e'
            or proof['scope'] != 'structured_reporting_forms_and_calculator_bridge_only'
            or proof['structured_form_count'] != 98
            or any(proof[key] is not False for key in ('clinical_approval', 'fine_anatomical_approval',
                'extends_historical_approval', 'native_decoder_mesh_CT_renderer_code_touched',
                'new_reporting_workflow_validated_by_this_inverse', 'canonical_lesson_data_changed'))):
        raise ValueError('Structured reporting inverse leaves its exact scope')
    return proof


def before_structured_bytes(path, raw, allow_older=False):
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # The downstream historical consumer still checks its exact hash.
        raise ValueError('Unreviewed structured reporting runtime byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('Structured reporting inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Structured reporting inverse changes unrelated bytes')
    return restored


def validate_refresh(step):
    proof = reviewed()
    row = proof['files']['web/app.js']
    if (step.get('id') != '2026-10-22-structured-reporting'
            or step.get('files') != {'web/app.js': {'before': row['before_sha256'], 'after': row['after_sha256']}}
            or step.get('scoped_compatibility_amendment') != {'path': PROOF, 'sha256': PROOF_SHA256}
            or step.get('guarded_paths_sha256') != proof['guarded_paths_sha256']
            or any(step.get(key) is not False for key in ('clinical_approval', 'fine_anatomical_approval',
                'reopens_or_extends_any_review', 'native_presentation_code_touched',
                'native_decoder_mesh_CT_renderer_code_touched'))):
        raise ValueError('Structured reporting refresh leaves its exact scope')
    for path in PATHS:
        raw = (ROOT / path).read_bytes()
        row = proof['files'][path]
        if sha(raw) != row['after_sha256'] or sha(before_structured_bytes(path, raw)) != row['before_sha256']:
            raise ValueError('Structured reporting current runtime differs')
    for path, expected in {**proof['added_files_sha256'], **proof['guarded_paths_sha256'], **proof['canonical_contract_files_sha256']}.items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('Structured reporting refresh changes a pinned or guarded file')
    return proof
