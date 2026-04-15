"""Notifier that archives every result to a SQLite store before forwarding."""
from __future__ import annotations

import sqlite3
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class ArchiveStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS archive (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline  TEXT    NOT NULL,
                success   INTEGER NOT NULL,
                error     TEXT,
                payload   TEXT,
                archived_at TEXT  NOT NULL
            )
            """
        )
        self._conn.commit()

    def save(self, result) -> None:
        payload = json.dumps(getattr(result, "metadata", None), default=str)
        self._conn.execute(
            "INSERT INTO archive (pipeline, success, error, payload, archived_at) VALUES (?,?,?,?,?)",
            (
                result.pipeline_name,
                int(result.success),
                result.error_message if not result.success else None,
                payload,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def get_recent(self, pipeline: str, limit: int = 50) -> list[dict]:
        cur = self._conn.execute(
            "SELECT pipeline, success, error, payload, archived_at FROM archive "
            "WHERE pipeline=? ORDER BY id DESC LIMIT ?",
            (pipeline, limit),
        )
        cols = ["pipeline", "success", "error", "payload", "archived_at"]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


@dataclass
class ArchiveNotifier:
    inner: Notifier
    store: ArchiveStore

    def send(self, result) -> None:
        self.store.save(result)
        self.inner.send(result)
