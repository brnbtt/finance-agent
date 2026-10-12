import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path


class UserState(StrEnum):
    AWAITING_INVITE = "awaiting_invite"
    AWAITING_NAME = "awaiting_name"
    READY = "ready"


@dataclass(frozen=True)
class User:
    id: int
    name: str | None
    state: UserState


@dataclass(frozen=True)
class Message:
    role: str
    content: str


# Append new migrations; never edit one that has shipped.
MIGRATIONS: list[str] = [
    """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        channel TEXT NOT NULL,
        external_id TEXT NOT NULL,
        name TEXT,
        state TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (channel, external_id)
    );
    CREATE TABLE messages (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE INDEX ix_messages_user ON messages(user_id, id);
    CREATE TABLE uploads (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        filename TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        content BLOB NOT NULL,
        received_at TEXT NOT NULL,
        UNIQUE (user_id, sha256)
    );
    """,
]


def _now() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    def close(self) -> None:
        self._conn.close()

    @property
    def schema_version(self) -> int:
        return self._conn.execute("PRAGMA user_version").fetchone()[0]

    def _migrate(self) -> None:
        for version, script in enumerate(MIGRATIONS[self.schema_version :], self.schema_version):
            try:
                self._conn.executescript(
                    f"BEGIN; {script}; PRAGMA user_version = {version + 1}; COMMIT;"
                )
            except sqlite3.Error:
                self._conn.rollback()
                raise

    def get_or_create_user(self, channel: str, external_id: str) -> User:
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO users (channel, external_id, state, created_at)"
                " VALUES (?, ?, ?, ?)",
                (channel, external_id, UserState.AWAITING_INVITE, _now()),
            )
        row = self._conn.execute(
            "SELECT id, name, state FROM users WHERE channel = ? AND external_id = ?",
            (channel, external_id),
        ).fetchone()
        return User(row["id"], row["name"], UserState(row["state"]))

    def update_user(self, user_id: int, state: UserState, name: str | None = None) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE users SET state = ?, name = COALESCE(?, name) WHERE id = ?",
                (state, name, user_id),
            )

    def add_message(self, user_id: int, role: str, content: str) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (user_id, role, content, _now()),
            )

    def recent_messages(self, user_id: int, limit: int) -> list[Message]:
        rows = self._conn.execute(
            "SELECT role, content FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [Message(row["role"], row["content"]) for row in reversed(rows)]

    def add_upload(self, user_id: int, filename: str, content: bytes) -> bool:
        """Store a file once per user. Returns False if the same file was already stored."""
        with self._conn:
            cursor = self._conn.execute(
                "INSERT OR IGNORE INTO uploads (user_id, filename, sha256, content, received_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (user_id, filename, hashlib.sha256(content).hexdigest(), content, _now()),
            )
        return cursor.rowcount == 1
