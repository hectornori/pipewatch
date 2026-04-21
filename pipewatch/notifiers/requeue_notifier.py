"""Notifier that re-queues failed notifications for later retry via a persistent store."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Protocol


class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class RequeueStore:
    db_path: str = "pipewatch_requeue.db"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requeue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline TEXT NOT NULL,
                error TEXT,
                queued_at REAL NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.commit()

    def enqueue(self, pipeline: str, error: str | None) -> None:
        self._conn.execute(
            "INSERT INTO requeue (pipeline, error, queued_at) VALUES (?, ?, ?)",
            (pipeline, error, time.time()),
        )
        self._conn.commit()

    def pop_due(self, limit: int = 10) -> list[tuple[int, str, str | None]]:
        rows = self._conn.execute(
            "SELECT id, pipeline, error FROM requeue ORDER BY queued_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return rows

    def remove(self, entry_id: int) -> None:
        self._conn.execute("DELETE FROM requeue WHERE id = ?", (entry_id,))
        self._conn.commit()

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM requeue").fetchone()[0]


@dataclass
class RequeueNotifier:
    """Wraps an inner notifier; on failure, enqueues the alert for later retry."""
    inner: Notifier
    store: RequeueStore

    def send(self, result) -> None:
        try:
            self.inner.send(result)
        except Exception:
            pipeline = getattr(result, "pipeline_name", "unknown")
            error = getattr(result, "error_message", None)
            self.store.enqueue(pipeline, error)

    def flush(self, factory) -> int:
        """Retry queued entries using *factory(pipeline, error) -> result*.
        Returns the number of successfully replayed entries."""
        due = self.store.pop_due()
        success = 0
        for entry_id, pipeline, error in due:
            try:
                result = factory(pipeline, error)
                self.inner.send(result)
                self.store.remove(entry_id)
                success += 1
            except Exception:
                pass
        return success
