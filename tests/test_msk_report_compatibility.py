"""MSK reporting cannot reuse historical receipts for arbitrary runtime changes."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools import msk_report_compatibility as bridge
from tools.anatomy_sources import ui_refresh

ROOT = Path(__file__).resolve().parents[1]


def step():
    return next(s for s in ui_refresh.load()['refreshes']
                if s['id'] == '2026-10-23-msk-anatomic-reporting')


@pytest.mark.parametrize('path', sorted(bridge.PATHS))
def test_msk_inverse_restores_exact_prior_bytes_and_rejects_unrecorded_edits(path):
    row = bridge.reviewed()['files'][path]
    from tools.holiatlas_runtime_compatibility import before_holiatlas_bytes
    raw = before_holiatlas_bytes(path, (ROOT / path).read_bytes(), allow_older=True)
    restored = bridge.before_msk_bytes(path, raw)
    from tools.all_report_compatibility import before_all_reports_bytes
    assert hashlib.sha256(before_all_reports_bytes(path, raw)).hexdigest() == row['after_sha256']
    assert hashlib.sha256(restored).hexdigest() == row['before_sha256']
    assert bridge.before_msk_bytes(path, restored) == restored
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_msk_bytes(path, raw + b'\n')
    # Earlier-view passthrough never transforms an unrecognised candidate.
    assert bridge.before_msk_bytes(path, raw + b'\n', allow_older=True) == raw + b'\n'
    assert bridge.before_msk_bytes('unrelated', b'unchanged') == b'unchanged'


def test_msk_server_inverse_runs_before_the_old_descriptor_path_filter():
    from tools.descriptor_report_compatibility import before_descriptor_bytes
    from tools.structured_reporting_runtime_compatibility import before_structured_bytes
    raw = (ROOT / 'primer/server.py').read_bytes()
    normalised = before_descriptor_bytes('primer/server.py', raw)
    assert hashlib.sha256(normalised).hexdigest() == bridge.reviewed()['files']['primer/server.py']['before_sha256']
    # The older consumer still rejects changed bytes after permissive chaining.
    with pytest.raises(ValueError, match='Unreviewed'):
        before_structured_bytes('primer/server.py', raw + b'\n')


def test_msk_refresh_keeps_all_historical_guards_and_approvals():
    proof = bridge.validate_refresh(step())
    assert set(proof['files']) == bridge.PATHS
    assert proof['base_commit'] == 'd1b98cd84c407e5f237eaf409192ca3a449db212'
    for key in bridge.FLAGS:
        assert proof[key] is False
    for path, expected in {**proof['guarded_paths_sha256'], **proof['canonical_contract_files_sha256']}.items():
        from tools.holiatlas_runtime_compatibility import before_holiatlas_bytes
        assert hashlib.sha256(before_holiatlas_bytes(path, (ROOT / path).read_bytes(), allow_older=True)).hexdigest() == expected


@pytest.mark.parametrize('key,value', [
    ('id', 'unrecorded-refresh'),
    ('clinical_approval', True),
    ('fine_anatomical_approval', True),
    ('reopens_or_extends_any_review', True),
    ('native_presentation_code_touched', True),
    ('native_decoder_mesh_CT_renderer_code_touched', True),
    ('canonical_lesson_data_changed', True),
    ('new_reporting_workflow_validated_by_this_inverse', True),
    ('native_presentation_change_scope', 'arbitrary-renderer-change'),
    ('scoped_compatibility_amendment', {'path': bridge.PROOF, 'sha256': '0' * 64}),
])
def test_msk_refresh_rejects_scope_expansion(key, value):
    candidate = copy.deepcopy(step())
    candidate[key] = value
    with pytest.raises(ValueError, match='scope'):
        bridge.validate_refresh(candidate)


@pytest.mark.parametrize('field', ['before', 'after'])
def test_msk_refresh_rejects_unrecorded_ui_transition(field):
    candidate = copy.deepcopy(step())
    candidate['files']['web/app.js'][field] = '0' * 64
    with pytest.raises(ValueError, match='scope'):
        bridge.validate_refresh(candidate)


def test_msk_refresh_rejects_changed_guard_set():
    candidate = copy.deepcopy(step())
    candidate['guarded_paths_sha256']['web/radiology-detailed-anatomy.js'] = '0' * 64
    with pytest.raises(ValueError, match='scope'):
        bridge.validate_refresh(candidate)


def test_msk_proof_bytes_are_bound_before_their_contents_are_used(tmp_path, monkeypatch):
    p = tmp_path / bridge.PROOF
    p.parent.mkdir(parents=True)
    p.write_bytes((ROOT / bridge.PROOF).read_bytes() + b'\n')
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='evidence changed'):
        bridge.reviewed()


@pytest.mark.parametrize('change', ['scope', 'base', 'paths', 'approval', 'guard', 'canonical'])
def test_msk_semantic_scope_cannot_be_rebound_with_a_changed_proof_hash(tmp_path, monkeypatch, change):
    proof = copy.deepcopy(bridge.reviewed())
    if change == 'scope':
        proof['scope'] = 'all-runtime'
    elif change == 'base':
        proof['base_commit'] = '0' * 40
    elif change == 'paths':
        proof['files']['web/radiology-detailed-anatomy.js'] = proof['files']['web/app.js']
    elif change == 'approval':
        proof['clinical_approval'] = True
    elif change == 'guard':
        proof['guarded_paths_sha256']['web/radiology-detailed-anatomy.js'] = '0' * 64
    else:
        first = next(iter(proof['canonical_contract_files_sha256']))
        proof['canonical_contract_files_sha256'][first] = '0' * 64
    raw = json.dumps(proof).encode()
    p = tmp_path / bridge.PROOF
    p.parent.mkdir(parents=True)
    p.write_bytes(raw)
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    monkeypatch.setattr(bridge, 'PROOF_SHA256', hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError, match='scope'):
        bridge.reviewed()


@pytest.mark.parametrize('side', ['before', 'after'])
def test_msk_inverse_checks_literals_and_restored_baseline(side, monkeypatch):
    proof = copy.deepcopy(bridge.reviewed())
    proof['files']['web/app.js']['changes'][0][side] += '\nchanged'
    monkeypatch.setattr(bridge, 'reviewed', lambda: proof)
    with pytest.raises(ValueError, match='literal|baseline'):
        bridge.before_msk_bytes('web/app.js', (ROOT / 'web/app.js').read_bytes())


def test_msk_packaging_inverse_preserves_the_exact_cardiac_wall_receipt():
    from tools.cardiac_wall_runtime_compatibility import before_wall_bytes, reviewed
    path = '.vercelignore'
    raw = (ROOT / path).read_bytes()
    restored = before_wall_bytes(path, raw)
    assert hashlib.sha256(restored).hexdigest() == reviewed()['files'][path]['before_sha256']
    with pytest.raises(ValueError, match='Unreviewed'):
        before_wall_bytes(path, raw + b'\nunrecorded-exclusion\n')
