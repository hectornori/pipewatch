"""Dead-letter notifier: captures failed notifications for later inspection."""
from __future__ import annotations

import sqlite3
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

log = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class DeadLetterEntry:
    id: int
    pipeline: str
    error: str
    payload: str
    recorded_at: datetime


@dataclass
class DeadLetterStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dead_letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline TEXT NOT NULL,
                error TEXT NOT NULL,
                payload TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, pipeline: str, error: str, payload: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO dead_letters (pipeline, error, payload, recorded_at) VALUES (?, ?, ?, ?)",
            (pipeline, error, payload, now),
        )
        self._conn.commit()

    def get_all(self) -> list[DeadLetterEntry]:
        rows = self._conn.execute(
            "SELECT id, pipeline, error, payload, recorded_at FROM dead_letters ORDER BY recorded_at DESC"
        ).fetchall()
        return [
            DeadLetterEntry(
                id=r[0],
                pipeline=r[1],
                error=r[2],
                payload=r[3],
                recorded_at=datetime.fromisoformat(r[4]),
            )
            for r in rows
        ]

    def clear(self) -> None:
        self._conn.execute("DELETE FROM dead_letters")
        self._conn.commit()


class DeadLetterNotifier:
    """Wraps an inner notifier; on failure, writes to a dead-letter store."""

    def __init__(self, inner: Notifier, store: DeadLetterStore) -> None:
        self._inner = inner
        self._store = store

    def send(self, result) -> None:
        try:
            self._inner.send(result)
        except Exception as exc:
            pipeline = getattr(result, "pipeline_name", "unknown")
            error_msg = str(exc)
            payload = repr(result)
            log.warning("Notification failed for '%s'; writing to dead-letter store: %s", pipeline, error_msg)
            self._store.record(pipeline=pipeline, error=error_msg, payload=payload)
