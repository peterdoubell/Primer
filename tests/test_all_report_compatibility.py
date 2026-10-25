"""All-report changes cannot extend or silently bypass historical receipts."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from tools import all_report_compatibility as bridge
from tools.holiatlas_runtime_compatibility import LEDGER_PATH, before_holiatlas_bytes

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize('path', sorted(bridge.PATHS))
def test_expansion_inverse_is_exact_idempotent_and_rejects_unrecorded_changes(path):
    row = bridge.reviewed()['files'][path]
    raw = before_holiatlas_bytes(path, (ROOT / path).read_bytes(), allow_older=True)
    assert sha(raw) == row['after_sha256']
    restored = bridge.before_all_reports_bytes(path, raw)
    assert sha(restored) == row['before_sha256']
    assert bridge.before_all_reports_bytes(path, restored) == restored
    assert row['changes'] and row['before_sha256'] != row['after_sha256']
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_all_reports_bytes(path, raw + b'\nunrecorded-change\n')
    assert bridge.before_all_reports_bytes(path, raw + b'\n', allow_older=True) == raw + b'\n'
    assert bridge.before_all_reports_bytes('unrelated-file', b'preserved') == b'preserved'


def test_composition_inverse_runs_before_the_msk_path_filter():
    from tools.msk_report_compatibility import PATHS, before_msk_bytes
    path = 'primer/descriptor_reporting.py'
    assert path not in PATHS
    restored = before_msk_bytes(path, (ROOT / path).read_bytes())
    assert sha(restored) == bridge.reviewed()['files'][path]['before_sha256']


def test_packaging_chain_preserves_the_actual_cardiac_wall_receipt():
    from tools.cardiac_wall_runtime_compatibility import before_wall_bytes, reviewed
    path = '.vercelignore'
    restored = before_wall_bytes(path, (ROOT / path).read_bytes())
    assert sha(restored) == reviewed()['files'][path]['before_sha256']
    with pytest.raises(ValueError, match='Unreviewed'):
        before_wall_bytes(path, (ROOT / path).read_bytes() + b'\nunrecorded-package-exclusion\n')


def test_standalone_proof_does_not_create_an_empty_native_ui_ledger_step():
    proof = bridge.validate_current()
    assert proof['base_commit'] == 'fd43c37003a7e894df350bf6b551bd000ba35677'
    assert proof['ui_presentation_ledger_changed'] is False
    assert set(proof['files']) == bridge.PATHS
    assert set(proof['added_files_sha256']) == {'primer/descriptor_calculations.py'}
    assert set(proof['unchanged_runtime_sha256']) == bridge.UNCHANGED_PATHS
    assert all(proof[flag] is False for flag in bridge.FLAGS)
    ledger = json.loads(before_holiatlas_bytes(LEDGER_PATH, (ROOT / LEDGER_PATH).read_bytes()))
    assert ledger['refreshes'][-1]['id'] == '2026-10-23-msk-anatomic-reporting'
    assert not any(step['id'] == '2026-10-23-all-anatomic-reporting' for step in ledger['refreshes'])
    for path in ('web/app.js', 'web/styles.css'):
        assert sha(before_holiatlas_bytes(path, (ROOT / path).read_bytes(), allow_older=True)) == proof['unchanged_runtime_sha256'][path]


def test_proof_bytes_are_checked_before_contents_are_used(tmp_path, monkeypatch):
    path = tmp_path / bridge.PROOF
    path.parent.mkdir(parents=True)
    path.write_bytes((ROOT / bridge.PROOF).read_bytes() + b'\n')
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='evidence changed'):
        bridge.reviewed()


@pytest.mark.parametrize('change', ['scope', 'base', 'paths', 'added', 'unchanged', 'ledger', 'approval', 'guard', 'canonical'])
def test_semantic_scope_cannot_be_rebound_by_changing_proof_hash(tmp_path, monkeypatch, change):
    proof = copy.deepcopy(bridge.reviewed())
    if change == 'scope':
        proof['scope'] = 'all-runtime'
    elif change == 'base':
        proof['base_commit'] = '0' * 40
    elif change == 'paths':
        proof['files']['web/radiology-detailed-anatomy.js'] = proof['files']['web/radiology-structured.js']
    elif change == 'added':
        proof['added_files_sha256']['unreviewed.py'] = '0' * 64
    elif change == 'unchanged':
        del proof['unchanged_runtime_sha256']['web/app.js']
    elif change == 'ledger':
        proof['ui_presentation_ledger_changed'] = True
    elif change == 'approval':
        proof['clinical_approval'] = True
    elif change == 'guard':
        proof['guarded_paths_sha256']['web/radiology-detailed-anatomy.js'] = '0' * 64
    else:
        first = next(iter(proof['canonical_contract_files_sha256']))
        proof['canonical_contract_files_sha256'][first] = '0' * 64
    raw = json.dumps(proof).encode()
    path = tmp_path / bridge.PROOF
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    monkeypatch.setattr(bridge, 'PROOF_SHA256', sha(raw))
    with pytest.raises(ValueError, match='scope'):
        bridge.reviewed()


@pytest.mark.parametrize('side', ['before', 'after'])
def test_inverse_checks_literal_delta_and_restored_baseline(side, monkeypatch):
    proof = copy.deepcopy(bridge.reviewed())
    proof['files']['web/radiology-structured.js']['changes'][0][side] += '\nchanged'
    monkeypatch.setattr(bridge, 'reviewed', lambda: proof)
    with pytest.raises(ValueError, match='literal|baseline'):
        bridge.before_all_reports_bytes('web/radiology-structured.js', (ROOT / 'web/radiology-structured.js').read_bytes())


@pytest.mark.parametrize(('path', 'message'), [
    ('web/radiology-structured.js', 'current runtime'),
    ('primer/reporting_bridge.py', 'current runtime'),
    ('primer/server.py', 'current runtime'),
    ('primer/descriptor_calculations.py', 'added runtime'),
    ('web/app.js', 'unchanged or guarded'),
    ('data/radiology/ui-presentation-refreshes.json', 'unchanged or guarded'),
    ('web/radiology-detailed-anatomy.js', 'unchanged or guarded'),
    ('primer/radiology.py', 'unchanged or guarded'),
])
def test_validation_rejects_changed_current_added_unchanged_and_guarded_files(tmp_path, monkeypatch, path, message):
    proof = bridge.reviewed()
    paths = {bridge.PROOF, *proof['files'], *proof['added_files_sha256'],
             *proof['unchanged_runtime_sha256'], *proof['guarded_paths_sha256'],
             *proof['canonical_contract_files_sha256']}
    for name in paths:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    target = tmp_path / path
    target.write_bytes(target.read_bytes() + b'\nunrecorded-drift\n')
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match=message):
        bridge.validate_current()


@pytest.mark.parametrize('flag', bridge.FLAGS)
def test_no_historical_approval_flag_can_be_rebound(tmp_path, monkeypatch, flag):
    proof = copy.deepcopy(bridge.reviewed())
    proof[flag] = True
    raw = json.dumps(proof).encode()
    path = tmp_path / bridge.PROOF
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    monkeypatch.setattr(bridge, 'PROOF_SHA256', sha(raw))
    with pytest.raises(ValueError, match='scope'):
        bridge.reviewed()
