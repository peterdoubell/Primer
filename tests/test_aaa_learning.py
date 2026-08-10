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


_FRESH_N = [0]


def _fresh_store():
    """A second, independent store — for tests that must compare the same
    action taken by two differently-calibrated readers."""
    import tempfile
    _FRESH_N[0] += 1
    d = tempfile.mkdtemp()
    return LearnerStore(os.path.join(d, 'fresh%d.db' % _FRESH_N[0]))


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


def test_overconfident_reader_gets_a_graded_discount_on_the_restore(store):
    """A reader whose confident quiz answers are often wrong cannot restore a
    faded node to full strength on their own say-so — but the discount ramps.

    Superseded assertion, rewritten: this used to require exactly 0.85 the
    instant the rate crossed 1/3. That made 0.333 and 0.334 different kinds of
    learner over a single answer, and a measured quantity with a cliff in the
    middle of its plausible range reports the cliff more than it reports the
    reader. The discount now starts at the limit and reaches the 0.85 cap at
    CALIBRATION_FULL_DISCOUNT; what must hold is that it is monotone, that a
    calibrated reader is untouched, and that the cap is a real floor.
    """
    def restore(over, total):
        s = _fresh_store()
        _seed_faded_mastered(s)
        for _ in range(3):
            s.log_event('calibration', {'node': 'n', 'overconfident': over,
                                        'underconfident': 0,
                                        'confident_total': total, 'total': total})
        cid = _add_due_card(s)
        s.review_card(cid, 5)
        return _node_row(s)['strength']

    at_limit = restore(1, 3)                 # exactly 1/3 — still calibrated
    middling = restore(2, 4)                 # 0.5
    hopeless = restore(4, 4)                 # 1.0
    assert at_limit == pytest.approx(1.0)
    assert 0.85 < middling < 1.0, middling
    assert hopeless == pytest.approx(0.85)
    assert at_limit > middling > hopeless


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


def test_overconfident_reader_earns_only_partial_reinforcement(store):
    """The same distrusted self-grade that gets its restore discounted must not
    buy a full permanent half-life extension either — one discount, applied to
    everything the grade pays for.

    Superseded assertion, rewritten alongside the restore cliff it mirrored:
    the payment used to be switched off entirely past 1/3. It is now scaled by
    the same ramp, so the durability a grade buys and the strength it restores
    move together and continuously. A fully-discounted grade still buys
    nothing; a half-discounted one buys half.
    """
    _seed_faded_mastered(store)
    _make_overconfident(store)          # rate 0.5 — halfway up the ramp
    cid = _add_due_card(store)
    store.review_card(cid, 5)
    row = _node_row(store)
    assert 1 < row['reinforcements'] < 2, 'a discounted grade buys a partial half-life'

    ruined = _fresh_store()
    _seed_faded_mastered(ruined)
    for _ in range(3):
        ruined.log_event('calibration', {'node': 'n', 'overconfident': 4,
                                         'underconfident': 0,
                                         'confident_total': 4, 'total': 4})
    ruined.review_card(_add_due_card(ruined), 5)
    assert _node_row(ruined)['reinforcements'] == 1, 'half-life must not lengthen at all'


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


# ---------------- 11. age-scaled spacing (round 4) --------------------------


def _set_age(store, age):
    store.save_profile(name='R', age=age, hours_per_week=6,
                       breadth='balanced', domains=['math'], stage=0)


def test_proving_window_and_learning_steps_scale_with_age():
    """The distributed-practice argument REINFORCE_MIN_GAP_BY_AGE already
    cites applies to the proving window and to SM-2's learning steps too."""
    from primer.learner import (MASTERY_MIN_INTERVAL, _mastery_min_interval,
                                _sm2_first_steps)
    assert _mastery_min_interval(30) == MASTERY_MIN_INTERVAL
    assert _mastery_min_interval(None) == MASTERY_MIN_INTERVAL
    assert _mastery_min_interval(5) < _mastery_min_interval(9) < _mastery_min_interval(15)
    # Still far longer than one sitting: two attempts in an afternoon can
    # never prove a node, at any age.
    assert _mastery_min_interval(4) >= 4 * 3600
    assert _sm2_first_steps(30) == (1.0, 6.0)
    young_first, young_second = _sm2_first_steps(5)
    assert 0 < young_first < 1.0 and young_first < young_second < 6.0


def test_a_young_reader_can_prove_a_node_across_one_day(store):
    """A 5-year-old's two spaced passes six hours apart are genuine spaced
    practice; the adult two-day window silently refused to count them."""
    _set_age(store, 5)
    now = time.time()
    store.record_attempt('n', 1.0)
    _raw(store, "UPDATE mastery SET first_pass_at=?, last_pass_at=? WHERE node_id='n'",
         now - 7 * 3600, now - 7 * 3600)
    r = store.record_attempt('n', 1.0)
    assert r['mastered'] and r['proven']


def test_an_adult_still_needs_two_days(store):
    _set_age(store, 30)
    now = time.time()
    store.record_attempt('n', 1.0)
    _raw(store, "UPDATE mastery SET first_pass_at=?, last_pass_at=? WHERE node_id='n'",
         now - 7 * 3600, now - 7 * 3600)
    assert not store.record_attempt('n', 1.0)['mastered']


def test_first_review_step_is_shorter_for_a_small_child(store):
    _set_age(store, 5)
    cid = _add_due_card(store, node_id='')
    assert store.review_card(cid, 5)['next_days'] < 1.0


# ---------------- 12. reader-card failure is still evidence ----------------


def test_a_failed_reader_card_lowers_node_strength(store):
    """Failure is evidence even when the test was easy — and a card the reader
    wrote is the easiest test there is. Previously it moved nothing at all."""
    _seed_faded_mastered(store, days_ago=0)
    before = _node_row(store)['strength']
    cid = _add_due_card(store, origin='reader')
    store.review_card(cid, 0)
    assert _node_row(store)['strength'] < before


def test_a_passed_reader_card_still_restores_nothing(store):
    """The asymmetry is the point: self-certification cannot raise a node."""
    _seed_faded_mastered(store)
    cid = _add_due_card(store, origin='reader')
    store.review_card(cid, 5)
    # Nothing was written at all: the stored strength keeps its old value
    # *and* its old clock, so the decayed reading is still below the gate.
    assert _node_row(store)['reinforcements'] == 1
    assert 'node.a' not in store.proven_set()


def test_a_reader_card_failure_cannot_revoke_mastery(store):
    """It can flag decay; it must not on its own tear down proven work."""
    _seed_faded_mastered(store, days_ago=0)
    cid = _add_due_card(store, origin='reader')
    for _ in range(8):
        _raw(store, "UPDATE srs_cards SET due=? WHERE id=?", time.time() - 60, cid)
        store.review_card(cid, 0)
    assert _node_row(store)['mastered_at'] is not None


# ---------------- 13. underconfidence is credited, not just penalised ------


def test_underconfident_reader_gets_a_more_generous_q3(store):
    """The mirror of the overconfidence discount: a reader whose hesitant quiz
    answers are usually right has their self-graded q=3 credited a notch up."""
    _seed_faded_mastered(store)
    for _ in range(3):
        store.log_event('calibration', {'node': 'n', 'overconfident': 0,
                                        'underconfident': 4,
                                        'hesitant_total': 4, 'total': 4})
    assert store.underconfidence_rate() > 1 / 3
    cid = _add_due_card(store)
    store.review_card(cid, 3)
    # Graded on the same ramp as the overconfidence discount it mirrors: a
    # fully underconfident reader gets the whole 0.7 floor, a borderline one a
    # fraction of the way up from 0.5. Asserting the endpoint keeps the two
    # directions symmetric without re-encoding the cliff that was removed.
    assert _node_row(store)['strength'] == pytest.approx(0.7)


def test_a_calibrated_reader_keeps_the_plain_q3_floor(store):
    _seed_faded_mastered(store)
    cid = _add_due_card(store)
    store.review_card(cid, 3)
    assert _node_row(store)['strength'] == pytest.approx(0.5)


def test_the_generous_q3_still_does_not_buy_the_half_life(store):
    """A notch up on strength, not the permanent durability payment q>=4 buys."""
    _seed_faded_mastered(store)
    for _ in range(3):
        store.log_event('calibration', {'node': 'n', 'overconfident': 0,
                                        'underconfident': 2, 'total': 4})
    cid = _add_due_card(store)
    store.review_card(cid, 3)
    assert _node_row(store)['reinforcements'] == 1


# ---------------- 14. the freshness gate shows its arithmetic --------------


def test_fresh_gate_is_consistent_with_the_interval_cap():
    """FRESH_GATE and MAX_INTERVAL_DAYS are two views of one number: the
    longest schedulable interval must still land above the gate at the slowest
    half-life, or a card can be reviewed exactly on time and read as faded."""
    import math
    from primer.learner import (FRESH_GATE, MAX_INTERVAL_DAYS,
                                STRENGTH_HALF_LIFE_MAX)
    survives_days = (STRENGTH_HALF_LIFE_MAX / DAY) * math.log(FRESH_GATE, 0.5)
    assert survives_days > MAX_INTERVAL_DAYS


# ---------------- 15. per-reader SRS maintenance in the roadmap ------------


def test_roadmap_keeps_its_shape_without_deck_stats():
    from primer.pacing import srs_minutes_per_node
    r = roadmap(PROFILE, GRAPH, {})
    assert r['srs_minutes_per_node'] == pytest.approx(SRS_REVIEW_MIN_PER_NODE)
    assert r['total_hours'] == roadmap(PROFILE, GRAPH, {}, deck=None)['total_hours']
    assert srs_minutes_per_node({}) == SRS_REVIEW_MIN_PER_NODE


def test_a_lapse_prone_deck_is_priced_higher_than_a_clean_one():
    clean = {'cards_per_node': 3.0, 'reviews_graded': 200, 'lapse_rate': 0.05}
    lapsey = {'cards_per_node': 3.0, 'reviews_graded': 200, 'lapse_rate': 0.5}
    a = roadmap(PROFILE, GRAPH, {}, deck=clean)
    b = roadmap(PROFILE, GRAPH, {}, deck=lapsey)
    assert b['srs_minutes_per_node'] > a['srs_minutes_per_node']
    assert b['total_hours'] >= a['total_hours']


def test_a_bigger_deck_per_node_costs_more_maintenance():
    small = {'cards_per_node': 2.0, 'reviews_graded': 100, 'lapse_rate': 0.125}
    big = {'cards_per_node': 8.0, 'reviews_graded': 100, 'lapse_rate': 0.125}
    from primer.pacing import srs_minutes_per_node
    assert srs_minutes_per_node(big) > srs_minutes_per_node(small)
    # And it is bounded either way: one rough fortnight must not triple a plan.
    from primer.pacing import SRS_MIN_PER_NODE_CEIL, SRS_MIN_PER_NODE_FLOOR
    wild = {'cards_per_node': 40.0, 'reviews_graded': 100, 'lapse_rate': 0.95}
    assert srs_minutes_per_node(wild) == SRS_MIN_PER_NODE_CEIL
    tiny = {'cards_per_node': 0.2, 'reviews_graded': 100, 'lapse_rate': 0.0}
    assert srs_minutes_per_node(tiny) == SRS_MIN_PER_NODE_FLOOR


def test_deck_stats_reports_the_shape_pacing_needs(store):
    store.add_cards([{'front': 'a', 'back': 'b', 'node_id': 'n1'},
                     {'front': 'c', 'back': 'd', 'node_id': 'n1'}])
    _raw(store, "UPDATE srs_cards SET reps=7, lapses=1")
    s = store.deck_stats()
    assert s['cards_per_node'] == pytest.approx(2.0)
    assert s['lapse_rate'] == pytest.approx(2 / 16)
    assert s['total'] == 2


# ---------------- 16. lapse_rate over reviews that were actually taken ------


def _drill(store, card_id, qualities):
    """Grade one card repeatedly, forcing it due before each grade."""
    for q in qualities:
        _raw(store, "UPDATE srs_cards SET due=? WHERE id=?", time.time() - 60, card_id)
        store.review_card(card_id, q)


def test_lapse_rate_is_measured_over_every_review_ever_taken(store):
    """Regression, quantitative and user-visible: `lapse_rate` divided by
    SUM(reps) + SUM(lapses), and SM-2 resets `reps` to 0 on every lapse.

    So a card with ten clean successes and then one failure reported reps=0,
    lapses=1 — a lapse rate of 1.0 for a card the reader gets right 91% of the
    time. That figure is not cosmetic: pacing.srs_minutes_per_node multiplies
    the entire curriculum by (1 + 2*lapse_rate), so the inflated rate pushed
    the reader's estimated finish toward the 36 min/node ceiling. `reps` is a
    ladder position, not a tally; `reviews` is the tally, and nothing resets it.
    """
    cid = _add_due_card(store, node_id='n1')
    _drill(store, cid, [5] * 10 + [0])

    card = _raw(store, "SELECT reps, lapses, reviews FROM srs_cards WHERE id=?", cid)[0]
    assert card['reps'] == 0 and card['lapses'] == 1, 'SM-2 still resets the ladder'
    assert card['reviews'] == 11, 'the tally must count every graded review'

    s = store.deck_stats()
    assert s['reviews_graded'] == 11
    assert s['lapse_rate'] == pytest.approx(1 / 11), \
        'one failure in eleven reviews is not a lapse rate of 1.0'


def test_the_inflated_lapse_rate_no_longer_inflates_the_plan():
    """The end of the chain the bug above rode: deck -> lapse_rate -> minutes
    per node -> estimated_years. Priced honestly, one bad review in eleven must
    cost the reader far less than being wrong nine times in ten."""
    from primer.pacing import srs_minutes_per_node
    s = _fresh_store()
    for i in range(3):
        _drill(store=s, card_id=_add_due_card(s, node_id='n1', ef=2.5 + i / 100.0),
               qualities=[5] * 10 + [0])
    deck = s.deck_stats()
    assert deck['lapse_rate'] == pytest.approx(3 / 33)
    honest = srs_minutes_per_node(deck)
    inflated = srs_minutes_per_node(dict(deck, lapse_rate=1.0))
    assert inflated > 2 * honest, \
        'the old reading priced this deck at {} min/node, not {}'.format(inflated, honest)


def test_a_pre_reviews_database_keeps_its_history(tmp_path):
    """Migration: a card graded before the column existed still has to count.

    reps+lapses is a lower bound (it lost the successes that preceded a lapse),
    but it is the only record those rows have, and a rate is better served by a
    stale lower bound than by a denominator of zero.
    """
    db = str(tmp_path / 'legacy.db')
    old = LearnerStore(db)
    old.add_cards([{'front': 'a', 'back': 'b', 'node_id': 'n1'}])
    _raw(old, "UPDATE srs_cards SET reps=7, lapses=1")
    _raw(old, "ALTER TABLE srs_cards DROP COLUMN reviews")
    assert 'reviews' not in {r['name'] for r in
                             _raw(old, "SELECT name FROM pragma_table_info('srs_cards')")}

    migrated = LearnerStore(db)          # re-open: migrations run on construction
    assert _raw(migrated, "SELECT reviews FROM srs_cards")[0]['reviews'] == 8
    assert migrated.deck_stats()['lapse_rate'] == pytest.approx(1 / 8)


# ---------------- 17. each calibration rate over its own population ---------


def test_each_calibration_rate_is_over_its_own_direction(store):
    """Regression: `total` was every rated answer, so both rates shared a
    denominator neither was a rate over.

    Overconfidence means "of the answers you were sure about, how many were
    wrong". Counting mid-confidence answers in that denominator diluted it with
    answers that could not possibly be in the numerator, so a reader who rates
    most answers a cautious 2 was systematically under-flagged against the 1/3
    limit — the more honestly they used the middle of the scale, the safer the
    book thought they were.
    """
    store.log_event('calibration', {
        'node': 'n', 'overconfident': 1, 'underconfident': 2,
        'confident_total': 3, 'hesitant_total': 2, 'total': 12})
    assert store.overconfidence_rate() == pytest.approx(1 / 3), 'one wrong of three confident'
    assert store.underconfidence_rate() == pytest.approx(1.0), 'both hesitant answers right'
    # The shared denominator would have read 1/12 and 2/12 — both comfortably
    # inside the limit, for a reader who is wrong a third of the time when sure.
    assert store.overconfidence_rate() > 1 / 12


def test_calibration_events_written_before_the_split_still_read(store):
    """Old rows carry only `total`. Falling back to it reproduces the old
    (diluted) reading for that sitting, which is wrong but bounded — better
    than dividing by zero and calling a miscalibrated reader perfect."""
    store.log_event('calibration', {'node': 'n', 'overconfident': 2,
                                    'underconfident': 0, 'total': 8})
    assert store.overconfidence_rate() == pytest.approx(2 / 8)


# ---------------- 18. a rate needs a sample, and a ramp not a cliff ---------


def test_one_answer_cannot_declare_a_reader_overconfident(store):
    """Regression: a single confident-and-wrong answer produced a rate of 1.0,
    which capped every self-graded restore and froze durability growth on a
    sample size of one. Below the floor we do not claim to have measured."""
    store.log_event('calibration', {'node': 'n', 'overconfident': 1,
                                    'underconfident': 0,
                                    'confident_total': 1, 'total': 1})
    assert store.overconfidence_rate() == 0.0
    assert store.underconfidence_rate() == 0.0

    # ...and once there is a sample, the measurement resumes.
    store.log_event('calibration', {'node': 'n', 'overconfident': 3,
                                    'underconfident': 0,
                                    'confident_total': 5, 'total': 5})
    assert store.overconfidence_rate() > 1 / 3


def test_the_overconfidence_threshold_is_a_ramp_not_a_cliff():
    """Regression: the limit was a hard binary at exactly 1/3, so a reader at
    0.333 and one at 0.334 — one answer in three hundred apart — got different
    kinds of treatment from every path that consults it."""
    from primer.learner import LearnerStore as L
    just_under = L._miscalibration(1 / 3 - 1e-4, L.OVERCONFIDENCE_LIMIT)
    just_over = L._miscalibration(1 / 3 + 1e-4, L.OVERCONFIDENCE_LIMIT)
    assert just_under == 0.0
    assert just_over < 0.001, 'crossing the limit must cost almost nothing'
    ramp = [L._miscalibration(r / 20.0, L.OVERCONFIDENCE_LIMIT) for r in range(21)]
    assert ramp == sorted(ramp), 'the discount must be monotone in the rate'
    assert ramp[0] == 0.0 and ramp[-1] == 1.0


# ---------------- 19. the half-life ceiling takes tens of reinforcements ----


def test_the_half_life_ceiling_is_not_reachable_in_a_week():
    """Regression: growth was linear at step 2.2, which reached the 365-day
    ceiling at the 7th reinforcement — one week of daily spaced practice, the
    exact failure the constant's own comment claimed to have fixed. Growth is
    sub-linear now (sqrt), so each spaced retrieval buys less than the last and
    the ceiling is a destination rather than a landing."""
    import primer.learner as lm
    ceiling = next(r for r in range(1, 500)
                   if lm._half_life(r) >= lm.STRENGTH_HALF_LIFE_MAX)
    assert ceiling >= 30, 'ceiling reached at reinforcement {}'.format(ceiling)
    # Sub-linear: every step must be smaller than the one before it.
    steps = [lm._half_life(r + 1) - lm._half_life(r) for r in range(1, 10)]
    assert steps == sorted(steps, reverse=True), 'growth must have diminishing returns'
    assert lm._half_life(1) == pytest.approx(lm.STRENGTH_HALF_LIFE)


def test_the_interval_cap_still_tracks_the_half_life_the_reader_has_reached():
    """The cap is tied to the half-life a reader has actually *reached* by the
    time SM-2 schedules that far out, not to the ceiling they may never see —
    that distinction was invisible under linear growth and is load-bearing now.
    """
    import math
    import primer.learner as lm
    interval, reinforcements = 0.0, 1
    for rep in range(1, 12):
        interval = (lm.SM2_FIRST_INTERVAL if rep == 1 else
                    lm.SM2_SECOND_INTERVAL if rep == 2 else interval * 2.5)
        interval = min(interval, lm.MAX_INTERVAL_DAYS)
        reinforcements += 1
        survives = (lm._half_life(reinforcements) / DAY) * math.log(lm.FRESH_GATE, 0.5)
        assert survives > interval, \
            'rep {}: scheduled {:.0f}d but only {:.0f}d survive above the gate'.format(
                rep, interval, survives)


# ---------------- 20. placement credit expires by name, not by silence -----


def test_placement_credit_does_not_quietly_evaporate(store):
    """Regression: `seed_assumed` wrote strength 0.8 at one reinforcement, so
    credit crossed the 0.35 gate at about day 36. Five weeks after a placement
    interview every credited node re-locked, the roadmap re-inflated, and
    `mastery_detail` reported mastered/proven/assumed/faded ALL false — the
    reader could not be told what had happened because nothing recorded it.

    Credit is not a memory. Only a test can disconfirm it, so it holds the gate
    until it expires, and expiry is a state with a name.
    """
    from primer.learner import ASSUMED_CREDIT_LIFE
    store.seed_assumed(['n'])

    def at(days):
        _raw(store, "UPDATE mastery SET last_seen=?, mastered_at=? WHERE node_id='n'",
             time.time() - days * DAY, time.time() - days * DAY)
        return store.gate_map()['n'], store.mastery_detail('n')

    for days in (0, 37, 100, 179):
        gate, d = at(days)
        assert gate == 1.0, 'day {}: placement credit must still open its gate'.format(days)
        assert d['assumed'] and not d['assumed_stale']

    gate, d = at(ASSUMED_CREDIT_LIFE / DAY + 1)
    assert gate < 1.0, 'credit is not permanent either'
    assert d['assumed'] and d['assumed_stale'], \
        'expired credit must be nameable — silence is what the reader saw before'
    assert 'n' in store.assumed_stale_set()


def test_credit_that_has_been_tested_decays_like_the_evidence_it_now_is(store):
    """The hold is only for nodes the book has never tested. Once a real pass
    is on the record, the node has evidence behind it and evidence fades."""
    store.seed_assumed(['n'])
    store.record_attempt('n', 1.0)          # one genuine pass: still `assumed`, now tested
    _raw(store, "UPDATE mastery SET last_seen=? WHERE node_id='n'", time.time() - 400 * DAY)
    assert store.gate_map()['n'] < 1.0, 'tested nodes are not held open by credit'
    assert 'n' not in store.assumed_stale_set()


# ---------------- 21. a node is not its easiest card -----------------------


def test_one_easy_card_cannot_carry_a_lapsed_node(store):
    """Regression: any single q>=4 review set the node's strength to 1.0
    outright, so the one card a reader finds trivial kept the whole node
    reading fully retained while its siblings sat lapsed and overdue."""
    _seed_faded_mastered(store, node_id='n1')
    easy = _add_due_card(store, node_id='n1')
    for i in range(3):
        sick = _add_due_card(store, node_id='n1', ef=2.5 + (i + 1) / 100.0)
        _raw(store, "UPDATE srs_cards SET due=?, reps=0, lapses=3 WHERE id=?",
             time.time() - 10 * DAY, sick)
    store.review_card(easy, 5)
    carried = _raw(store, "SELECT strength FROM mastery WHERE node_id='n1'")[0]['strength']
    assert carried < 1.0, 'three lapsed siblings cannot be worth nothing'

    healthy = _fresh_store()
    _seed_faded_mastered(healthy, node_id='n1')
    only = _add_due_card(healthy, node_id='n1')
    healthy.review_card(only, 5)
    solo = _raw(healthy, "SELECT strength FROM mastery WHERE node_id='n1'")[0]['strength']
    assert solo == pytest.approx(1.0), 'a node whose whole deck is healthy still restores fully'
    assert solo > carried


def test_a_readers_own_cards_neither_prop_up_nor_hold_down_a_node(store):
    """Reader-authored cards are notes, not evidence — they cannot restore a
    node, and by the same argument a neglected pile of them cannot drag one
    down when the book's own cards are in good order."""
    _seed_faded_mastered(store, node_id='n1')
    book = _add_due_card(store, node_id='n1')
    for i in range(4):
        mine = _add_due_card(store, node_id='n1', origin='reader', ef=2.5 + (i + 1) / 100.0)
        _raw(store, "UPDATE srs_cards SET due=?, reps=0, lapses=3 WHERE id=?",
             time.time() - 10 * DAY, mine)
    store.review_card(book, 5)
    assert _raw(store, "SELECT strength FROM mastery WHERE node_id='n1'")[0]['strength'] \
        == pytest.approx(1.0)
