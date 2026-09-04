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
