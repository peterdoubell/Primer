"""Real-reader regressions and exhaustive checks for the handover contract."""
import itertools
import random
import time
from collections import Counter

import pytest
from test_end_to_end_progression import app_client, _sit_placement, _stage


def test_advanced_evidence_survives_several_new_fields_over_http(app_client):
    _sit_placement(app_client, 'math', True)
    for domain in ('history', 'physics', 'chemistry', 'biology'):
        _sit_placement(app_client, domain, False)
        stage, evidence = _stage(app_client)
        assert evidence['math'] >= 4
        assert stage >= 2, (stage, evidence)


def test_stage_policy_exhaustive_reachable_sittings():
    import primer.server as srv
    # Every measurement vector for three general fields, every current stage,
    # every replacement measurement, including repeat sittings and recovery.
    transitions = 0
    for vector in itertools.product(range(6), repeat=3):
        for current, field, result in itertools.product(range(6), range(3), range(6)):
            updated = list(vector)
            updated[field] = result
            evidence = dict(zip(('math', 'history', 'biology'), updated))
            target = srv._general_target(evidence)
            after = srv._settle_stage(current, target, result)
            assert 0 <= after <= 5
            assert after >= current - 1
            assert after >= target
            if target >= current:
                assert after == target
            if result >= current:
                assert after >= current
            if max(updated) >= 4:
                assert after >= 2
            # Repeated low evidence settles, rather than freezing a high-water mark.
            state = after
            for _ in range(6):
                state = srv._settle_stage(state, target, 0)
            assert state == target
            transitions += 1
    assert transitions == 23328


def test_unmarked_practice_counts_once_in_today_without_mastery(app_client):
    import primer.server as srv
    node = 'bio.0.plants'
    app_client.post('/api/profile', json={'name': 'Ada', 'age': 5,
        'hours_per_week': 3, 'breadth': 'balanced', 'domains': ['biology']})
    for sitting in range(3):
        paper = app_client.get('/api/practice/know:'+node, params={'node_id': node}).json()
        answers=[]
        for q in srv._SERVED.get(paper['token'])['questions']:
            # Commit a possible, wrong tap before feedback.
            if q['kind'] == 'order':
                answer = ' '.join(q['items'])
                if answer == q['answer']:
                    answer = ' '.join(reversed(q['items']))
            else:
                answer = next(c for c in q['choices'] if c != q['answer'])
            if sitting:
                answer=str(q["answer"])
            r=app_client.post('/api/quiz/check',json={'token':paper['token'],
                'node_id':node,'id':q['id'],'answer':answer})
            assert r.status_code == 200
            answers.append(answer)
        body={'node_id':node,'token':paper['token'],'answers':answers}
        result=app_client.post('/api/attempt',json=body)
        assert result.status_code == 200
    assert result.json()['unscored']
    before=app_client.get('/api/today').json()
    assert before['quest']['practice']['done']
    assert before['pace']['steps']['practice'] == 0
    assert not before['quest']['learn']['done']
    assert node not in srv.learner.proven_set()
    assert app_client.post('/api/attempt',json=body).status_code == 409
    after=app_client.get('/api/today').json()
    assert after['quest']['practice']['done_count'] == before['quest']['practice']['done_count']


def _tap(q, rng):
    if q['kind'] == 'order':
        parts=list(q['items'])
        rng.shuffle(parts)
        return ' '.join(parts)
    return rng.choice(q['choices'])


@pytest.mark.parametrize('node,domain', [('bio.0.plants','biology'), ('bio.0.living','biology'), ('chem.0.water-states','chemistry')])
@pytest.mark.parametrize('mode,seeds', [('half',range(2)),('guess',range(2)),('learn',range(2))])
def test_45_daily_sittings(app_client, monkeypatch, tmp_path, mode, seeds, node, domain):
    import primer.server as srv
    import primer.learner as learner
    from primer.wiki import WikiService
    base=time.time()
    results=[]
    for seed in seeds:
        db=str(tmp_path / ('%s-%s.db'%(mode,seed)))
        srv.learner=learner.LearnerStore(db)
        srv.wiki=WikiService(db)
        monkeypatch.setattr(srv.time,'time',lambda:base)
        app_client.post('/api/profile',json={'name':'Ada','age':5,'hours_per_week':3,
            'breadth':'balanced','domains':[domain]})
        srv.practice.R.seed(seed)
        srv.practice.reset_rotation()
        rng=random.Random(seed)
        known={}
        exposures=Counter()
        last_retrieved={}
        first=None
        for day in range(45):
            now=base+day*86400
            monkeypatch.setattr(srv.time,'time',lambda:now)
            assert learner.time.time() == now
            paper=app_client.get('/api/practice/know:'+node,params={'node_id':node}).json()
            assert len(paper['questions']) == 10
            answers=[]
            for q in srv._SERVED.get(paper['token'])['questions']:
                key=q['prompt']
                if key not in known:
                    known[key]=rng.random()<0.5 if mode=='half' else False
                if mode == 'learn' and known[key] and now-last_retrieved.get(key,now)>10*86400:
                    known[key]=False
                    exposures[key]=0
                answer=str(q['answer']) if known[key] else _tap(q,rng)
                if answer == str(q['answer']):
                    last_retrieved[key]=now
                feedback=app_client.post('/api/quiz/check',json={'token':paper['token'],
                    'node_id':node,'id':q['id'],'answer':answer})
                assert feedback.status_code == 200
                answers.append(answer)
                exposures[key]+=1
                if mode=='learn' and exposures[key]>=2:
                    known[key]=True
            r=app_client.post('/api/attempt',json={'node_id':node,
                'token':paper['token'],'answers':answers,'seconds':180})
            assert r.status_code == 200
            if node in srv.learner.proven_set() and first is None:
                first=day
            # The honest learner retrieves due cards; nonlearners do not gain
            # knowledge from a review merely because a test gave them the key.
            if mode=='learn':
                for card in app_client.get('/api/review/due').json()['cards']:
                    app_client.post('/api/review',json={'card_id':card['id'],
                        'quality':4 if known.get(card['front']) else 1,'seconds':20})
        results.append(first)
    print(node, mode, results)
    if mode=='learn':
        assert all(d is not None and d<=14 for d in results),results
    else:
        assert results == [None]*len(results),results


def test_three_young_passes_are_each_spaced_and_the_page_says_three(app_client, monkeypatch):
    import primer.server as srv
    base=time.time()
    node='bio.0.plants'
    app_client.post('/api/profile',json={'name':'Ada','age':5,'hours_per_week':3,
        'breadth':'balanced','domains':['biology']})
    # External Wikipedia availability is irrelevant to the local evidence rule.
    monkeypatch.setattr(srv.wiki, 'get_summary', lambda title: None)
    for hours, expected in [(0,1),(1,1),(7,2),(7.1,2),(14,3)]:
        now=base+hours*3600
        monkeypatch.setattr(srv.time,'time',lambda:now)
        paper=app_client.get('/api/practice/know:'+node,params={'node_id':node}).json()
        qs=srv._SERVED.get(paper['token'])['questions']
        assert len(qs)==10
        r=app_client.post('/api/attempt',json={'node_id':node,'token':paper['token'],
            'answers':[str(q['answer']) for q in qs]}).json()
        detail=app_client.get('/api/curriculum/node/'+node).json()['mastery_detail']
        assert detail['passes_needed']==3
        assert detail['passes']==expected
        assert r['proven'] == (expected==3)


def test_adaptive_reencounter_reduces_error_on_missed_concepts(app_client, monkeypatch, tmp_path):
    """A controlled learning model, not evidence about real children's learning.

    The child needs two feedback encounters to retain a missed concept. Both
    conditions have identical initial knowledge, cards, seeds and two daily
    sittings; only access to the recorded mistakes is ablated. An identical
    delayed probe then measures remaining errors on those initial mistakes.
    """
    import primer.server as srv
    from primer.learner import LearnerStore
    base=time.time()
    totals={True:0,False:0}
    outcomes=[]
    for seed in range(8):
        for adaptive in (True,False):
            srv.learner=LearnerStore(str(tmp_path / ('adaptive-%s-%s.db'%(seed,adaptive))))
            monkeypatch.setattr(srv.time,'time',lambda:base)
            app_client.post('/api/profile',json={'name':'Ada','age':5,'hours_per_week':3,
                'breadth':'balanced','domains':['biology']})
            node='bio.0.plants'
            srv.practice.R.seed(seed)
            srv.practice.reset_rotation()
            initial=srv.practice.generate_set('know:'+node,10,0)
            # Durable, uniquely worded concepts chosen before either treatment.
            targets={q['prompt']:q for q in initial if q['kind']=='order'}
            assert targets
            srv.learner.add_cards([{'front':q['prompt'],'back':q['answer'],
                'node_id':node,'article':'Plant'} for q in targets.values()])
            if not adaptive:
                monkeypatch.setattr(srv.learner,'missed_fronts',lambda *a,**kw:[])
            exposures=Counter()
            rng=random.Random(seed)
            for day in range(2):
                now=base+day*86400
                monkeypatch.setattr(srv.time,'time',lambda:now)
                paper=app_client.get('/api/practice/know:'+node,params={'node_id':node}).json()
                answers=[]
                for q in srv._SERVED.get(paper['token'])['questions']:
                    missed=q['prompt'] in targets and exposures[q['prompt']]<2
                    answer=_tap(q,rng) if missed else str(q['answer'])
                    r=app_client.post('/api/quiz/check',json={'token':paper['token'],
                        'node_id':node,'id':q['id'],'answer':answer})
                    assert r.status_code==200
                    exposures[q['prompt']]+=1
                    answers.append(answer)
                assert app_client.post('/api/attempt',json={'node_id':node,
                    'token':paper['token'],'answers':answers}).status_code==200
            # Administer the same held-out paper three days later. The model
            # retains a concept after two teaching encounters; this remains
            # simulated retention, not a human learning-effect estimate.
            monkeypatch.setattr(srv.time, 'time', lambda: base+4*86400)
            probe=list(targets.values())
            responses=[]
            for q in probe:
                if exposures[q['prompt']] >= 2:
                    responses.append(str(q['answer']))
                else:
                    wrong=_tap(q,rng)
                    while wrong == str(q['answer']):
                        wrong=_tap(q,rng)
                    responses.append(wrong)
            marks=srv.quiz.score_quiz(probe,responses)
            errors=marks['total']-marks['right']
            totals[adaptive]+=errors
            outcomes.append((seed,adaptive,errors,len(targets)))
    print('adaptive delayed-probe errors',totals,outcomes)
    assert totals[True] < totals[False], outcomes


def test_review_revealed_key_restarts_cooling_off(app_client, monkeypatch):
    import primer.server as srv
    from primer import practice
    node = 'bio.0.plants'
    question = practice._know_order(practice.young_material()[node])
    # Use the same durable front/back representation as mistake cards.
    srv.learner.add_cards([{'front': question['prompt'], 'back': question['answer'],
                           'node_id': node}])
    with srv.learner._conn() as conn:
        card_id = conn.execute('SELECT id FROM srs_cards WHERE node_id=?', (node,)).fetchone()[0]
    original = srv.time.time()
    srv.learner.burn_item(node, srv._fingerprint(question))
    monkeypatch.setattr(srv.time, 'time', lambda: original + 3 * 86400)
    assert not srv.learner.burned_map(node, window_days=2)
    response = app_client.post('/api/review', json={'card_id': card_id, 'quality': 1})
    assert response.status_code == 200
    assert srv._fingerprint(question) in srv.learner.burned_map(node, window_days=2)


@pytest.mark.parametrize('kind', ['fact', 'short'])
def test_explained_and_abbreviated_review_keys_cannot_be_fresh_evidence(app_client, monkeypatch, kind):
    import primer.server as srv
    node='bio.0.plants'
    q={'id':'review-key', 'kind':'choice', 'prompt':'What do leaves make?',
       'answer':'their own food', 'choices':['their own food','their own soil'],
       'explain':'Leaves use sunlight to make food out of air and water.'}
    if kind == 'short':
        q.update(kind='short', prompt='Explain what leaves make.',
                 answer='Leaves make food using light, air and water.', keywords=['food','light'])
    cards=srv.quiz.cards_from_missed([q],['wrong'],node,'Plant')
    assert cards and cards[0]['back'] != q['answer']
    srv.learner.add_cards(cards)
    with srv.learner._conn() as conn:
        card_id=conn.execute('SELECT id FROM srs_cards WHERE node_id=?',(node,)).fetchone()[0]
    before=srv.time.time()
    monkeypatch.setattr(srv.time,'time',lambda:before+3*86400)
    assert app_client.post('/api/review',json={'card_id':card_id,'quality':1}).status_code==200
    assert srv._drop_burned([q],[q['answer']],node,1)[0] == []
    monkeypatch.setattr(srv.time,'time',lambda:before+12*86400)
    assert srv._drop_burned([q],[q['answer']],node,1)[0] == [q]


def test_maintenance_exits_when_shutdown_arrives_during_a_backup(monkeypatch):
    import threading
    import primer.server as srv
    stop=threading.Event()
    runs=[]
    def run_once():
        runs.append(1)
        stop.set()
    monkeypatch.setattr(srv,'_run_maintenance_once',run_once)
    worker=threading.Thread(target=srv._maintenance_loop,args=(stop,),daemon=True)
    worker.start()
    worker.join(timeout=1)
    assert not worker.is_alive()
    assert runs == [1]


def test_successful_review_does_not_burn_an_already_known_key(app_client, monkeypatch):
    import primer.server as srv
    q={'prompt':'Why does an animal need food?', 'answer':'eat it to grow'}
    node='bio.0.living'
    srv.learner.add_cards([{'front':q['prompt'],'back':q['answer'],'node_id':node}])
    with srv.learner._conn() as conn:
        card_id=conn.execute('SELECT id FROM srs_cards WHERE node_id=?',(node,)).fetchone()[0]
    now=srv.time.time()
    monkeypatch.setattr(srv.time,'time',lambda:now+8*86400)
    assert app_client.post('/api/review',json={'card_id':card_id,'quality':4}).status_code==200
    assert not srv.learner.burned_map(node)
    assert srv._drop_burned([q],[q['answer']],node,1)[0] == [q]
