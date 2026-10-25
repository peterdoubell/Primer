"""The fluids companion preserves existing teaching assets and bounded provenance."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media
from primer.quiz import score_short_answer
from tools.fluids_runtime_compatibility import PATHS, before_fluids_bytes, reviewed
from tools.linear_algebra_runtime_compatibility import before_linear_algebra_bytes

ROOT = Path(__file__).resolve().parents[1]


def test_fluids_companion_preserves_the_existing_venturi_and_context():
    node = Curriculum().nodes['phys.4.fluids']
    media = node['lesson_media']
    assert any(row['id'] == 'venturi-flow-plate' for row in media)
    assert any(row.get('renderer') == 'venturi-flow-lab' for row in media)
    assert any(row.get('renderer') == 'spatial-3d' for row in media)
    companion = [row for row in media if row.get('renderer') == 'fluids-concept-lab']
    assert len(companion) == 1
    assert companion[0]['props'] == {'scenario': 'phys.4.fluids'}
    assert len(node['quiz']) == 10


@pytest.mark.parametrize('node_id,props', [
    ('phys.4.fluids', {}),
    ('phys.4.fluids', {'scenario': 'phys.4.fluids', 'extra': True}),
    ('phys.4.fluids', {'scenario': 'phys.4.experiment'}),
    ('phys.4.experiment', {'scenario': 'phys.4.fluids'}),
])
def test_fluids_companion_rejects_unknown_and_cross_lesson_settings(node_id, props):
    node = copy.deepcopy(Curriculum().nodes['phys.4.fluids'])
    item = next(row for row in node['lesson_media'] if row.get('renderer') == 'fluids-concept-lab')
    item['props'] = props
    node['id'] = node_id
    node['lesson_media'] = [item]
    with pytest.raises(ValueError, match='unknown or cross-lesson'):
        _validate_lesson_media(node)


@pytest.mark.parametrize('path', sorted(PATHS))
def test_historical_view_is_exact_and_rejects_unreviewed_changes(path):
    raw = before_linear_algebra_bytes(path, (ROOT / path).read_bytes())
    proof = reviewed()['files'][path]
    assert hashlib.sha256(raw).hexdigest() == proof['after_sha256']
    previous = before_fluids_bytes(path, raw)
    assert hashlib.sha256(previous).hexdigest() == proof['before_sha256']
    assert before_fluids_bytes(path, previous) == previous
    with pytest.raises(ValueError, match='Unreviewed'):
        before_fluids_bytes(path, raw + b'\n')


def test_only_reviewed_teaching_fields_and_companion_change_the_authored_node():
    path = 'data/curriculum/03-physics.json'
    from tools.fidelity_continuation_runtime_compatibility import before_continuation_bytes
    current = json.loads(before_continuation_bytes(path, (ROOT / path).read_bytes()))
    original = json.loads(before_fluids_bytes(path, (ROOT / path).read_bytes()))
    corrections = json.loads((ROOT / 'docs/fluids-fidelity-review-20261016/teaching-corrections.json').read_text())
    assert corrections['unchanged_quiz_indices'] == [0, 1, 3, 5, 6, 7]
    restored = copy.deepcopy(current)
    for row in corrections['changes']:
        parts = row['json_pointer'].split('/')
        assert parts[:4] == ['', 'nodes', '25', 'quiz']
        assert int(parts[4]) in {2, 4, 8, 9}
        quiz = restored['nodes'][25]['quiz'][int(parts[4])]
        assert quiz[parts[5]] == row['after']
        quiz[parts[5]] = row['before']
    assert restored['nodes'][25]['lesson_media'].pop() == corrections['added_media']
    assert restored == original
    for index in [4, 9]:
        quiz = current['nodes'][25]['quiz'][index]
        assert quiz['choices'].count(quiz['answer']) == 1
    for index in [2, 8]:
        quiz = current['nodes'][25]['quiz'][index]
        assert score_short_answer(quiz['answer'], quiz['keywords']) == 1.0
