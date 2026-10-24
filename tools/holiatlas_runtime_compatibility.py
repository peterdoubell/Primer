"""Exact historical view before one separate source-template reference."""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/holiatlas-source-review-20261023/runtime-inverse.json'
PROOF_SHA256 = '8246562da1885bf915277ea2d2753afb3cadbcafe750db6086bf6d7698ee1990'
READER_SHA256 = 'afdc87a634d5927fbd95f82dc709c0c494d2a1786c83446426d2e14b2c374f2f'
RECOVERY_SHA256 = 'a42035115b127d30c691f25d70a58bf4f33f72b2e08e7eeb1928e04fd935ada3'
PRESERVATION_SHA256 = 'e1ad16619068f73e9a75a757150c680ca5c3937ec607212d710a7ba228595092'
PATHS = frozenset({'web/app.js', 'primer/server.py', 'primer/source_native_inspectors.py',
                   'vercel.json', 'docs/radiology-fidelity-scope.json'})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('holiAtlas inverse evidence changed')
    proof = json.loads(raw)
    if (set(proof['files']) != PATHS or proof['base_commit'] != 'fd43c37003a7e894df350bf6b551bd000ba35677'
            or proof['scope'] != 'one_separate_holiatlas_source_reference_and_exact_delivery_only'
            or proof['bindings'] != ['ra.brain-anatomy']
            or any(proof[k] is not False for k in ('clinical_approval', 'fine_anatomical_approval',
                'extends_historical_approval', 'new_reader_validated_by_this_inverse'))):
        raise ValueError('holiAtlas inverse leaves exact scope')
    return proof


def before_holiatlas_bytes(path, raw, allow_older=False):
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
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
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('holiAtlas recovery source differs')
    reader = json.loads(reader_raw)
    if (not reader['allPassed'] or reader['productionVerified'] or reader['clinicalApproval']
            or len(reader['cases']) != 8 or len(reader['directMeshes']) != 332 or reader['errors']):
        raise ValueError('holiAtlas current reader proof is incomplete')
    for path, expected in reader['sourceSHA256'].items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('holiAtlas current reader source differs')
    for path, expected in step['guarded_paths_sha256'].items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('holiAtlas refresh changed guarded native code')
    return reader
