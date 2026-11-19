"""The chapter-sampling sequence uses real excerpts and keeps marking server-owned."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from primer.learning_games import authoring, catalog, evaluators

ROOT = Path(__file__).resolve().parents[1]
NODE = 'lang.5.comp-ling'
SLUG = 'chapter-samples-in-alice'


def words(text):
    return [unicodedata.normalize('NFC', word).casefold().replace('’', "'")
            for word in re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)*", text)]


def authored():
    [sequence] = authoring.parse(
        (ROOT / 'data/learning-games/language-chapter-sampling.lg').read_text(),
        'data/learning-games/language-chapter-sampling.lg',
    )
    authoring.validate(sequence, 5)
    return sequence


def test_the_chapter_figures_are_reproducible_from_the_original_text():
    source = json.loads((ROOT / 'data/learning-game-sources/alice-chapter-sampling.json').read_text())
    assert source['edition_commit'] == '8da5cac1a4ec2c811322eff79daa5e11e851a813'
    chapters = {chapter['number']: chapter for chapter in source['chapters']}
    assert set(chapters) == {1, 2, 12}
    for chapter in chapters.values():
        assert hashlib.sha256(chapter['text'].encode()).hexdigest() == chapter['text_sha256']
    opening = words(chapters[1]['text'].split('\n\n')[0])
    assert (len(opening), len(set(opening))) == (57, 40)
    excerpt = 'Alice had not a moment to think about stopping herself before she found herself falling down a very deep well.'
    assert excerpt in chapters[1]['text']
    assert (len(words(excerpt)), len(set(words(excerpt)))) == (20, 18)
    chapter_one = words(chapters[1]['text'])
    chapter_twelve = words(chapters[12]['text'])
    assert [len(set(chapter_one[:n])) for n in (100, 200)] == [66, 116]
    assert len(set(chapter_twelve[:200])) == 118
    assert words(chapters[2]['text'])[:500].count('rabbit') == 3
    seq = authored()
    steps = [beat for beat in seq['beats'] if beat['kind'] == 'step']
    assert [step['type'] for step in steps] == ['fill', 'compare', 'predict', 'fill']
    assert len(steps) == 4 and steps[-1]['transfer']
    assert steps[0]['answers'] == [['18']]
    assert steps[-1]['answers'] == [['0.6']]
    assert '57' in seq['beats'][1]['text'] and '40' in seq['beats'][1]['text']
    for step in steps:
        assert evaluators.evaluate(step, evaluators.solution(step), {})['correct'] is True


def test_the_alternate_sequence_is_marked_through_the_private_api(tmp_path, monkeypatch):
    import primer.server as server
    from fastapi.testclient import TestClient
    from primer.learner import LearnerStore
    from primer.wiki import WikiService

    database = str(tmp_path / 'chapter-reader.db')
    monkeypatch.setattr(server, 'learner', LearnerStore(database))
    monkeypatch.setattr(server, 'wiki', WikiService(database))
    monkeypatch.setattr(server, 'BACKUP_DIR', str(tmp_path / 'backups'))
    with TestClient(server.app) as client:
        client.post('/api/profile', json={
            'name': 'Reader', 'age': 32, 'hours_per_week': 6, 'breadth': 'balanced',
            'domains': ['language'],
        })
        locked = client.get('/api/learning-games/' + NODE, params={'sequence': SLUG}).json()
        assert locked['locked'] and {beat['kind'] for beat in locked['current']['beats']} <= {'intro', 'demo'}
        # Simulate a reader returning with standing credit for this module.
        server.learner.seed_assumed([NODE])
        sequence = catalog.for_curriculum(server.curr).sequence(NODE, SLUG)
        assert sequence is not None
        sequences = catalog.for_curriculum(server.curr).sequences(NODE)
        assert len(sequences) >= 2 and sequences[0]['slug'] != SLUG
        response = client.get('/api/learning-games/' + NODE, params={'sequence': SLUG})
        assert response.status_code == 200
        public = response.json()
        assert public['locked'] is False
        serialized = json.dumps(public['current'])
        steps = [beat for beat in sequence['beats'] if beat['kind'] == 'step']
        for step in steps:
            assert step['why'] not in serialized
        first = steps[0]
        attempt = {'sequence': SLUG, 'step': first['id'], 'response': {'values': ['20']}}
        wrong = client.post('/api/learning-games/' + NODE + '/check', json=attempt).json()
        assert wrong['correct'] is False and 'each occur twice' in wrong['feedback']
        hint = client.post('/api/learning-games/' + NODE + '/hint',
                           json={'sequence': SLUG, 'step': first['id']}).json()
        assert len(hint['state']['hints_shown']) == 1
        assert client.post('/api/learning-games/' + NODE + '/reveal',
                           json={'sequence': SLUG, 'step': first['id']}).status_code == 409
        previous_mastery = server.learner.mastery_map().get(NODE, 0)
        for step in steps:
            checked = client.post('/api/learning-games/' + NODE + '/check', json={
                'sequence': SLUG, 'step': step['id'], 'response': catalog.public_solution(step),
            })
            assert checked.status_code == 200, checked.text
            marked = checked.json()
            assert marked['correct'] is True
        assert marked['completed'] and marked['completed']['steps'] == 4
        assert server.learner.mastery_map().get(NODE, 0) == previous_mastery
