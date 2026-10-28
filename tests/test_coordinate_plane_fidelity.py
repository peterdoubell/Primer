"""Current lesson evidence, preserved assessments and bounded historical projections."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from primer.curriculum import Curriculum, _validate_lesson_media, _validate_authored_lesson
from tools.coordinate_plane_runtime_compatibility import before_coordinate_plane_bytes, reviewed

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/coordinate-plane-review-20261028'


def test_original_quiz_prerequisites_and_illustration_preserved():
    scope = json.loads((DOCS / 'initial-scope.json').read_bytes())
    node = next(n for n in json.loads((ROOT / 'data/curriculum/01-mathematics.json').read_bytes())['nodes'] if n['id'] == 'math.2.coordinates')
    old = scope['originalNode']
    assert len(node['quiz']) == 10
    assert {k: v for k, v in node.items() if k not in ['lesson_media', 'lesson', 'learning_outcomes']} == {
        k: v for k, v in old.items() if k != 'lesson_media'}
    assert node['lesson_media'][0] == old['lesson_media'][0]
    assert len(node['lesson_media']) == 2
    assert node['lesson_media'][1]['renderer'] == 'coordinate-plane-lab'
    assert len(node['learning_outcomes']) == 6
    _validate_authored_lesson(node)
    _validate_lesson_media(node)
    bindings = json.loads((ROOT / 'data/module-models.json').read_bytes())
    row = next(r for r in bindings['models'] if r['node_id'] == node['id'])
    assert row['family'] == 'coordinate-plane-exact' and row['mode'] == 'model'


def test_invalid_and_cross_lesson_props_rejected():
    node = Curriculum().node('math.2.coordinates')
    for props in [{}, {'scenario': 'math.3.linear'}, {'scenario': node['id'], 'extra': 1}]:
        bad = copy.deepcopy(node)
        bad['lesson_media'][1]['props'] = props
        with pytest.raises(ValueError):
            _validate_lesson_media(bad)


def test_exact_historical_projection_does_not_accept_other_edits():
    for file, row in reviewed()['files'].items():
        raw = (ROOT / file).read_bytes()
        restored = before_coordinate_plane_bytes(file, raw)
        assert hashlib.sha256(restored).hexdigest() == row['before_sha256']
        assert before_coordinate_plane_bytes(file, restored) == restored
        with pytest.raises(ValueError):
            before_coordinate_plane_bytes(file, raw + b'\n')


def test_authenticated_reader_proof_matches_current_sources():
    proof = json.loads((DOCS / 'reader/proof.json').read_bytes())
    assert proof['allPassed'] and proof['syntheticLoopback'] and not proof['productionVerified']
    assert proof['errors'] == []
    assert {case['width'] for case in proof['cases']} == {390, 1440}
    assert sum(len(case['states']) for case in proof['cases']) == 28
    for file, digest in proof['sourceSHA256'].items():
        assert hashlib.sha256((ROOT / file).read_bytes()).hexdigest() == digest, file
    for case in proof['cases']:
        assert len(case['poses']) == 7
        assert all(case[k] for k in ['originalIllustrationLoaded', 'assessmentsPreserved',
                                    'invalidDraftPreserved', 'cameraPreservedState',
                                    'resetSynchronized', 'keyboardTableScroll'])
        assert all(s['linked'] and s['exactPointTable'] and s['geometryVerified'] and not s['overflow'] for s in case['states'])
