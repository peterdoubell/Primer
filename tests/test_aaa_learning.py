"""AAA learning-science audit fixes: focused regression tests.

Covers: decay-aware pacing (gate view, not raw EMA), SRS review load in the
roadmap price, calibration-modulated self-graded restores, the quality-
sensitive SM-2 lapse penalty, partial credit for effortful (q=3) recall,
and placement re-measurement after a cooling period.

Run:  .venv/bin/python -m pytest tests/test_aaa_learning.py -q
"""

import os
import sqlite3
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer.learner import DAY, LearnerStore  # noqa: E402
from primer.pacing import SRS_REVIEW_MIN_PER_NODE, roadmap  # noqa: E402


@pytest.fixture
def store(tmp_path):
    return LearnerStore(str(tmp_path / 'aaa.db'))


def _raw(store, sql, *args):
    conn = sqlite3.connect(store.db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, args)
        rows = cur.fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def _add_due_card(store, node_id='node.a', origin='book', ef=2.5, reps=0,
                  interval=0.0):
    now = time.time()
    _raw(store,
         """INSERT INTO srs_cards(front, back, node_id, article, ef, interval,
                                  reps, lapses, due, created_at, origin)
            VALUES(?,?,?,?,?,?,?,0,?,?,?)""",
         'q-' + node_id + '-' + origin + str(ef), 'a', node_id, '', ef,
         interval, reps, now - 60, now - 90 * DAY, origin)
    return _raw(store, "SELECT id FROM srs_cards ORDER BY id DESC LIMIT 1")[0]['id']


def _seed_faded_mastered(store, node_id='node.a', days_ago=120):
    """A genuinely proven node whose memory has since decayed well below the
    0.35 gate (half-life 30d at one reinforcement)."""
    then = time.time() - days_ago * DAY
    _raw(store,
         """INSERT INTO mastery(node_id, level, attempts, passes, first_pass_at,
                                last_pass_at, strength, last_seen, assumed,
                                mastered_at, reinforcements, first_mastered_at)
            VALUES(?,0.9,3,2,?,?,1.0,?,0,?,1,?)""",
         node_id, then - 3 * DAY, then, then, then, then)


def _node_row(store, node_id='node.a'):
    return _raw(store, "SELECT * FROM mastery WHERE node_id=?", node_id)[0]


# ---------------- 1. pacing counts from the gate view, not raw EMA ----------


GRAPH = {
    'domains': [{'id': 'math', 'name': 'Math'}],
    'nodes': [
        {'id': 'm1', 'domain': 'math', 'stage': 0, 'minutes': 60},
        {'id': 'm2', 'domain': 'math', 'stage': 0, 'minutes': 60},
    ],
}
PROFILE = {'breadth': 'focused', 'domains': ['math'], 'hours_per_week': 6,
           'stage': 0}


def test_raw_ema_level_does_not_shorten_the_plan():
    """mastery_map()-style values (raw EMA >= 0.8, never decayed, assumed and
    proven indistinguishable) must not drop a node from the roadmap. Only the
    gate view's exact 1.0 — mastery currently standing — does."""
    ema_high = roadmap(PROFILE, GRAPH, {'m1': 0.85})   # EMA high, gates closed
    untouched = roadmap(PROFILE, GRAPH, {})
    assert ema_high['total_hours'] == untouched['total_hours']
    assert ema_high['nodes_mastered'] == 0

    gate_open = roadmap(PROFILE, GRAPH, {'m1': 1.0})
    assert gate_open['total_hours'] < untouched['total_hours']
    assert gate_open['nodes_mastered'] == 1


def test_faded_node_stays_in_the_plan_like_the_gates_say():
    """gate_map() emits min(level, 0.79) for a faded mastered node — pacing
    must keep scheduling it, matching what the gates actually re-locked."""
    faded = roadmap(PROFILE, GRAPH, {'m1': 0.79})  # gate_map's faded encoding
    assert faded['nodes_mastered'] == 0
    assert faded['total_hours'] == roadmap(PROFILE, GRAPH, {})['total_hours']


# ---------------- 6. roadmap prices SRS maintenance, not just instruction ---


def test_roadmap_prices_srs_review_load():
    graph = {
        'domains': [{'id': 'math', 'name': 'Math'}],
        'nodes': [{'id': 'm%d' % i, 'domain': 'math', 'stage': 0, 'minutes': 60}
                  for i in range(100)],
    }
    r = roadmap(PROFILE, graph, {})
    instructional = sum(n['minutes'] for n in graph['nodes'])
    expected = instructional + SRS_REVIEW_MIN_PER_NODE * len(graph['nodes'])
    assert r['total_hours'] == round(expected / 60)
    assert r['total_hours'] > round(instructional / 60)


# ---------------- 2. calibration modulates self-graded restores -------------


def test_overconfidence_rate_pools_recent_calibration_events(store):
    assert store.overconfidence_rate() == 0.0
    store.log_event('calibration', {'node': 'n', 'overconfident': 2,
                                    'underconfident': 0, 'total': 4})
    store.log_event('calibration', {'node': 'n', 'overconfident': 0,
                                    'underconfident': 1, 'total': 4})
    assert store.overconfidence_rate() == pytest.approx(2 / 8)


def test_calibrated_reader_still_gets_full_restore(store):
    _seed_faded_mastered(store)
    cid = _add_due_card(store)
    store.review_card(cid, 5)
    assert _node_row(store)['strength'] == pytest.approx(1.0)


def test_overconfident_reader_gets_capped_restore(store):
    """A reader whose confident quiz answers are wrong more than a third of
    the time cannot restore a faded node to full strength on their own say-so;
    the self-graded q>=4 restore is capped at 0.85."""
    _seed_faded_mastered(store)
    for _ in range(3):
        store.log_event('calibration', {'node': 'n', 'overconfident': 2,
                                        'underconfident': 0, 'total': 4})
    assert store.overconfidence_rate() > 1 / 3
    cid = _add_due_card(store)
    store.review_card(cid, 5)
    assert _node_row(store)['strength'] == pytest.approx(0.85)


# ---------------- 3. SM-2 quality-sensitive lapse penalty --------------------


@pytest.mark.parametrize('quality,drop', [(2, 0.32), (1, 0.54), (0, 0.80)])
def test_lapse_ef_penalty_follows_the_sm2_polynomial(store, quality, drop):
    cid = _add_due_card(store, node_id='', ef=2.5)
    store.review_card(cid, quality)
    row = _raw(store, "SELECT ef FROM srs_cards WHERE id=?", cid)[0]
    assert row['ef'] == pytest.approx(2.5 - drop, abs=1e-6)


def test_lapse_ef_never_falls_below_the_sm2_floor(store):
    cid = _add_due_card(store, node_id='', ef=1.4)
    store.review_card(cid, 0)
    row = _raw(store, "SELECT ef FROM srs_cards WHERE id=?", cid)[0]
    assert row['ef'] == pytest.approx(1.3)


# ---------------- 4. q=3 (effortful success) gives partial node credit -------


def test_q3_book_review_partially_refreshes_the_node(store):
    _seed_faded_mastered(store)
    before = _node_row(store)
    cid = _add_due_card(store)
    now = time.time()
    store.review_card(cid, 3)
    after = _node_row(store)
    assert after['last_seen'] >= now - 5, 'the decay clock must restart'
    assert after['strength'] == pytest.approx(0.5)
    assert after['strength'] < 1.0, 'partial, not the q>=4 full restore'
    assert after['last_seen'] > before['last_seen']
    # Enough to stand as mastered again — effortful recall is real evidence.
    assert 'node.a' in store.mastered_set()


def test_q3_on_a_reader_written_card_is_still_not_evidence(store):
    _seed_faded_mastered(store)
    before = _node_row(store)
    cid = _add_due_card(store, origin='reader')
    store.review_card(cid, 3)
    after = _node_row(store)
    assert after['strength'] == before['strength']
    assert after['last_seen'] == before['last_seen']


# ---------------- 7. placement re-measurement after cooling ------------------


def test_settled_placement_cannot_reopen_inside_the_cooling_window(store):
    store.placement_update('math', 2, ['q1'], True)
    assert store.reopen_placement('math') is False
    assert store.placement_state()['math']['done'] is True


def test_settled_placement_reopens_after_cooling(store):
    store.placement_update('math', 2, ['q1'], True)
    _raw(store, "UPDATE placement SET settled_at=? WHERE domain=?",
         time.time() - 8 * DAY, 'math')
    assert store.reopen_placement('math') is True
    state = store.placement_state()['math']
    assert state['done'] is False
    assert state['stage'] == 2 and state['asked'] == ['q1'], \
        'the rung and asked-history survive, only the settled flag clears'
    # Not settled any more, so a second call has nothing to reopen.
    assert store.reopen_placement('math') is False


def test_unsettled_or_unknown_domain_never_reopens(store):
    store.placement_update('math', 1, [], False)
    assert store.reopen_placement('math') is False
    assert store.reopen_placement('history') is False


def test_legacy_settled_row_without_timestamp_is_reopenable(store):
    store.placement_update('math', 2, [], True)
    _raw(store, "UPDATE placement SET settled_at=NULL WHERE domain=?", 'math')
    assert store.reopen_placement('math') is True


# ---------------- 7. early review: failures count, successes don't ----------


def _add_early_card(store, node_id='node.a', days_until_due=1.0):
    now = time.time()
    _raw(store,
         """INSERT INTO srs_cards(front, back, node_id, article, ef, interval,
                                  reps, lapses, due, created_at, origin)
            VALUES(?,?,?,?,2.5,3.0,2,0,?,?, 'book')""",
         'early-q-' + node_id, 'a', node_id, '',
         now + days_until_due * DAY, now - 90 * DAY)
    return _raw(store, "SELECT id FROM srs_cards ORDER BY id DESC LIMIT 1")[0]['id']


def test_early_success_is_still_practice_not_progress(store):
    """Passing a card before it is due proves nothing (the short gap made it
    easy) and must stay creditless — the anti-farming rule."""
    _seed_faded_mastered(store)
    before = _node_row(store)['strength']
    cid = _add_early_card(store)
    res = store.review_card(cid, 5)
    assert res.get('early') is True and res['xp_gained'] == 0
    assert _node_row(store)['strength'] == pytest.approx(before)


def test_early_failure_is_negative_evidence(store):
    """Blanking on a card a day before it was due is genuine forgetting: the
    card must lapse and the node's strength must drop, not be discarded."""
    _seed_faded_mastered(store)
    _raw(store, "UPDATE mastery SET strength=1.0, last_seen=? WHERE node_id=?",
         time.time(), 'node.a')
    cid = _add_early_card(store)
    res = store.review_card(cid, 0)
    assert res.get('early') is not True
    assert res['xp_gained'] == 0, 'no farming route through failure'
    card = _raw(store, "SELECT * FROM srs_cards WHERE id=?", cid)[0]
    assert (card['lapses'] or 0) >= 1
    assert _node_row(store)['strength'] < 1.0


# ---------------- 8. overconfidence discounts durability growth too ---------


def _make_overconfident(store):
    for _ in range(3):
        store.log_event('calibration', {'node': 'n', 'overconfident': 2,
                                        'underconfident': 0, 'total': 4})
    assert store.overconfidence_rate() > 1 / 3


def test_calibrated_reader_earns_reinforcement(store):
    _seed_faded_mastered(store)
    cid = _add_due_card(store)
    store.review_card(cid, 5)
    assert _node_row(store)['reinforcements'] == 2


def test_overconfident_reader_earns_no_reinforcement(store):
    """The same distrusted self-grade that gets its restore capped must not
    buy a permanent half-life extension either — one discount, applied to
    everything the grade pays for."""
    _seed_faded_mastered(store)
    _make_overconfident(store)
    cid = _add_due_card(store)
    store.review_card(cid, 5)
    row = _node_row(store)
    assert row['strength'] == pytest.approx(0.85)
    assert row['reinforcements'] == 1, 'half-life must not lengthen'


# ---------------- 9. roadmap headline: proven vs assumed --------------------


def test_roadmap_splits_proven_from_assumed_when_told():
    r = roadmap(PROFILE, GRAPH, {'m1': 1.0, 'm2': 1.0}, proven={'m1'})
    assert r['nodes_mastered'] == 2
    assert r['nodes_proven'] == 1
    assert r['nodes_assumed'] == 1


def test_roadmap_without_proven_set_leaves_split_unknown():
    r = roadmap(PROFILE, GRAPH, {'m1': 1.0})
    assert r['nodes_mastered'] == 1
    assert r['nodes_proven'] is None and r['nodes_assumed'] is None


# ---------------- 10. ambiguous prereq titles get domain-qualified ----------


def test_cross_domain_and_duplicate_prereq_titles_are_qualified():
    from primer.curriculum import Curriculum
    curr = Curriculum()
    # math.3.trig requires math.3.functions — same domain, but "Functions"
    # also names cs.2.functions, so the title alone is ambiguous.
    reqs = curr.unlock_requirements(curr.nodes['math.3.trig'], {})
    assert any('Functions (' in r for r in reqs)
    # math.3.euclid requires mind.2.logic-intro — a cross-domain prereq.
    reqs = curr.unlock_requirements(curr.nodes['math.3.euclid'], {})
    assert any('(' in r and 'Logic' in r for r in reqs)
