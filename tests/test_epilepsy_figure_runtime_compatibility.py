"""The six-figure historical view cannot hide changed source or unrelated data."""
import copy
import hashlib
import json

import pytest

from tools import epilepsy_figure_runtime_compatibility as bridge
from tools.check_radiology_fidelity import digest


@pytest.mark.parametrize('path', sorted(bridge.PATHS))
def test_exact_byte_inverse_recovers_base_and_rejects_unrecorded_bytes(path):
    row = bridge.reviewed()['files'][path]
    raw = (bridge.ROOT / path).read_bytes()
    restored = bridge.before_figure_bytes(path, raw)
    assert hashlib.sha256(restored).hexdigest() == row['before_sha256']
    assert bridge.before_figure_bytes(path, restored) == restored
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_figure_bytes(path, raw + b'\n')


def test_only_exact_source_gallery_is_removed_from_the_observed_lesson():
    from primer.curriculum import Curriculum
    fields = ['goal', 'learning_outcomes', 'lesson', 'reference', 'radiology_reference', 'visual_spec',
              'lesson_media', 'model_family', 'model_context', 'practice', 'quiz', 'kid_text']
    node = Curriculum().node(bridge.MODULE)
    current = {key: node.get(key) for key in fields}
    record = bridge.reviewed()['lesson']
    assert digest(current) == record['after_sha256']
    original = copy.deepcopy(current)
    prior = bridge.before_figure_lesson_fields(bridge.MODULE, current)
    assert current == original and digest(prior) == record['before_sha256']
    assert bridge.before_figure_lesson_fields(bridge.MODULE, prior) == prior
    current['unrelated'] = 'retain'
    assert bridge.before_figure_lesson_fields(bridge.MODULE, current)['unrelated'] == 'retain'
    next(item for item in current['lesson_media'] if item['id'] == record['added_media']['id'])['clinical_approval'] = True
    with pytest.raises(ValueError, match='companion'):
        bridge.before_figure_lesson_fields(bridge.MODULE, current)


@pytest.mark.parametrize('path', [
    'data/radiology/radiology-open-images.json', 'data/radiology/radiology-asset-evidence.json',
    'data/radiology/reporting-steps/neuroradiology.json'])
def test_semantic_inverse_preserves_unknown_records_and_rejects_changed_added_records(path):
    record = bridge.reviewed()['data_values'][path]
    data = json.loads((bridge.ROOT / path).read_bytes())
    if record['kind'] == 'added_array_records':
        tokens = {'assets:' + key: value for key, value in record['raw_token_sha256'].items()}
        data['assets'].append({'id': 'unreviewed-figure', 'unverified_claim': True})
        tokens['assets:unreviewed-figure'] = 'f' * 64
        target = next(row for row in data['assets'] if row['id'] in bridge.FIGURES)
    else:
        tokens = {record['token_keys'][0]: record['after_raw_token_sha256']}
        data['unrelated'] = 'retain'
        target = data[record['key']][0] if record['kind'] == 'added_mapping' else data[record['field']][record['key']]
    original = copy.deepcopy(data)
    prior, prior_tokens = bridge.restore_prior_view(path, data, tokens)
    assert data == original
    if record['kind'] == 'added_array_records':
        assert prior['assets'][-1] == data['assets'][-1]
        assert prior_tokens == {'assets:unreviewed-figure': 'f' * 64}
    else:
        assert prior['unrelated'] == 'retain'
    target['unreviewed_claim'] = True
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.restore_prior_view(path, data, tokens)
    bad_tokens = dict(tokens)
    bad_tokens[next(key for key in tokens if 'unreviewed-figure' not in key)] = '0' * 64
    with pytest.raises(ValueError, match='raw value token'):
        bridge.restore_prior_view(path, original, bad_tokens)


def test_record_and_token_omissions_duplicates_and_ambiguous_namespaces_are_rejected():
    proof = bridge.reviewed()
    path = 'data/radiology/radiology-open-images.json'
    row = proof['data_values'][path]
    data = json.loads((bridge.ROOT / path).read_bytes())
    tokens = {key: row['after_raw_token_sha256'] for key in row['token_keys']}
    with pytest.raises(ValueError, match='ambiguous'):
        bridge.restore_prior_view(path, data, tokens)
    with pytest.raises(ValueError, match='missing'):
        bridge.restore_prior_view(path, data, {})
    path = 'data/radiology/radiology-asset-evidence.json'
    row = proof['data_values'][path]
    data = json.loads((bridge.ROOT / path).read_bytes())
    tokens = {'assets:' + key: value for key, value in row['raw_token_sha256'].items()}
    position = next(i for i, item in enumerate(data['assets']) if item['id'] in bridge.FIGURES)
    for duplicate in [False, True]:
        changed = copy.deepcopy(data)
        if duplicate:
            changed['assets'].append(copy.deepcopy(changed['assets'][position]))
        else:
            changed['assets'].pop(position)
        with pytest.raises(ValueError, match='omission or duplicate'):
            bridge.restore_prior_view(path, changed, tokens)


def test_exact_contract_views_reject_other_changes_and_keep_unknown_contracts():
    row = bridge.reviewed()['contract']
    current = copy.deepcopy(row['after'])
    assert bridge.restore_prior_contract(bridge.CASE, current) == row['before']
    assert current == row['after']
    current['reading'].append({'unreviewed': True})
    with pytest.raises(ValueError, match='effective contract'):
        bridge.restore_prior_contract(bridge.CASE, current)
    hashes = {bridge.CASE: row['after_sha256'], 'unrelated': 'f' * 64}
    assert bridge.restore_prior_contracts(hashes) == {bridge.CASE: row['before_sha256'], 'unrelated': 'f' * 64}
    hashes[bridge.CASE] = '0' * 64
    with pytest.raises(ValueError, match='effective contract'):
        bridge.restore_prior_contracts(hashes)


def test_unknown_paths_get_no_waiver_and_modified_evidence_is_rejected(tmp_path, monkeypatch):
    assert bridge.before_figure_bytes('unknown', b'unreviewed') == b'unreviewed'
    data, tokens = {'unreviewed': True}, {'unknown': 'f' * 64}
    assert bridge.restore_prior_view('unknown', data, tokens) == (data, tokens)
    raw = (bridge.ROOT / bridge.PROOF).read_bytes()
    path = tmp_path / bridge.PROOF
    path.parent.mkdir(parents=True)
    path.write_bytes(raw + b'\n')
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='evidence changed'):
        bridge.reviewed()
