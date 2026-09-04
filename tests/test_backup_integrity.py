"""The backup is the reader's record, and only the reader's record.

The Primer's whole promise is a multi-year history that survives — which makes
`LearnerStore.backup()` the most load-bearing few lines in the project, and it
had never been tested for what it actually produces.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



@pytest.fixture
def shrink_small_backups():
    """Lower the shrink threshold for one test, and put it back.

    The production threshold sits far above anything a test should write, so
    exercising the shedding path means lowering it — and an earlier version of
    this file simply assigned the module global and walked away. That left every
    backup for the rest of the session trying to VACUUM, which is exactly the
    extra pressure that made an unrelated backup fail with "disk I/O error"
    later in the run. A test that changes a global owns putting it back.
    """
    import primer.learner as learner_mod
    original = learner_mod._SHRINK_BACKUP_ABOVE
    learner_mod._SHRINK_BACKUP_ABOVE = 100_000
    try:
        yield
    finally:
        learner_mod._SHRINK_BACKUP_ABOVE = original


def test_a_backup_keeps_the_record_and_sheds_the_cache(tmp_path, shrink_small_backups):
    """A backup of the irreplaceable record should be the record.

    One SQLite file holds two unlike things: the reader's multi-year history,
    which nothing can reconstruct, and the wiki article/image caches, which are
    bytes from a ZIM file or a URL away. `backup()` page-copied the whole file,
    so every "backup of the learner record" was in practice 319 MB of
    disposable cache around about a megabyte of the reader's actual life — and
    five rotated generations of it. This asserts the copy is the record: cache
    tables gone, profile and mastery intact, and one file rather than a .db
    with -wal/-shm sidecars a restore would leave behind.
    """
    import sqlite3
    from primer.learner import LearnerStore
    from primer.wiki import WikiService

    db = str(tmp_path / "primer.db")
    store = LearnerStore(db)
    WikiService(db)                      # creates the cache tables in the same file
    store.save_profile("Ada", 11, 8, "balanced", 0, ["math"], {})

    con = sqlite3.connect(db)
    cols = [r[1] for r in con.execute("PRAGMA table_info(article_cache)")]
    for i in range(20):
        con.execute("INSERT OR REPLACE INTO article_cache VALUES (%s)"
                    % ",".join("?" * len(cols)),
                    [("t%d" % i) if c in ("title", "key") else "x" * 100_000
                     for c in cols])
    con.commit()
    con.close()

    source_size = os.path.getsize(db)
    dest_dir = str(tmp_path / "backups")
    dest = store.backup(dest_dir)
    assert dest, "backup did not complete"

    assert os.path.getsize(dest) < source_size / 10, (
        "the backup is still carrying the wiki cache: %d vs %d bytes"
        % (os.path.getsize(dest), source_size))

    copy = sqlite3.connect(dest)
    try:
        tables = {r[0] for r in copy.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        assert "article_cache" not in tables and "image_cache" not in tables
        assert copy.execute("SELECT name FROM profile").fetchone()[0] == "Ada"
        assert copy.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        copy.close()

    strays = [f for f in os.listdir(dest_dir) if f.endswith(("-wal", "-shm"))]
    assert not strays, "a finished backup left sidecars behind: %s" % strays


def test_rotating_a_backup_out_takes_its_sidecars_with_it(tmp_path):
    """Retention deleted the .db and left the -wal/-shm for ever.

    Both retention paths filtered on the `.db` suffix and removed only that
    file, so each rotated-out generation left two orphans nothing would ever
    collect — 672 of them had piled up in one real backup directory.
    """
    from primer.learner import _remove_backup

    dest_dir = tmp_path / "backups"
    dest_dir.mkdir()
    base = dest_dir / "primer-20260101-000000.db"
    for suffix in ("", "-wal", "-shm"):
        (dest_dir / (base.name + suffix)).write_text("x")
    _remove_backup(str(base))
    assert not list(dest_dir.iterdir()), (
        "sidecars survived retention: %s" % [p.name for p in dest_dir.iterdir()])


def test_a_backup_survives_a_failed_shrink(tmp_path, caplog):
    """Shrinking the copy is an optimisation and must never cost the backup.

    The first version of the cache-shedding ran mid-copy, inside the try that
    discards a failed backup — so an OperationalError from VACUUM (a full disk,
    an unwritable temp directory, an exhausted file-descriptor table under a
    long test run) threw away a sound copy and returned None. That is a far
    worse bug than the one it was fixing: it turns "your backup is bigger than
    it needs to be" into "you have no backup". Shrinking now runs last, on its
    own connection, outside that try, and behind its own guard.
    """
    import sqlite3
    import primer.learner as learner_mod
    from primer.learner import LearnerStore

    db = str(tmp_path / "primer.db")
    store = LearnerStore(db)
    store.save_profile("Ada", 11, 8, "balanced", 0, ["math"], {})

    def explode(_path):
        raise sqlite3.OperationalError("disk I/O error")

    real, learner_mod._shed_wiki_cache = learner_mod._shed_wiki_cache, explode
    try:
        dest = store.backup(str(tmp_path / "backups"))
    finally:
        learner_mod._shed_wiki_cache = real

    assert dest, "a failed shrink destroyed the backup"
    copy = sqlite3.connect(dest)
    try:
        assert copy.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert copy.execute("SELECT name FROM profile").fetchone()[0] == "Ada"
    finally:
        copy.close()


def test_revoking_assumed_credit_keeps_what_was_earned(tmp_path):
    """Withdrawing an assumption must not erase evidence.

    `assumed` stays 1 through a genuine passing attempt — `_apply_attempt_once`
    clears it only on the branch where mastery is fully earned. So a
    placement-credited node the reader had since sat and passed once still
    matched `assumed=1`, and `DELETE ... WHERE assumed=1` took the whole row:
    the pass, its timestamp, the attempts, the strength. A later placement that
    moved the reader down did not just withdraw an assumption, it made them
    earn that first pass again.
    """
    from primer.learner import LearnerStore

    store = LearnerStore(str(tmp_path / "primer.db"))
    store.save_profile("Ada", 11, 8, "balanced", 0, ["math"], {})

    store.seed_assumed(["math.2.fractions", "math.2.decimals"])
    # One honest pass on one of them; the other stays a bare assumption.
    store.record_attempt("math.2.fractions", 0.9)
    before = store.mastery_detail("math.2.fractions")
    assert before["passes"] == 1

    store.revoke_assumed(["math.2.fractions", "math.2.decimals"])

    kept = store.mastery_detail("math.2.fractions")
    assert kept, "the row with a real pass behind it was deleted outright"
    assert kept["passes"] == 1, "a genuine passing attempt was erased"
    assert not kept.get("assumed"), "the assumption should be gone"
    assert not kept.get("mastered_at"), "credit-derived mastery should be gone"

    # A bare assumption still goes entirely.
    assert not store.mastery_map().get("math.2.decimals")


def test_a_card_blanked_minutes_ago_cannot_restore_the_node(tmp_path):
    """Ten minutes of short-term memory is not evidence against forgetting.

    On a lapse the card is rescheduled RELEARN_DELAY (10 min) out with reps and
    interval zeroed. Nothing in the q>=4 branch asked how long ago the reader
    had last seen it, so blanking a card and immediately passing it restored
    the node's strength to target and restarted the decay clock — lifting it
    back over the freshness gate the blank had just closed. The honest path
    (blank, come back tomorrow) must still be credited, so the discriminator is
    elapsed time, not the relearning state.
    """
    from primer.learner import LearnerStore, RELEARN_DELAY

    store = LearnerStore(str(tmp_path / "primer.db"))
    store.save_profile("Ada", 30, 8, "balanced", 0, ["math"], {})
    store.record_attempt("math.2.fractions", 0.95)
    store.add_cards([{"front": "1/2 + 1/4", "back": "3/4",
                      "node_id": "math.2.fractions", "article": "Fraction"}])
    card = store.due_cards(limit=5)[0] if store.due_cards(limit=5) else None
    if card is None:                      # a new card waits RELEARN_DELAY
        import sqlite3
        con = sqlite3.connect(str(tmp_path / "primer.db"))
        con.execute("UPDATE srs_cards SET due = due - ?", (RELEARN_DELAY + 60,))
        con.commit(); con.close()
        card = store.due_cards(limit=5)[0]

    store.review_card(card["id"], 0)                 # blank it
    after_blank = store.mastery_map().get("math.2.fractions", 0)
    store.review_card(card["id"], 5)                 # ...and pass it right back
    after_repass = store.mastery_map().get("math.2.fractions", 0)

    assert after_repass <= after_blank + 1e-9, (
        "a re-pass inside the relearning window restored the node: %.3f -> %.3f"
        % (after_blank, after_repass))


def test_a_specialist_field_does_not_reprice_the_general_spine():
    """Each kind of field is priced against its own kind.

    Per-node minutes scale by content density against the stage's average. That
    was computed over every domain at once, which was harmless while the book
    held ten general fields of comparable depth — and stopped being harmless
    when a specialist field arrived carrying 3.7x the content per node. At
    stage 5 radiology pulled the average past every general node's density: 49
    of the 52 general graduate nodes sat on the 0.5 clamp floor, nine of ten
    general domains had their whole graduate tier priced at half, and the tier
    the instructional-time anchor rests on cost half what it claims.

    The invariant asserted here is the one the anchor actually makes: a group's
    mean node minutes stays near its stage's base. A bound-population heuristic
    would not have caught it — the nodes were all *at* a bound, legally.
    """
    from primer.curriculum import Curriculum, DEFAULT_MINUTES

    curr = Curriculum()
    specialist = {d["id"] for d in curr.domains if d.get("entry_stage", 0) > 0}
    assert specialist, "this test needs a specialist field to be meaningful"

    pools = {}
    for node in curr.nodes.values():
        pool = node["domain"] if node["domain"] in specialist else "general"
        pools.setdefault((node["stage"], pool), []).append(node["minutes"])

    for (stage, pool), minutes in sorted(pools.items()):
        mean = sum(minutes) / len(minutes)
        base = DEFAULT_MINUTES[stage]
        assert abs(mean - base) <= 0.35 * base, (
            "%s at stage %d averages %.0f minutes against a base of %d"
            % (pool, stage, mean, base))

    floor = 0.5 * DEFAULT_MINUTES[5]
    general_5 = [n for n in curr.nodes.values()
                 if n["stage"] == 5 and n["domain"] not in specialist]
    on_floor = [n["id"] for n in general_5 if n["minutes"] <= floor]
    assert len(on_floor) <= len(general_5) // 4, (
        "%d of %d general graduate nodes are on the clamp floor: %s"
        % (len(on_floor), len(general_5), on_floor[:5]))


def test_a_re_measurement_can_place_a_reader_down(tmp_path):
    """A re-check that can only ratchet upward is not a measurement.

    `reopen_placement` keeps the asked-history so the new sitting does not
    repeat items the reader has already seen — but `_placement_rung` and the
    settle both computed `max(passed) + 1` over the WHOLE list, so the previous
    run's passes went on setting the floor. A reader who had genuinely
    forgotten could be re-measured upward and never downward, which is half the
    bar's clause about placement gone.
    """
    import time
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as c:
            c.post("/api/profile", json={
                "name": "Ada", "age": 30, "hours_per_week": 8,
                "breadth": "balanced", "domains": ["math"]})

            def answer_key(paper):
                served = srv._SERVED[paper["token"]]["questions"]
                by_id = {q.get("id"): q.get("answer", "") for q in served}
                return [by_id.get(q["id"], "") for q in paper["questions"]]

            def sit(correct):
                for _ in range(8):
                    p = c.get("/api/placement/next?domain=math&n=4").json()
                    if not p.get("questions"):
                        return None
                    answers = (answer_key(p) if correct
                               else ["definitely wrong"] * len(p["questions"]))
                    r = c.post("/api/placement/submit", json={
                        "domain": "math", "stage": p["stage"],
                        "token": p["token"], "answers": answers}).json()
                    if r.get("settled"):
                        return r
                return None

            assert sit(True) is not None, "first placement never settled"
            high = c.get("/api/state").json()["profile"]["settings"]["placed"]["math"]
            assert high > 0, "the reader should have placed above zero"

            # Cool the placement off so it may be re-opened, then forget everything.
            with srv.learner._conn() as conn:
                conn.execute("UPDATE placement SET settled_at=?",
                             (time.time() - 30 * 86400,))
            assert srv.learner.reopen_placement("math") is True

            assert sit(False) is not None, "the re-measurement never settled"
            low = c.get("/api/state").json()["profile"]["settings"]["placed"]["math"]
            assert low < high, (
                "a re-check could not lower the reader: %s then %s" % (high, low))
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig
