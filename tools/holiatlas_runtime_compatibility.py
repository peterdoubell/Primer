"""Exact historical view before one separate source-template reference."""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/holiatlas-source-review-20261023/runtime-inverse.json'
PROOF_SHA256 = 'b3dd28e529975736ab6e96501d36adfe17784e439f5241a4970a4d84ba85e7c3'
BASE_COMMIT = 'd4b5fbefae6005d05bd90bbd56141f726fe4f83e'
LEDGER_PATH = 'data/radiology/ui-presentation-refreshes.json'
LEDGER_PROOF = 'docs/holiatlas-source-review-20261023/ledger-inverse.json'
LEDGER_PROOF_SHA256 = 'f3846f84a84ad45dc33f6e4db17bfed76e5fa70b19d8845508c1a3c663c555cf'
READER_SHA256 = '9f5ecc3aea01228cf9b580e018dac52341391ef29e7f1e8b51bf3aa73875eee4'
RECOVERY_SHA256 = '78101319e1f5c4eb70b861d0ae74ffaf0f92cc4b2e433d3b13e54c8f79d9ec90'
PRESERVATION_SHA256 = '6856b04441c161cacfe3fa1458f5d1cad52189318c37425acb5162eb014a1b1a'
PATHS = frozenset({'web/app.js', 'primer/server.py', 'primer/source_native_inspectors.py',
                   'vercel.json', 'docs/radiology-fidelity-scope.json'})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('holiAtlas inverse evidence changed')
    proof = json.loads(raw)
    if (set(proof['files']) != PATHS or proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != 'one_separate_holiatlas_source_reference_and_exact_delivery_only'
            or proof['bindings'] != ['ra.brain-anatomy']
            or any(proof[k] is not False for k in ('clinical_approval', 'fine_anatomical_approval',
                'extends_historical_approval', 'new_reader_validated_by_this_inverse'))):
        raise ValueError('holiAtlas inverse leaves exact scope')
    return proof


def reviewed_ledger():
    """Pin the ledger after its runtime-proof digest, avoiding a hash cycle."""
    raw = (ROOT / LEDGER_PROOF).read_bytes()
    if sha(raw) != LEDGER_PROOF_SHA256:
        raise ValueError('holiAtlas ledger inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT or proof['path'] != LEDGER_PATH
            or proof['scope'] != 'one_exact_holiatlas_presentation_ledger_append_only'
            or proof['source_refresh_id'] != '2026-10-23-holiatlas-source-template'
            or proof['runtime_inverse_sha256'] != PROOF_SHA256
            or any(proof[k] is not False for k in ('clinical_approval', 'fine_anatomical_approval',
                                                   'extends_historical_approval'))):
        raise ValueError('holiAtlas ledger inverse leaves exact scope')
    return proof


def before_holiatlas_bytes(path, raw, allow_older=False):
    from tools.fidelity_continuation_runtime_compatibility import before_continuation_bytes
    raw = before_continuation_bytes(path, raw, allow_older=True)
    path = str(path)
    if path not in PATHS and path != LEDGER_PATH:
        return raw
    row = reviewed_ledger() if path == LEDGER_PATH else reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # Earlier consumers retain their own exact byte guards.
        raise ValueError('Unreviewed holiAtlas byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('holiAtlas inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('holiAtlas inverse changes unrelated bytes')
    return restored


def before_holiatlas_reference_fields(identifier, fields):
    from tools.fidelity_continuation_runtime_compatibility import before_continuation_reference_fields
    fields = before_continuation_reference_fields(identifier, fields)
    if identifier != 'ra.brain-anatomy':
        return fields
    result = copy.deepcopy(fields)
    addition = reviewed()['source_inspector_addition']
    items = result.get('source_native_inspectors', [])
    matches = [item for item in items if item.get('id') == addition['id']]
    if matches:
        if matches != [addition]:
            raise ValueError('Unreviewed holiAtlas source descriptor change')
        items.remove(matches[0])
    return result


def validate_refresh(step):
    from tools.fidelity_continuation_runtime_compatibility import before_continuation_bytes
    proof = reviewed()
    row = proof['files']['web/app.js']
    if (step.get('id') != '2026-10-23-holiatlas-source-template'
            or step.get('files') != {'web/app.js': {'before': row['before_sha256'], 'after': row['after_sha256']}}
            or step.get('native_presentation_code_touched') is not True
            or step.get('native_presentation_change_scope') != 'separate_holiatlas_source_wrappers_only'
            or step.get('native_decoder_mesh_CT_renderer_code_touched') is not False
            or any(step.get(k) is not False for k in ('clinical_approval', 'fine_anatomical_approval',
                                                     'reopens_or_extends_any_review'))):
        raise ValueError('holiAtlas presentation refresh leaves exact scope')
    reader_raw = (ROOT / 'docs/holiatlas-source-review-20261023/reader/proof.json').read_bytes()
    preservation_raw = (ROOT / 'docs/holiatlas-source-review-20261023/preserved-old-spl/preservation-proof.json').read_bytes()
    if sha(reader_raw) != READER_SHA256 or sha(preservation_raw) != PRESERVATION_SHA256:
        raise ValueError('holiAtlas reader evidence changed')
    preservation = json.loads(preservation_raw)
    if not preservation['allPassed'] or len(preservation['cases']) != 2 or preservation['errors']:
        raise ValueError('Current original-source preservation is incomplete')
    recovery_raw = (ROOT / 'docs/holiatlas-source-review-20261023/reader-current-recovery-proof.json').read_bytes()
    if sha(recovery_raw) != RECOVERY_SHA256:
        raise ValueError('holiAtlas recovery evidence changed')
    recovery = json.loads(recovery_raw)
    if not recovery['allPassed'] or len(recovery['cases']) != 5:
        raise ValueError('holiAtlas current recovery evidence is incomplete')
    for path, expected in recovery['sourceSHA256'].items():
        if sha(before_continuation_bytes(path, (ROOT / path).read_bytes(), allow_older=True)) != expected:
            raise ValueError('holiAtlas recovery source differs')
    reader = json.loads(reader_raw)
    if (not reader['allPassed'] or reader['productionVerified'] or reader['clinicalApproval']
            or len(reader['cases']) != 8 or len(reader['directMeshes']) != 332 or reader['errors']):
        raise ValueError('holiAtlas current reader proof is incomplete')
    for path, expected in reader['sourceSHA256'].items():
        if sha(before_continuation_bytes(path, (ROOT / path).read_bytes(), allow_older=True)) != expected:
            raise ValueError('holiAtlas current reader source differs')
    for path, expected in step['guarded_paths_sha256'].items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('holiAtlas refresh changed guarded native code')
    return reader
