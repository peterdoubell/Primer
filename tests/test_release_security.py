"""Backup retention must never touch unrelated or redirected local files."""

import os
from pathlib import Path
import sqlite3

import pytest

import primer.learner as learner_mod
from primer.learner import LearnerStore


STAMP = "20260304-123456"
BACKUP_NAME = "primer-" + STAMP + ".db"
SIDECARS = ("-wal", "-shm", "-journal")


@pytest.fixture(autouse=True)
def isolated_backup_clock(monkeypatch):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    original = learner_mod.time.strftime
    monkeypatch.setattr(learner_mod.time, "strftime", lambda fmt, *args:
                        STAMP if fmt == "%Y%m%d-%H%M%S" else original(fmt, *args))


@pytest.fixture
def reader(tmp_path):
    store = LearnerStore(str(tmp_path / "reader.db"))
    store.save_profile("Ada", 11, 8, "balanced", 0, ["math"], {})
    return store


def test_retention_only_removes_generated_primer_backups(reader, tmp_path):
    directory = tmp_path / "shared backups"
    directory.mkdir()
    unrelated = [directory / name for name in (
        "accounts.db", "primer-not-a-date.db", "primer-20261301-000000.db",
        "primer-20260101-000000.db.backup")]
    for path in unrelated:
        path.write_bytes(b"unrelated database")
    old = directory / "primer-20000101-000000.db"
    for suffix in ("",) + SIDECARS:
        Path(str(old) + suffix).write_bytes(b"old backup")

    destination = reader.backup(str(directory), keep=1)

    assert destination == str(directory / BACKUP_NAME)
    assert Path(destination).is_file()
    assert all(path.read_bytes() == b"unrelated database" for path in unrelated)
    assert not any(Path(str(old) + suffix).exists() for suffix in ("",) + SIDECARS)


@pytest.mark.parametrize("suffix", ("",) + SIDECARS)
def test_backup_refuses_symlink_destinations_and_sqlite_sidecars(reader, tmp_path, suffix):
    directory = tmp_path / "backups"
    directory.mkdir()
    outside = tmp_path / "outside.db"
    outside.write_bytes(b"outside sentinel")
    redirected = directory / (BACKUP_NAME + suffix)
    redirected.symlink_to(outside)

    assert reader.backup(str(directory)) is None
    assert outside.read_bytes() == b"outside sentinel"
    assert redirected.is_symlink()
    if suffix:
        assert not (directory / BACKUP_NAME).exists()


@pytest.mark.parametrize("suffix", ("",) + SIDECARS)
def test_cleanup_rejects_the_whole_backup_when_one_member_is_a_symlink(tmp_path, suffix):
    directory = tmp_path / "backups"
    directory.mkdir()
    outside = tmp_path / "outside.db"
    outside.write_bytes(b"outside sentinel")
    base = directory / BACKUP_NAME
    for member in ("",) + SIDECARS:
        path = Path(str(base) + member)
        if member == suffix:
            path.symlink_to(outside)
        else:
            path.write_bytes(b"kept backup member")

    learner_mod._remove_backup(str(base))

    assert outside.read_bytes() == b"outside sentinel"
    assert Path(str(base) + suffix).is_symlink()
    for member in ("",) + SIDECARS:
        if member != suffix:
            assert Path(str(base) + member).read_bytes() == b"kept backup member"


@pytest.mark.parametrize("suffix", ("",) + SIDECARS)
def test_shrinking_never_opens_a_redirected_backup(tmp_path, monkeypatch, suffix):
    directory = tmp_path / "backups"
    directory.mkdir()
    base = directory / BACKUP_NAME
    outside = tmp_path / "outside.db"
    outside.write_bytes(b"outside sentinel")
    if suffix:
        base.write_bytes(b"backup sentinel")
    Path(str(base) + suffix).symlink_to(outside)
    monkeypatch.setattr(learner_mod, "_SHRINK_BACKUP_ABOVE", 0)
    monkeypatch.setattr(learner_mod.sqlite3, "connect", lambda *_args, **_kwargs:
                        pytest.fail("A redirected database must never be opened"))

    learner_mod._shed_wiki_cache(str(base))

    assert outside.read_bytes() == b"outside sentinel"
    assert Path(str(base) + suffix).is_symlink()


def test_same_directory_symlinks_are_refused_too(tmp_path):
    target = tmp_path / "other.db"
    target.write_bytes(b"same-directory sentinel")
    base = tmp_path / BACKUP_NAME
    base.symlink_to(target)
    learner_mod._remove_backup(str(base))
    assert base.is_symlink()
    assert target.read_bytes() == b"same-directory sentinel"


def test_cleanup_rejects_hardlinks_to_another_database(tmp_path):
    outside = tmp_path / "outside.db"
    outside.write_bytes(b"hardlink sentinel")
    base = tmp_path / BACKUP_NAME
    os.link(outside, base)
    assert learner_mod._checked_backup_path(str(base)) is None
    learner_mod._remove_backup(str(base))
    assert base.read_bytes() == outside.read_bytes() == b"hardlink sentinel"


def test_cleanup_refuses_lexical_traversal_and_captured_root_escapes(tmp_path):
    directory = tmp_path / "backups"
    directory.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / BACKUP_NAME
    victim.write_bytes(b"outside sentinel")
    traversal = str(directory / ".." / "outside" / BACKUP_NAME)
    assert learner_mod._checked_backup_path(traversal, str(directory)) is None
    assert learner_mod._checked_backup_path(str(victim), str(directory)) is None
    learner_mod._remove_backup(traversal)
    assert victim.read_bytes() == b"outside sentinel"


def test_explicit_configured_storage_root_is_preserved(reader, tmp_path):
    mounted = tmp_path / "mounted storage" / "reader backups"
    mounted.mkdir(parents=True)
    # A directory alias explicitly chosen by the administrator is resolved
    # once; generated DBs and sidecars inside it may never redirect elsewhere.
    configured = tmp_path / "configured storage"
    configured.symlink_to(mounted, target_is_directory=True)
    destination = reader.backup(str(configured))
    assert destination == str(mounted / BACKUP_NAME)
    with sqlite3.connect(destination) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("SELECT name FROM profile").fetchone()[0] == "Ada"


def test_backup_never_overwrites_or_rotates_its_live_source(tmp_path):
    directory = tmp_path / "backups"
    directory.mkdir()
    source = directory / "primer-20000101-000000.db"
    reader = LearnerStore(str(source))
    reader.save_profile("Ada", 11, 8, "balanced", 0, ["math"], {})
    destination = reader.backup(str(directory), keep=1)
    assert destination and source.is_file()
    assert reader.get_profile()["name"] == "Ada"

    current = LearnerStore(destination)
    assert current.backup(str(directory)) is None
    assert current.get_profile()["name"] == "Ada"
