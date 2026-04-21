"""CapNotifier: suppress notifications once a per-pipeline cap is reached within a rolling window."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class CapStore:
    db_path: str
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cap_events (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline  TEXT    NOT NULL,
                sent_at   REAL    NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, pipeline: str) -> None:
        self._conn.execute(
            "INSERT INTO cap_events (pipeline, sent_at) VALUES (?, ?)",
            (pipeline, time.time()),
        )
        self._conn.commit()

    def count_since(self, pipeline: str, since: float) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM cap_events WHERE pipeline = ? AND sent_at >= ?",
            (pipeline, since),
        ).fetchone()
        return int(row[0]) if row else 0


@dataclass
class CapNotifier:
    """Forward to *inner* only while the send count for the pipeline is below *max_count*
    within the last *window_seconds* seconds."""

    inner: Notifier
    store: CapStore
    max_count: int
    window_seconds: float

    def __post_init__(self) -> None:
        if self.max_count < 1:
            raise ValueError("max_count must be >= 1")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

    def send(self, result) -> None:
        pipeline = getattr(result, "pipeline_name", "unknown")
        since = time.time() - self.window_seconds
        if self.store.count_since(pipeline, since) >= self.max_count:
            return
        self.inner.send(result)
        self.store.record(pipeline)
