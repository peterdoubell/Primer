"""Durable, single-use OAuth return destinations behind opaque random nonces.

Only the nonce belongs in the OAuth state parameter or browser cookie. The
return destination stays in this separate table, independent of any reader.
"""

from contextlib import closing
import re
import secrets
import time


TTL_SECONDS = 600
MAX_PENDING = 512
MAX_RETURN_PATH = 512
_NONCE = re.compile(r"[A-Za-z0-9_-]{43}\Z")


class OAuthStateStore:
    def __init__(self, connection_factory):
        self._connection_factory = connection_factory

    @staticmethod
    def _prepare(connection):
        connection.execute("""
            CREATE TABLE IF NOT EXISTS oauth_states (
                id INTEGER PRIMARY KEY,
                nonce TEXT NOT NULL UNIQUE,
                return_path TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS oauth_states_expiry
            ON oauth_states (expires_at)
        """)
        # HTTP libSQL autocommits statements. An insertion and its eviction
        # therefore share one atomic SQL write, even across worker processes.
        # New rows have the greatest id, so the nonce just issued is retained.
        connection.execute(f"""
            CREATE TRIGGER IF NOT EXISTS oauth_states_limit
            AFTER INSERT ON oauth_states
            BEGIN
                DELETE FROM oauth_states WHERE id NOT IN (
                    SELECT id FROM oauth_states ORDER BY id DESC LIMIT {MAX_PENDING}
                );
            END
        """)

    def issue(self, return_path: str) -> str:
        """Remember a local destination for ten minutes and return an opaque key."""
        if (not isinstance(return_path, str) or not return_path
                or len(return_path) > MAX_RETURN_PATH
                or not return_path.startswith("/") or return_path.startswith("//")
                or "\\" in return_path
                or any(ord(character) < 32 or ord(character) == 127
                       for character in return_path)):
            raise ValueError("OAuth return destination must be a short local path")
        nonce = secrets.token_urlsafe(32)
        now = time.time()
        with closing(self._connection_factory()) as connection, connection:
            self._prepare(connection)
            connection.execute("DELETE FROM oauth_states WHERE expires_at <= ?", (now,))
            connection.execute(
                "INSERT INTO oauth_states (nonce, return_path, expires_at) VALUES (?, ?, ?)",
                (nonce, return_path, now + TTL_SECONDS),
            )
        return nonce

    def consume(self, nonce: str):
        """Return an unexpired destination once; missing or invalid keys yield None."""
        if not isinstance(nonce, str) or _NONCE.fullmatch(nonce) is None:
            return None
        now = time.time()
        with closing(self._connection_factory()) as connection, connection:
            self._prepare(connection)
            connection.execute("DELETE FROM oauth_states WHERE expires_at <= ?", (now,))
            # One SQL statement owns both the result and the deletion. A
            # SELECT followed by DELETE could replay across HTTP workers.
            rows = connection.execute(
                "DELETE FROM oauth_states WHERE nonce = ? AND expires_at > ? RETURNING return_path",
                (nonce, now),
            ).fetchall()
        return rows[0][0] if rows else None
