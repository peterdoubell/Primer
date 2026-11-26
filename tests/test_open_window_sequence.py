"""Primary-text fidelity and real server marking of the alternate Saki sequence."""
import hashlib
import json
import time
from unittest.mock import patch
from pathlib import Path

from primer.curriculum import Curriculum
from primer.learning_games import catalog

ROOT = Path(__file__).resolve().parents[1]
NODE = 'lang.5.narratology'
SLUG = 'whose-account-the-open-window'


def test_excerpts_are_verbatim_in_the_pinned_primary_transcription():
    provenance = json.loads((ROOT / 'docs/open-window-evidence/source.json').read_text())
    raw = (ROOT / provenance['raw_file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == provenance['raw_sha256']
    text = raw.decode('utf-8')
    authored = (ROOT / 'data/learning-games/language-open-window.lg').read_text()
    assert len(provenance['anchors']) == 10
    for anchor in provenance['anchors'].values():
        assert text[anchor['start']:anchor['end']] == anchor['text']
        assert anchor['text'] in authored
    assert provenance['source'].endswith('oldid=10921512')
    assert 'Romance at short notice was her speciality.' in text


def test_the_new_sequence_preserves_the_original_narratology_entry():
    cat = catalog.Catalog(Curriculum().nodes)
    assert not cat.problems
    seqs = cat.sequences(NODE)
    assert len(seqs) == 2
    assert seqs[0]['slug'] == 'narratology-and-critical-theory'
    seq = cat.sequence(NODE, SLUG)
    assert seq['origin']['review'] == 'unreviewed'
    steps = [b for b in seq['beats'] if b['kind'] == 'step']
    assert [s['type'] for s in steps] == ['match', 'compare', 'predict', 'predict']
    assert [s['transfer'] for s in steps] == [False, False, False, True]
    # Keep the transfer's interpretation local: this is not a claim that the
    # whole story has a single fixed focaliser.
    assert 'does not establish that the whole story' in steps[-1]['why']


def test_real_api_checks_matches_and_preserves_the_study_mastery_boundary(tmp_path):
    from fastapi.testclient import TestClient
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService

    saved = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / 'saki.db')
        srv.learner, srv.wiki = LearnerStore(db), WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / 'backups')
        srv.learner.save_profile('Source reader', 20, 5, 'focused', 5, ['language'], {'pronouns': 'she'})
        srv.learner.seed_assumed([nid for nid in srv.curr.nodes if nid != NODE])
        # Graduate entry requires genuine spaced proof in the prior stage.
        # Build that evidence in this disposable reader; leave the gate intact.
        prior = [nid for nid, node in srv.curr.nodes.items()
                 if node['domain'] == 'language' and node['stage'] == 4]
        now = time.time()
        with patch('primer.learner.time.time', return_value=now - 3 * 86400):
            for nid in prior:
                srv.learner.record_attempt(nid, 1)
        for nid in prior:
            srv.learner.record_attempt(nid, 1)
        seq = catalog.for_curriculum(srv.curr).sequence(NODE, SLUG)
        steps = [b for b in seq['beats'] if b['kind'] == 'step']
        base = '/api/learning-games/' + NODE
        with TestClient(srv.app) as client:
            data = client.get(base + '?sequence=' + SLUG).json()
            assert not data['locked'] and data['current']['slug'] == SLUG
            payload = json.dumps(data, ensure_ascii=False)
            for step in steps:
                assert step['why'] not in payload
                for option in step.get('options', []):
                    assert option['feedback'] not in payload
            first = steps[0]
            right = catalog.public_solution(first)
            ids = list(right['pairs'])
            values = list(right['pairs'].values())
            wrong = {'pairs': dict(zip(ids, values[1:] + values[:1]))}
            attempt = client.post(base + '/check', json={'sequence': SLUG, 'step': first['id'], 'response': wrong}).json()
            assert not attempt['correct'] and attempt['feedback']
            repeat = client.post(base + '/check', json={'sequence': SLUG, 'step': first['id'], 'response': wrong}).json()
            assert repeat['state']['attempts'] == 1
            assert client.post(base + '/reveal', json={'sequence': SLUG, 'step': first['id']}).status_code == 409
            hint = client.post(base + '/hint', json={'sequence': SLUG, 'step': first['id']}).json()
            assert len(hint['state']['hints_shown']) == 1
            mastery = srv.learner.mastery_map().get(NODE, 0)
            last = None
            for step in steps:
                last = client.post(base + '/check', json={'sequence': SLUG, 'step': step['id'], 'response': catalog.public_solution(step)}).json()
                assert last['correct'], last
            assert last['completed']['first'] and 0 < last['completed']['xp_gained'] <= 6
            assert 'quiz' in last['completed']['study_note'].lower()
            assert srv.learner.mastery_map().get(NODE, 0) == mastery
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = saved
