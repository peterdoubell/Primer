"""The storage seam: local SQLite by default, Turso (libSQL) when configured.

Two things are being defended here, and only one of them is the new feature.

The first, and the one that actually matters, is that *nothing changed
locally*. `primer.store.connect()` with no environment set must hand back a
real `sqlite3.Connection` configured exactly as the three call sites used to
configure themselves — same WAL, same busy timeout, same `sqlite3.Row`. The
reader's multi-year record and the rest of this suite depend on it.

The second is that the remote adapter presents the same interface. libSQL is
wire-compatible SQLite, but its Python client is not a DB-API driver: no
`executescript`, no `.keys()` on rows, no cursor, no implicit transaction, and
its own exception hierarchy. Each of those gaps is papered over in store.py
and each one is pinned here.

No test needs the network or real Turso credentials: the adapter is exercised
either against a fake client or against a libSQL `file:` URL, which drives the
identical remote code path against a temp file.

Run:  .venv/bin/python -m pytest tests/test_aaa_store.py -q
"""

import os
import sqlite3
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer import store  # noqa: E402
from primer.learner import LearnerStore  # noqa: E402
from primer.sittings import SittingStore  # noqa: E402


@pytest.fixture(autouse=True)
def _no_inherited_turso(monkeypatch):
    """Every test states its own backend. A developer who happens to have
    TURSO_DATABASE_URL exported must not silently run the whole suite against
    their real cloud database."""
    monkeypatch.delenv(store.URL_ENV, raising=False)
    monkeypatch.delenv(store.TOKEN_ENV, raising=False)


# --------------------------------------------------------------------------
# Local mode: the non-negotiable half
# --------------------------------------------------------------------------

def test_local_connect_is_a_real_sqlite3_connection(tmp_path):
    conn = store.connect(str(tmp_path / 'a.db'))
    try:
        assert isinstance(conn, sqlite3.Connection)
        # Not a wrapper, not a subclass with surprises: the genuine article.
        assert type(conn) is sqlite3.Connection
    finally:
        conn.close()


def test_local_connect_applies_the_same_pragmas(tmp_path):
    conn = store.connect(str(tmp_path / 'b.db'))
    try:
        assert conn.execute('PRAGMA journal_mode').fetchone()[0] == 'wal'
        assert conn.execute('PRAGMA busy_timeout').fetchone()[0] == 8000
    finally:
        conn.close()


def test_local_connect_can_skip_wal_for_the_sittings_store(tmp_path):
    # SittingStore never set journal_mode; it inherits whatever the learner
    # store put on the same file. Opening it must not change the file's mode.
    path = str(tmp_path / 'c.db')
    conn = store.connect(path, wal=False)
    try:
        assert conn.execute('PRAGMA journal_mode').fetchone()[0] != 'wal'
    finally:
        conn.close()


def test_local_named_rows_are_sqlite3_rows(tmp_path):
    conn = store.connect(str(tmp_path / 'd.db'), named_rows=True)
    try:
        conn.execute('CREATE TABLE t (a TEXT, b INTEGER)')
        conn.execute("INSERT INTO t VALUES ('x', 2)")
        row = conn.execute('SELECT * FROM t').fetchone()
        assert isinstance(row, sqlite3.Row)
        assert row['a'] == 'x' and row[1] == 2
        assert dict(row) == {'a': 'x', 'b': 2}
    finally:
        conn.close()


def test_local_plain_rows_stay_tuples(tmp_path):
    conn = store.connect(str(tmp_path / 'e.db'))
    try:
        conn.execute('CREATE TABLE t (a TEXT)')
        conn.execute("INSERT INTO t VALUES ('x')")
        assert conn.execute('SELECT * FROM t').fetchone() == ('x',)
    finally:
        conn.close()


def test_local_store_round_trips_a_reader(tmp_path):
    """The end the reader sees: a profile that survives a re-open, which is
    exactly what the Vercel deployment could not do."""
    path = str(tmp_path / 'primer.db')
    first = LearnerStore(path)
    first.save_profile('Nell', 9.0, 5.0, 'wide', 1, ['math'])
    first.record_attempt('math.arith', 0.9)

    again = LearnerStore(path)
    assert again.get_profile()['name'] == 'Nell'
    assert again.mastery_map()['math.arith'] == pytest.approx(0.9)


def test_three_factories_all_route_through_the_seam(tmp_path, monkeypatch):
    """learner, wiki and sittings must share one connection factory — the
    whole point of store.py is that there is no second way in."""
    seen = []
    real = store.connect

    def spy(db_path, **kwargs):
        seen.append(os.path.basename(db_path))
        return real(db_path, **kwargs)

    monkeypatch.setattr(store, 'connect', spy)
    learner = LearnerStore(str(tmp_path / 'primer.db'))
    SittingStore(lambda: learner.db_path)['tok'] = {'at': 1.0, 'q': []}

    from primer.wiki import WikiService
    WikiService(str(tmp_path / 'wiki.db'))._conn().close()

    assert 'primer.db' in seen and 'wiki.db' in seen


# --------------------------------------------------------------------------
# Backend selection
# --------------------------------------------------------------------------

def test_selection_defaults_to_local():
    assert store.turso_url() is None
    assert store.using_turso() is False


def test_selection_reads_and_normalizes_the_env_at_call_time(monkeypatch):
    monkeypatch.setenv(store.URL_ENV, 'libsql://example.turso.io')
    assert store.using_turso() is True
    assert store.turso_url() == 'https://example.turso.io'
    monkeypatch.delenv(store.URL_ENV)
    assert store.using_turso() is False


def test_a_preview_deployment_never_reaches_the_remote_database(monkeypatch):
    """The guarantee that a pull request cannot migrate production.

    The Turso integration provisions one database across Production, Preview
    and Development, so a preview built from any open branch used to boot,
    run _init_db(), and apply that branch's migrations to the real reader's
    record — which is exactly how production once ended up running
    pre-migration code against a post-migration schema.
    """
    monkeypatch.setenv(store.URL_ENV, 'libsql://example.turso.io')
    monkeypatch.setenv('VERCEL_ENV', 'preview')
    assert store.turso_url() is None
    assert store.using_turso() is False


def test_production_and_local_still_reach_the_remote_database(monkeypatch):
    """The guard is aimed at previews only; it must not cost production its
    database, nor change what a laptop with no VERCEL_ENV at all does."""
    monkeypatch.setenv(store.URL_ENV, 'libsql://example.turso.io')
    for env in ('production', 'development'):
        monkeypatch.setenv('VERCEL_ENV', env)
        assert store.using_turso() is True, env
    monkeypatch.delenv('VERCEL_ENV', raising=False)
    assert store.using_turso() is True


def test_a_preview_with_its_own_database_may_opt_back_in(monkeypatch):
    """A preview pointed at a database of its own is a different thing from a
    preview pointed at production's, and only the operator can tell them
    apart — so the refusal is a default, not a wall."""
    monkeypatch.setenv(store.URL_ENV, 'libsql://preview-of-its-own.turso.io')
    monkeypatch.setenv('VERCEL_ENV', 'preview')
    monkeypatch.setenv(store.PREVIEW_REMOTE_ENV, '1')
    assert store.turso_url() == 'https://preview-of-its-own.turso.io'


def test_blank_env_var_still_means_local(monkeypatch):
    # A marketplace integration that provisions the variable but leaves it
    # empty must not break the local fallback into a connection attempt.
    monkeypatch.setenv(store.URL_ENV, '   ')
    assert store.using_turso() is False


def test_turso_env_selects_the_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv(store.URL_ENV, 'libsql://example.turso.io')
    monkeypatch.setenv(store.TOKEN_ENV, 'tok')
    captured = {}

    class _FakeModule(object):
        @staticmethod
        def create_client_sync(url, **kwargs):
            captured.update(url=url, kwargs=kwargs)
            return _FakeClient()

    monkeypatch.setitem(sys.modules, 'libsql_client', _FakeModule)
    conn = store.connect(str(tmp_path / 'ignored.db'))
    assert isinstance(conn, store._LibsqlConnection)
    assert captured['url'] == 'https://example.turso.io'
    assert captured['kwargs'] == {'auth_token': 'tok'}


# --------------------------------------------------------------------------
# The adapter, against a fake client (no dependency, no network)
# --------------------------------------------------------------------------

class _FakeResult(object):
    def __init__(self, columns, rows, rows_affected=0, last_insert_rowid=None):
        self.columns = columns
        self.rows = rows
        self.rows_affected = rows_affected
        self.last_insert_rowid = last_insert_rowid


class _FakeTxn(object):
    """A transaction over a scratch in-memory sqlite3 — enough to prove the
    adapter's own logic without asking anything of a network."""

    def __init__(self, client):
        self._client = client
        self.committed = self.rolled_back = False

    def execute(self, sql, params=None):
        self._client.statements.append(sql.strip())
        cur = self._client.raw.execute(sql, params or [])
        rows = cur.fetchall()
        cols = tuple(d[0] for d in cur.description) if cur.description else ()
        return _FakeResult(cols, rows, cur.rowcount if cur.rowcount > 0 else 0,
                           cur.lastrowid)

    def commit(self):
        self.committed = True
        self._client.raw.commit()

    def rollback(self):
        self.rolled_back = True
        self._client.raw.rollback()


class _FakeClient(object):
    def __init__(self):
        self.raw = sqlite3.connect(':memory:')
        self.raw.isolation_level = None
        self.statements = []
        self.transactions = []
        self.closed = False

    def transaction(self):
        txn = _FakeTxn(self)
        self.transactions.append(txn)
        return txn

    def close(self):
        self.closed = True


def _adapter(named_rows=False):
    client = _FakeClient()
    return store._LibsqlConnection('libsql://x', None, named_rows=named_rows,
                                   _client=client), client


def test_adapter_rows_behave_like_sqlite3_rows():
    conn, _ = _adapter(named_rows=True)
    with conn as c:
        c.execute('CREATE TABLE t (a TEXT, b INTEGER)')
        c.execute('INSERT INTO t VALUES (?, ?)', ['x', 2])
        row = c.execute('SELECT * FROM t').fetchone()
        # libSQL's own row has none of this: no keys(), and dict(row) raises.
        assert row['a'] == 'x'
        assert row[1] == 2
        assert row.keys() == ['a', 'b']
        assert dict(row) == {'a': 'x', 'b': 2}
        assert 'b' in row.keys() and 'nope' not in row.keys()


def test_adapter_missing_column_raises_indexerror_like_sqlite3():
    conn, _ = _adapter(named_rows=True)
    with conn as c:
        c.execute('CREATE TABLE t (a TEXT)')
        c.execute("INSERT INTO t VALUES ('x')")
        row = c.execute('SELECT * FROM t').fetchone()
        with pytest.raises(IndexError):
            row['missing']


def test_adapter_cursor_supports_fetch_and_iteration():
    conn, _ = _adapter()
    with conn as c:
        c.execute('CREATE TABLE t (a INTEGER)')
        for n in (1, 2, 3):
            c.execute('INSERT INTO t VALUES (?)', [n])
        assert c.execute('SELECT a FROM t ORDER BY a').fetchall() == [
            (1,), (2,), (3,)]
        assert [r[0] for r in c.execute('SELECT a FROM t ORDER BY a')] == [1, 2, 3]
        cur = c.execute('SELECT a FROM t ORDER BY a')
        assert cur.fetchone() == (1,)
        assert cur.fetchall() == [(2,), (3,)]
        # Past the end sqlite3 yields None, and callers test `if row is None`.
        assert c.execute('SELECT a FROM t WHERE a > 99').fetchone() is None


def test_adapter_executescript_splits_on_statements_not_semicolons():
    conn, client = _adapter()
    with conn as c:
        c.executescript("""
            CREATE TABLE t (a TEXT);
            INSERT INTO t VALUES ('one; still one');
            CREATE INDEX IF NOT EXISTS idx_t ON t (a);
        """)
        # Three statements, not four: the semicolon inside the literal did not
        # split anything.
        assert len(client.statements) == 3
        assert c.execute('SELECT a FROM t').fetchone() == ('one; still one',)


def test_adapter_executemany_and_total_changes():
    conn, _ = _adapter()
    with conn as c:
        c.execute('CREATE TABLE t (a INTEGER)')
        c.executemany('INSERT INTO t VALUES (?)', [(1,), (2,), (3,)])
        before = c.total_changes
        c.executemany('DELETE FROM t WHERE a=?', [(1,), (2,)])
        assert c.total_changes - before == 2


def test_adapter_local_only_pragmas_are_no_ops():
    conn, client = _adapter()
    with conn as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('PRAGMA busy_timeout=8000')
    # Neither reached the server: WAL and lock timeouts describe a local file
    # and a local lock, neither of which exists behind an HTTP endpoint.
    assert not any('PRAGMA' in s.upper() for s in client.statements)


def test_adapter_informational_pragmas_do_execute():
    # The learner's migrations read table_info to decide which columns to add;
    # no-oping this one would silently skip every migration.
    conn, _ = _adapter()
    with conn as c:
        c.execute('CREATE TABLE t (a TEXT, b INTEGER)')
        cols = {r[1] for r in c.execute('PRAGMA table_info(t)')}
        assert cols == {'a', 'b'}


def test_adapter_translates_errors_into_sqlite3_errors():
    conn, _ = _adapter()

    class _LibsqlError(RuntimeError):
        code = 'SQLITE_UNKNOWN'

    _LibsqlError.__module__ = 'libsql_client.client'

    class _Boom(object):
        def execute(self, sql, params=None):
            raise _LibsqlError('no such column: nope')

        def commit(self):
            pass

        def rollback(self):
            pass

    conn._txn = _Boom()
    # The migrations run ALTER TABLE inside `except sqlite3.OperationalError`.
    # A raw LibsqlError would sail through that guard and kill startup.
    with pytest.raises(sqlite3.OperationalError):
        conn.execute('ALTER TABLE mastery ADD COLUMN nope TEXT')


def test_adapter_commits_on_clean_exit_and_rolls_back_on_error():
    conn, client = _adapter()
    with conn as c:
        c.execute('CREATE TABLE t (a INTEGER)')
    assert client.transactions[-1].committed

    conn2 = store._LibsqlConnection('libsql://x', None, _client=client)
    with pytest.raises(ValueError):
        with conn2 as c:
            c.execute('INSERT INTO t VALUES (1)')
            raise ValueError('boom')
    assert client.transactions[-1].rolled_back


def test_adapter_backup_is_refused_clearly():
    # sqlite3's page-copy backup has no remote equivalent; the learner store
    # already logs and carries on, but the error must say why.
    conn, _ = _adapter()
    with pytest.raises(sqlite3.Error):
        conn.backup('/tmp/nope.db')


# --------------------------------------------------------------------------
# The adapter against the real libSQL client, driven at a `file:` URL
# --------------------------------------------------------------------------

libsql_client = pytest.importorskip(
    'libsql_client',
    reason='libsql-client is not installed; the remote path cannot be '
           'exercised (pip install -r requirements.txt)')


@pytest.fixture
def turso_learner(monkeypatch):
    """A LearnerStore running through the real libSQL client.

    `file:` drives the identical remote code path — same client, same
    ResultSet, same missing executescript — against a temp file, so the
    adapter is proved without credentials or a network round trip.
    """
    d = tempfile.mkdtemp()
    monkeypatch.setenv(store.URL_ENV, 'file:' + os.path.join(d, 'remote.db'))
    return LearnerStore(os.path.join(d, 'unused.db'))


def test_real_client_builds_the_whole_schema(turso_learner):
    # If executescript, the migrations or PRAGMA table_info were wrong, the
    # constructor above would already have thrown.
    with turso_learner._conn() as c:
        names = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {'profile', 'mastery', 'srs_cards', 'events'} <= names


def test_real_client_matches_local_behaviour(tmp_path, monkeypatch):
    """Same script, two backends, identical answers.

    Order matters, and not just at construction: the backend is chosen per
    connection, from the environment as it stands at that moment. So the local
    run has to finish before the environment names a remote, or it becomes a
    second handle on the same remote database and the test compares a store
    against itself.
    """

    def script(s):
        s.save_profile('Nell', 9.0, 5.0, 'wide', 1, ['math'])
        first = s.record_attempt('math.arith', 0.9)
        second = s.record_attempt('math.arith', 0.95)
        s.add_cards([{'front': '2+2', 'back': '4', 'node_id': 'math.arith',
                      'article': 'Addition'}])
        s.seed_assumed(['math.geometry'])
        revoked = s.revoke_assumed(['math.geometry'])
        profile = dict(s.get_profile())
        profile.pop('created_at')
        return (profile, first, second, revoked, s.mastery_map(),
                s.mastery_detail('math.arith'), s.deck_stats()['total'])

    local_out = script(LearnerStore(str(tmp_path / 'local.db')))
    monkeypatch.setenv(store.URL_ENV, 'file:' + str(tmp_path / 'remote.db'))
    remote_out = script(LearnerStore(str(tmp_path / 'unused.db')))
    for remote, local_value in zip(remote_out, local_out):
        if isinstance(remote, dict) and 'ready_at' in remote:
            remote, local_value = dict(remote), dict(local_value)
            remote.pop('ready_at'), local_value.pop('ready_at')
        assert remote == local_value


def test_real_client_persists_across_reopen(turso_learner, monkeypatch):
    """The bug this whole change exists to fix: a second connection — which
    on Vercel is a second function instance — still knows the reader."""
    turso_learner.save_profile('Nell', 9.0, 5.0, 'wide', 1, ['math'])
    reopened = LearnerStore(turso_learner.db_path)
    assert reopened.get_profile()['name'] == 'Nell'


def test_real_client_carries_the_sittings_store_too(turso_learner):
    sittings = SittingStore(lambda: turso_learner.db_path)
    sittings['tok'] = {'at': 1.0, 'questions': [1, 2]}
    assert sittings['tok']['questions'] == [1, 2]
    assert 'tok' in sittings


def test_real_client_rolls_back_a_failed_block(turso_learner):
    conn = turso_learner._conn()
    with pytest.raises(ValueError):
        with conn as c:
            c.execute("INSERT INTO mastery (node_id, level) VALUES ('x', 1)")
            raise ValueError('boom')
    with turso_learner._conn() as c:
        assert c.execute(
            "SELECT COUNT(*) FROM mastery WHERE node_id='x'").fetchone()[0] == 0


@pytest.mark.skipif(
    not (os.environ.get('PRIMER_TURSO_TEST_URL')
         and os.environ.get('PRIMER_TURSO_TEST_TOKEN')),
    reason='no throwaway Turso credentials in PRIMER_TURSO_TEST_URL / '
           'PRIMER_TURSO_TEST_TOKEN; the hosted path is not exercised')
def test_against_real_turso(monkeypatch):
    """Opt-in only, and never against the reader's own database: point
    PRIMER_TURSO_TEST_* at a scratch Turso database to run this."""
    monkeypatch.setenv(store.URL_ENV, os.environ['PRIMER_TURSO_TEST_URL'])
    monkeypatch.setenv(store.TOKEN_ENV, os.environ['PRIMER_TURSO_TEST_TOKEN'])
    conn = store.connect('unused.db', named_rows=True)
    with conn as c:
        assert c.execute('SELECT 1 AS n').fetchone()['n'] == 1
