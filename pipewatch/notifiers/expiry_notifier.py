"""Notifier that suppresses alerts after a pipeline-specific TTL has elapsed."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class ExpiryStore:
    db_path: str
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expiry_log (
                pipeline TEXT NOT NULL,
                first_sent_at REAL NOT NULL,
                PRIMARY KEY (pipeline)
            )
            """
        )
        self._conn.commit()

    def record_first_sent(self, pipeline: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO expiry_log (pipeline, first_sent_at) VALUES (?, ?)",
            (pipeline, time.time()),
        )
        self._conn.commit()

    def first_sent_at(self, pipeline: str) -> float | None:
        row = self._conn.execute(
            "SELECT first_sent_at FROM expiry_log WHERE pipeline = ?",
            (pipeline,),
        ).fetchone()
        return row[0] if row else None

    def clear(self, pipeline: str) -> None:
        self._conn.execute("DELETE FROM expiry_log WHERE pipeline = ?", (pipeline,))
        self._conn.commit()


@dataclass
class ExpiryNotifier:
    """Forward alerts only within a TTL window since the first alert for a pipeline."""

    inner: Notifier
    store: ExpiryStore
    ttl_seconds: float

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

    def send(self, result) -> None:
        pipeline = getattr(result, "pipeline_name", None) or "unknown"
        first = self.store.first_sent_at(pipeline)
        now = time.time()

        if first is None:
            self.store.record_first_sent(pipeline)
            self.inner.send(result)
            return

        if now - first <= self.ttl_seconds:
            self.inner.send(result)
        # else: TTL expired — suppress silently
