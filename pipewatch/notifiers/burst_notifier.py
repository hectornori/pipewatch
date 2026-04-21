"""BurstNotifier – suppresses notifications when the alert rate exceeds a
short-term burst threshold, protecting downstream channels from floods."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Protocol


class Notifier(Protocol):
    def send(self, result: object) -> None: ...


@dataclass
class BurstStore:
    db_path: str
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS burst_events (
                pipeline TEXT NOT NULL,
                sent_at  REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, pipeline: str) -> None:
        self._conn.execute(
            "INSERT INTO burst_events (pipeline, sent_at) VALUES (?, ?)",
            (pipeline, time.time()),
        )
        self._conn.commit()

    def count_since(self, pipeline: str, since: float) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM burst_events WHERE pipeline = ? AND sent_at >= ?",
            (pipeline, since),
        ).fetchone()
        return int(row[0]) if row else 0


@dataclass
class BurstNotifier:
    """Forward alerts to *inner* only when the burst limit has not been reached.

    Args:
        inner:          Wrapped notifier.
        store:          Persistent event store.
        max_count:      Maximum alerts allowed within *window_seconds*.
        window_seconds: Rolling window length in seconds.
    """

    inner: Notifier
    store: BurstStore
    max_count: int
    window_seconds: float

    def __post_init__(self) -> None:
        if self.max_count < 1:
            raise ValueError("max_count must be >= 1")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

    def send(self, result: object) -> None:
        pipeline: str = getattr(result, "pipeline_name", "unknown")
        since = time.time() - self.window_seconds
        count = self.store.count_since(pipeline, since)
        if count >= self.max_count:
            return
        self.store.record(pipeline)
        self.inner.send(result)
