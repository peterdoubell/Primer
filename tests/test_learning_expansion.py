"""Age-three to master's pathways preserve progression and teaching media."""
import copy
from collections import Counter

import pytest

from primer.curriculum import Curriculum, _validate_authored_lesson
from primer.learner import STAGE_SPAN


@pytest.fixture(scope='module')
def curriculum():
    return Curriculum()


def test_every_field_has_a_continuous_pathway(curriculum):
    assert len(curriculum.domains) == 19
    assert '3–5' in STAGE_SPAN[0] and 'master' in STAGE_SPAN[5]
    for domain in curriculum.domains:
        counts = Counter(n['stage'] for n in curriculum.nodes.values() if n['domain'] == domain['id'])
        assert set(counts) == set(range(6)), domain['id']
        assert min(counts.values()) >= 2, domain['id']


def test_expansion_contains_taught_assessed_visual_lessons(curriculum):
    nodes = [node for node in curriculum.nodes.values() if node.get('lesson')]
    assert len(nodes) == 106
    for node in nodes:
        _validate_authored_lesson(node)
        assert len(node['lesson']['overview'].split()) >= 30, node['id']
        assert len(node['learning_outcomes']) >= 3
        assert len(node['quiz']) >= (6 if node['stage'] < 2 else 11)
        assert all(q.get('explain') for q in node['quiz'])
        assert {m['kind'] for m in node['lesson_media']} == {'photograph', 'illustration', 'model'}
        plate = next(m for m in node['lesson_media'] if m['kind'] == 'illustration')
        assert plate['long_description'] == node['visual_spec']
        assert all(p in curriculum.nodes for p in node['prereqs'])
        if node['stage'] <= 1:
            assert node['kid_text']


def test_imaging_foundations_do_not_become_clinical_reports(curriculum):
    imaging = [n for n in curriculum.nodes.values() if n['id'].startswith('img.')]
    clinical = [n for n in curriculum.nodes.values() if n['id'].startswith('rad.')]
    assert len(imaging) == 10 and len(clinical) == 96
    assert all(n['domain'] == 'radiology' and n['stage'] < 5 for n in imaging)
    assert all(not n.get('radiology_reference') for n in imaging)
    assert all(n.get('radiology_reference') and n['stage'] == 5 for n in clinical)
    assert all(not curriculum.unlocked(n, {}) for n in clinical)
    assert all(curriculum.unlocked(n, {}) for n in imaging if n['stage'] == 0)


def test_teaching_bodies_are_detail_only(curriculum):
    graph = curriculum.annotated_graph({})
    detail_fields = {'lesson', 'learning_outcomes', 'visual_spec', 'model_context', 'model_family', 'lesson_media'}
    assert all(not detail_fields.intersection(node) for node in graph['nodes'])
    assert curriculum.node('eng.0.build')['lesson']


@pytest.mark.parametrize('change', ['missing_example', 'empty_activity', 'bad_outcomes'])
def test_malformed_teaching_content_is_rejected(curriculum, change):
    node = copy.deepcopy(curriculum.node('eng.0.build'))
    if change == 'missing_example':
        del node['lesson']['worked_example']
    elif change == 'empty_activity':
        node['lesson']['activity'] = ''
    else:
        node['learning_outcomes'] = 'not a list'
    with pytest.raises(ValueError):
        _validate_authored_lesson(node)
