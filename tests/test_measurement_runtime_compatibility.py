"""Measurement history accepts only the exact mount and one reviewed quiz delta."""
import hashlib
import json

import pytest

from tools import measurement_runtime_compatibility as bridge


@pytest.mark.parametrize('path', sorted(bridge.PATHS))
def test_each_exact_inverse_recovers_base_bytes_and_is_idempotent(path):
    raw = (bridge.ROOT / path).read_bytes()
    row = bridge.reviewed()['files'][path]
    assert hashlib.sha256(raw).hexdigest() == row['after_sha256']
    prior = bridge.before_measurement_bytes(path, raw)
    assert hashlib.sha256(prior).hexdigest() == row['before_sha256']
    assert bridge.before_measurement_bytes(path, prior) == prior
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_measurement_bytes(path, raw + b'\n')


def test_script_and_mount_are_the_only_shared_ui_changes():
    proof = bridge.reviewed()
    for path, literal in [('web/index.html', proof['script_include_literal']),
                          ('web/lesson-models.js', proof['renderer_mount_literal'])]:
        raw = (bridge.ROOT / path).read_bytes()
        assert raw.count(literal.encode()) == 1
        expected = raw.replace(literal.encode(), b'', 1)
        assert bridge.before_measurement_bytes(path, raw) == expected
        changed = raw.replace(literal.encode(), literal.replace('phys.4.experiment', 'phys.4.unreviewed')
                              .replace('measurement-lab.js', 'unreviewed-lab.js').encode(), 1)
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.before_measurement_bytes(path, changed)


def test_quiz_comparison_restores_only_three_recorded_values_and_rejects_other_edits():
    path = 'data/curriculum/03-physics.json'
    raw = (bridge.ROOT / path).read_bytes()
    current = json.loads(raw)
    before = json.loads(bridge.before_measurement_bytes(path, raw))
    changes = bridge.reviewed()['curriculum_changes']
    assert {tuple(row['path']) for row in changes} == {('nodes', 33, 'quiz', 7, key)
                                                    for key in ['prompt', 'answer', 'explain']}
    for row in changes:
        target = current
        for key in row['path'][:-1]:
            target = target[key]
        assert target[row['path'][-1]] == row['after']
        target[row['path'][-1]] = row['before']
    assert current == before
    modified = json.loads(raw)
    modified['nodes'][0]['title'] += ' unreviewed'
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_measurement_bytes(path, json.dumps(modified).encode())


def test_new_science_and_figure_evidence_are_outside_this_inverse():
    proof = bridge.reviewed()
    assert proof['new_measurement_script_science_and_reader_validated_by_this_inverse'] is False
    assert proof['extends_historical_approval'] is False
    figure = proof['figure_inverse_unchanged']
    assert hashlib.sha256((bridge.ROOT / figure['path']).read_bytes()).hexdigest() == figure['sha256']
    assert bridge.before_measurement_bytes('web/measurement-lab.js', b'unreviewed') == b'unreviewed'
    assert bridge.before_measurement_bytes('unknown', b'unreviewed') == b'unreviewed'


def test_existing_figure_reader_source_hashes_use_only_the_exact_prior_measurement_view():
    figure = bridge.reviewed()['figure_inverse_unchanged']
    inverse = json.loads((bridge.ROOT / figure['path']).read_bytes())
    reader = inverse['reader_proof']
    raw = (bridge.ROOT / reader['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == reader['sha256']
    proof = json.loads(raw)
    assert proof['productionVerified'] is False
    changed = set(proof['sourceSHA256']) & bridge.PATHS
    assert changed == {'web/index.html'}
    for path, expected in proof['sourceSHA256'].items():
        before = bridge.before_measurement_bytes(path, (bridge.ROOT / path).read_bytes())
        assert hashlib.sha256(before).hexdigest() == expected


def test_modified_inverse_evidence_cannot_restore_known_files(tmp_path, monkeypatch):
    raw = (bridge.ROOT / 'web/index.html').read_bytes()
    proof = (bridge.ROOT / bridge.PROOF).read_bytes()
    path = tmp_path / bridge.PROOF
    path.parent.mkdir(parents=True)
    path.write_bytes(proof + b'\n')
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='evidence changed'):
        bridge.before_measurement_bytes('web/index.html', raw)
