"""Where the reader's record actually lives.

The Primer keeps everything in SQLite files, which is exactly right on a
laptop: one file, no server, and a multi-year learning record you can copy to a
USB stick. It is exactly wrong on Vercel. There the function filesystem is
read-only apart from /tmp, and /tmp belongs to one warm instance for a few
minutes. The demo deployment therefore *forgot the reader between requests* —
you answered a placement quiz, the next request landed on a different instance,
and the book greeted you as a stranger. That is not a rough edge; a book that
cannot remember you is not the Primer.

Turso (libSQL) is the fix. It is SQLite over the wire: the same dialect, the
same `?` placeholders, the same `ON CONFLICT` and `AUTOINCREMENT` this codebase
already leans on across a hundred-odd raw statements. Nothing above this module
has to learn a second SQL dialect, which is why it was picked over Postgres.

This module is the one seam. Three stores (learner, wiki, sittings) used to
call `sqlite3.connect` directly; they now call `connect()` here. The contract
is deliberately lopsided:

  * With no environment variables set, `connect()` returns a *real*
    `sqlite3.Connection`, configured exactly as the three call sites used to
    configure it themselves. No wrapper, no adapter, no behaviour change. The
    local book, the user's real database, and 415 tests are the thing that
    must not move.
  * With `TURSO_DATABASE_URL` set, it returns an adapter that presents the
    slice of the `sqlite3` interface this codebase uses, on top of a libSQL
    client. Every gap between the two is papered over *here*, once, rather
    than smeared through learner.py/wiki.py/sittings.py as `if turso:` tests.
"""

import os
import sqlite3

# The env vars the Vercel Marketplace integration (`tursocloud/database`)
# injects. Absent locally, and absent on Vercel until the integration is
# actually attached — hence every use is guarded, never assumed.
URL_ENV = "TURSO_DATABASE_URL"
TOKEN_ENV = "TURSO_AUTH_TOKEN"


def turso_url():
    """The configured remote URL, or None for "stay local".

    Read at call time, not at import time: tests flip the environment between
    cases, and the server can be re-pointed at a different store while running.
    An empty string counts as unset — an integration that provisions the var
    but leaves it blank should not silently break the local fallback.
    """
    url = (os.environ.get(URL_ENV) or "").strip() or None
    if url is None:
        return None
    # Turso hands out `libsql://…`, which this client resolves to a WebSocket
    # (`wss://`). That handshake is refused by the Vercel-provisioned endpoint
    # — verified against the live database: 400 "Invalid response status".
    # The same host answers Hrana-over-HTTP happily, and HTTP is the better
    # fit for serverless anyway: no long-lived socket to keep alive across
    # invocations that may be frozen between requests.
    if url.startswith("libsql://"):
        url = "https://" + url[len("libsql://"):]
    return url


def using_turso():
    return turso_url() is not None


def connect(db_path, named_rows=False, wal=True, busy_timeout=8000, timeout=15):
    """Open the store behind `db_path`.

    `db_path` names a local file. In Turso mode there is exactly one remote
    database and the path is ignored — the learner, sittings and wiki tables
    are disjoint (profile/mastery/srs_cards/events/placement/burned/
    reading_log, sittings, article_cache/image_cache), so they coexist in one
    database without collision.

    `named_rows` asks for `sqlite3.Row`-style rows (index *and* column-name
    access) — the learner store's rows are read by name all over.
    """
    url = turso_url()
    if url is None:
        # The local path, unchanged and unwrapped. Everything below the
        # `return` is what the three factories each used to do inline.
        conn = sqlite3.connect(db_path, timeout=timeout)
        if wal:
            conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=%d" % busy_timeout)
        if named_rows:
            conn.row_factory = sqlite3.Row
        return conn
    return _LibsqlConnection(url, os.environ.get(TOKEN_ENV) or None,
                             named_rows=named_rows)


# --------------------------------------------------------------------------
# The adapter. Everything below runs only when TURSO_DATABASE_URL is set.
# --------------------------------------------------------------------------

class _Row(tuple):
    """A stand-in for `sqlite3.Row`.

    libSQL's own row object indexes by position and by name but has no
    `.keys()`, and `dict(row)` on it raises. The learner store relies on both:
    `dict(row)` to build a profile, and `"col" in row.keys()` as its guard for
    columns added by a migration. So this is a tuple — positional access and
    equality for free — that also answers to column names and to `.keys()`,
    which together is all `dict()` needs to consume it.

    A missing name raises IndexError, matching sqlite3.Row rather than the
    KeyError a dict would raise, because that is what a caller catching one or
    the other will have been written against.
    """

    def __new__(cls, columns, values):
        row = super().__new__(cls, values)
        row._columns = columns
        return row

    def keys(self):
        return list(self._columns)

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                idx = list(self._columns).index(key)
            except ValueError:
                raise IndexError("No item with that key")
            return tuple.__getitem__(self, idx)
        return tuple.__getitem__(self, key)


class _Cursor(object):
    """What `conn.execute(...)` hands back.

    libSQL returns a whole `ResultSet` — every row, already materialised —
    where sqlite3 returns a lazy cursor. Callers here only ever `.fetchone()`,
    `.fetchall()` or iterate, so a cursor over an in-memory list is a faithful
    stand-in; the queries in this book are all small enough that eager reads
    cost nothing. `.fetchone()` returning None past the end matters: several
    call sites test `if row is None`.
    """

    def __init__(self, rows, description=None, rowcount=-1, lastrowid=None):
        self._rows = rows
        self._i = 0
        self.description = description
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def __iter__(self):
        return self

    def __next__(self):
        if self._i >= len(self._rows):
            raise StopIteration
        row = self._rows[self._i]
        self._i += 1
        return row

    next = __next__

    def fetchone(self):
        if self._i >= len(self._rows):
            return None
        row = self._rows[self._i]
        self._i += 1
        return row

    def fetchall(self):
        rest = self._rows[self._i:]
        self._i = len(self._rows)
        return list(rest)

    def fetchmany(self, size=1):
        rest = self._rows[self._i:self._i + size]
        self._i += len(rest)
        return list(rest)

    def close(self):
        pass


def _translate(exc):
    """Re-raise libSQL errors as the `sqlite3` errors the callers catch.

    This is not cosmetic. The learner's migrations run `ALTER TABLE ... ADD
    COLUMN` inside `except sqlite3.OperationalError: pass` — that is how a
    database opened by an older build catches up. A `LibsqlError` sails
    straight through that guard and takes the whole store down on startup.
    """
    code = (getattr(exc, "code", "") or "").upper()
    text = str(exc).upper()
    if "CONSTRAINT" in code or "CONSTRAINT" in text:
        return sqlite3.IntegrityError(str(exc))
    return sqlite3.OperationalError(str(exc))


class _LibsqlConnection(object):
    """The `sqlite3.Connection` surface this codebase actually uses.

    Deliberately small: execute / executemany / executescript / commit /
    rollback / close / total_changes / context manager. Anything not listed is
    something no caller asks for, and inventing it would be inventing
    behaviour we cannot test.
    """

    def __init__(self, url, auth_token=None, named_rows=False, _client=None):
        self._named_rows = named_rows
        self.total_changes = 0
        self.row_factory = None         # accepted and ignored; see connect()
        if _client is not None:
            self._client = _client
        else:
            # Imported lazily so that a local install with no Turso in sight
            # never pays for (or requires) the dependency.
            import libsql_client
            kwargs = {}
            if auth_token:
                kwargs["auth_token"] = auth_token
            self._client = libsql_client.create_client_sync(url, **kwargs)
        # Statements are buffered into an explicit transaction, opened lazily
        # on first use and closed by __exit__/commit — see __exit__ for why.
        # Except over HTTP, which has no transactions at all: see _target().
        # Decided from the URL rather than by catching the failure, so the
        # first write of a request does not pay a round trip to find out.
        self._autocommit = str(url or "").lower().startswith(("http://", "https://"))
        self._txn = None
        self._closed = False

    # ---------- statement execution ----------

    def _target(self):
        """The transaction everything runs through — where one is available.

        libSQL's client autocommits each statement unless you hold a
        transaction object. sqlite3, by contrast, opens one implicitly and
        commits it at the end of `with conn:` — precisely the shape every call
        site here uses, several of them to make a read-modify-write atomic.

        Over HTTP there is no transaction to hold. The client says so plainly
        (TRANSACTIONS_NOT_SUPPORTED) and directs you to a WebSocket URL, but
        the WebSocket handshake against the Vercel-provisioned Turso endpoint
        is refused outright — 400, verified against the live database — because
        this pure-Python client speaks a Hrana version the current servers no
        longer accept over WS. The Rust-backed clients that do speak it ship no
        wheel for this interpreter and cannot be built here, so they cannot be
        verified before shipping.

        So on HTTP each statement autocommits, and the honest statement of what
        that costs is: a read-modify-write is no longer atomic *across
        instances*. Within one process the module-level lock in learner.py
        still serialises writers. The Primer is a single-reader book — one
        profile, `CHECK (id = 1)` — so the exposure is one reader driving two
        tabs through a quiz at the same moment, where an interleaving could
        drop one update. Losing that guarantee is worth stating; it is not
        worth blocking persistence for, since the alternative on offer is a
        store that forgets the reader entirely between requests.
        """
        if self._autocommit:
            return self._client
        if self._txn is None:
            self._txn = self._client.transaction()
        return self._txn

    def _run(self, sql, params=None):
        try:
            return self._target().execute(sql, list(params) if params else None)
        except Exception as exc:                      # noqa: BLE001
            if exc.__class__.__module__.startswith("libsql_client"):
                raise _translate(exc)
            raise

    def execute(self, sql, params=None):
        stripped = sql.lstrip().upper()
        if stripped.startswith("PRAGMA"):
            return self._pragma(sql, stripped)
        result = self._run(sql, params)
        affected = getattr(result, "rows_affected", 0) or 0
        if affected > 0:
            self.total_changes += affected
        return self._cursor(result)

    def executemany(self, sql, seq_of_params):
        # No batching primitive that preserves per-statement error semantics,
        # and these batches are tens of rows at most (stale event pruning,
        # dropping assumed mastery), so a loop inside the open transaction is
        # both correct and fast enough.
        last = None
        for params in seq_of_params:
            last = self.execute(sql, params)
        return last if last is not None else _Cursor([])

    def executescript(self, script):
        """Run a multi-statement DDL script.

        libSQL has no `executescript`, and splitting SQL on ';' is the classic
        way to corrupt a script that contains a semicolon inside a literal or
        a trigger body. Rather than write a half-parser, hand the job to the
        stdlib's own tokenizer: `sqlite3.complete_statement` tells us exactly
        where SQLite would consider a statement to end. stdlib sqlite3 is
        always importable, even when the data lives a continent away.
        """
        buf = ""
        for line in script.splitlines(True):
            buf += line
            if sqlite3.complete_statement(buf):
                if buf.strip():
                    self.execute(buf)
                buf = ""
        if buf.strip():
            self.execute(buf)
        return _Cursor([])

    def _cursor(self, result):
        columns = tuple(getattr(result, "columns", ()) or ())
        raw = list(getattr(result, "rows", ()) or ())
        if self._named_rows:
            rows = [_Row(columns, tuple(r)) for r in raw]
        else:
            rows = [tuple(r) for r in raw]
        description = tuple((c, None, None, None, None, None, None)
                            for c in columns) or None
        return _Cursor(rows, description,
                       getattr(result, "rows_affected", -1),
                       getattr(result, "last_insert_rowid", None))

    # ---------- PRAGMAs ----------

    def _pragma(self, sql, stripped):
        """Most PRAGMAs are meaningless against a remote database.

        `journal_mode=WAL` and `busy_timeout` are statements about a local
        file and a local lock: WAL is how one process avoids blocking another
        on the same inode, and busy_timeout is how long to spin on that lock.
        Turso serves a managed database over HTTP — there is no inode and no
        lock to wait on, the server handles concurrency itself. So these are
        answered locally instead of shipped, both because they are noise and
        because a libSQL server may reject them outright.

        Informational PRAGMAs like `table_info` are a different animal: the
        migration code reads them to decide which columns to add, so they must
        genuinely execute.
        """
        head = stripped[6:].strip()
        if head.startswith("JOURNAL_MODE"):
            # Report the truth for a server-side database rather than a lie
            # about WAL: nothing in the codebase reads this value.
            return _Cursor([("memory",)])
        if head.startswith("BUSY_TIMEOUT"):
            return _Cursor([(0,)])
        return self._cursor(self._run(sql))

    # ---------- transaction / lifecycle ----------

    def commit(self):
        if self._txn is not None:
            txn, self._txn = self._txn, None
            txn.commit()

    def rollback(self):
        if self._autocommit:
            # Nothing to undo: each statement was already durable when it ran.
            # Silent rather than raising, because __exit__ and close() both
            # call this on the normal path and a store that cannot roll back
            # is still a store that must close cleanly.
            return
        if self._txn is not None:
            txn, self._txn = self._txn, None
            txn.rollback()

    def close(self):
        if self._closed:
            return
        # Uncommitted work is dropped, exactly as sqlite3 does on close.
        try:
            self.rollback()
        finally:
            self._closed = True
            self._client.close()

    def backup(self, target, **kwargs):
        # sqlite3's online backup copies pages between two local files. There
        # is no such thing over the wire; Turso takes its own point-in-time
        # backups. The learner's backup() already logs and carries on when
        # this fails, so a clear error is the honest answer.
        raise sqlite3.NotSupportedError(
            "online backup is not available against a remote libSQL database; "
            "Turso keeps its own point-in-time backups")

    def __enter__(self):
        # sqlite3 yields the *connection*, not a cursor — call sites do
        # `with self._conn() as c: c.execute(...)`.
        return self

    def __exit__(self, exc_type, exc, tb):
        # sqlite3's connection context manager commits on clean exit and rolls
        # back on an exception — and, notably, does NOT close the connection.
        # We do close, because unlike a file handle a libSQL client owns a
        # worker thread and an HTTP session; leaving one per call site to be
        # reaped by the garbage collector would leak sockets on a serverless
        # instance. Nothing in the codebase reuses a connection after its
        # `with` block, so closing is invisible from above.
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()
        return False
