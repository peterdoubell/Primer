"""Cost regressions: the shapes that made hot endpoints slow, held down.

These are not timing tests. A wall-clock threshold on a shared machine is a
coin flip, and a flaky guard gets deleted rather than fixed. Each test here
pins the *shape* of the work instead — how many connections a call opens, how
many times an inner routine runs, whether a memo is consulted — so a
regression fails the same way on a laptop and on a loaded CI box.

They exist because the streak walk had gone quadratic without anyone noticing:
one /api/today asked four questions that were all the same walk over the same
four hundred days, at 11 ms each, and re-derived it from scratch every time.
That was 36 of the endpoint's 57 ms. Nothing about the reader's experience
said so, and no test failed, which is exactly why these are here.
"""

import os
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer import learner as lm            # noqa: E402
from primer import store as store_mod       # noqa: E402
from primer.learner import LearnerStore     # noqa: E402


DAY = 86400.0


@pytest.fixture()
def store(tmp_path):
    return LearnerStore(str(tmp_path / "perf.db"))


# --------------------------------------------------------------------------
# The walk itself
# --------------------------------------------------------------------------

def _reference_bridged(days, anchor):
    """The pre-optimisation walk, kept verbatim as the oracle.

    The fast version bisects for the right edge and walks by index instead of
    filtering the whole history into a fresh list per anchor. That is only
    worth having if it is the *same* walk, so the two are compared directly
    rather than the new one being spot-checked against hand-written answers.
    """
    relevant = [d for d in days if d <= anchor]
    if not relevant:
        return 0, 0
    run = 0
    spent = []
    expect = anchor
    for d in reversed(relevant):
        gap = expect - d
        if gap:
            nearby = [s for s in spent if s - d < lm.STREAK_FREEZE_RENEW_DAYS]
            if len(nearby) + gap > lm.STREAK_FREEZES:
                break
            spent.extend(d + 1 + i for i in range(gap))
        run += 1
        expect = d - 1
    used = sum(1 for s in spent if anchor - s < lm.STREAK_FREEZE_RENEW_DAYS)
    return run, used


def _reference_walk(days, today):
    if not days:
        return 0, lm.STREAK_FREEZES, 0
    anchor = days[-1] if days[-1] >= today - 1 else today - 1
    current, used = _reference_bridged(days, anchor)
    best = max((_reference_bridged(days, a)[0] for a in days), default=0)
    best = max(best, current)
    return current, max(0, lm.STREAK_FREEZES - used), best


def _patterns():
    """Day histories that exercise every branch of the bridging rule."""
    base = 739000
    return [
        [],
        [base],
        list(range(base, base + 400)),                       # perfect attendance
        list(range(base, base + 200)) + list(range(base + 260, base + 400)),
        [base + i for i in range(0, 400, 2)],                # every other day
        [base + i for i in range(0, 400, 3)],                # every third day
        list(range(base, base + 30)) + [base + 60] + list(range(base + 90, base + 120)),
        list(range(base, base + 10)) + list(range(base + 11, base + 25))
        + list(range(base + 27, base + 100)),                # two bridgeable gaps
        sorted({base + (i * 7919) % 500 for i in range(220)}),   # ragged
    ]


def test_the_fast_walk_answers_exactly_what_the_old_one_did():
    base = 739000
    for days in _patterns():
        for today in (base - 1, base, base + 200, base + 399, base + 400,
                      base + 401, base + 600):
            assert lm._streak_walk_from_days(tuple(days), today) == \
                _reference_walk(days, today), \
                "walk diverged on {} days at today={}".format(len(days), today)


def test_a_single_run_never_rescans_the_whole_history_per_anchor(monkeypatch):
    """The best-streak scan must stop once no earlier anchor can win.

    A run ending at the i-th active day is at most i + 1 days long, so once
    the index falls to the best already found, every remaining anchor is
    provably a loser. Without that, the scan is one full walk per active day —
    quadratic in the length of the reader's history, and the reason four
    identical questions cost 44 ms on /api/today.

    Counted rather than timed: the count is the same on every machine.
    """
    days = tuple(range(739000, 739000 + 400))     # 400 days, no gaps
    calls = []
    real = lm._bridged_run_ending_at
    monkeypatch.setattr(lm, "_bridged_run_ending_at",
                        lambda d, a: (calls.append(a), real(d, a))[1])
    lm._streak_walk_from_days(days, 739399)
    assert len(calls) < 50, \
        "the anchor scan ran {} walks over a 400-day history".format(len(calls))


def test_the_walk_is_memoised_on_the_days_it_was_given():
    """Four of /api/today's questions are one walk. It should be computed once.

    The memo is exact rather than a staleness trade: the walk reads nothing
    but the set of active days and which day is today, so an event on a day
    already in the set cannot change the answer, and an event on a new day
    changes the key.
    """
    rows = tuple("2024-01-{:02d}".format(i) for i in range(1, 29))
    lm._streak_walk_from_rows.cache_clear()
    first = lm._streak_walk_from_rows(rows, 739000)
    hits_before = lm._streak_walk_from_rows.cache_info().hits
    for _ in range(5):
        assert lm._streak_walk_from_rows(rows, 739000) == first
    assert lm._streak_walk_from_rows.cache_info().hits == hits_before + 5
    # A different day, or a different history, is a different question.
    assert lm._streak_walk_from_rows(rows + ("2024-01-29",), 739000) is not None
    assert lm._streak_walk_from_rows.cache_info().misses >= 2


# --------------------------------------------------------------------------
# Connections opened, which is what the hosted path is actually billed in
# --------------------------------------------------------------------------

def _count_connections(monkeypatch, fn):
    """How many times `fn` opens the store, on this thread only.

    Local SQLite makes this look free. Turso does not: every connect() is an
    HTTPS client and every statement on it is a round trip, so the count is
    the honest unit of cost for the deployed book.

    Only this thread's opens are counted. `store.connect` is a module global,
    and by the time these run a full suite has left several of the server's
    daily-maintenance daemon threads alive (each TestClient lifespan starts
    one, and `_shutdown` is a module-level Event that is never cleared, so a
    later one runs a whole backup-and-prune pass before noticing it should
    stop). Those threads open connections of their own against their own
    databases. Counting them would make this test a measurement of whichever
    files pytest happened to run first.
    """
    opened = []
    real = store_mod.connect
    mine = threading.get_ident()

    def counting(*a, **k):
        if threading.get_ident() == mine:
            opened.append(1)
        return real(*a, **k)

    monkeypatch.setattr(store_mod, "connect", counting)
    fn()
    return len(opened)


def test_reading_the_profile_takes_one_connection(store, monkeypatch):
    """get_profile() rides on almost every route the reader touches.

    It used to open three connections — the row, then total_xp(), then
    streak_days() — each a fresh client and a fresh round trip against Turso.
    Same three queries, one connection.
    """
    store.save_profile("Nell", 12, 20, "balanced", 2, ["math"])
    store.log_event("read", {"title": "Anything"}, xp=3)
    assert _count_connections(monkeypatch, store.get_profile) == 1


def test_the_streak_walk_takes_one_connection(store, monkeypatch):
    store.log_event("read", {"title": "Anything"}, xp=1)
    assert _count_connections(monkeypatch, store._streak_walk) == 1


def test_the_profile_still_reports_the_numbers_it_always_did(store):
    """The one-connection read must not have changed a single answer."""
    now = time.time()
    store.save_profile("Nell", 12, 20, "balanced", 2, ["math"])
    for back in (2, 1, 0):
        with lm._lock, store._conn() as c:
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", now - back * DAY, 5))
    prof = store.get_profile()
    assert prof["xp"] == store.total_xp() == 15
    assert prof["streak"] == store.streak_days() == 3


def test_pending_proofs_is_still_one_query_not_a_loop(store, monkeypatch):
    """The trap this function was written to avoid, pinned.

    mastery_detail() opens a connection per node. pending_proofs() answers the
    same question for every node at once, and /api/today reads it on every
    load — so it must never quietly become a loop over the per-node version.
    """
    now = time.time()
    with lm._lock, store._conn() as c:
        for i in range(40):
            c.execute(
                "INSERT INTO mastery(node_id, level, passes, first_pass_at, "
                "strength, last_seen, assumed, reinforcements) "
                "VALUES(?,?,?,?,?,?,0,1)",
                ("n{}".format(i), 0.85, 1, now - DAY, 1.0, now - DAY))
    assert _count_connections(monkeypatch, store.pending_proofs) == 1
    assert len(store.pending_proofs()) == 40
