"""Quota-enforcing notifier: caps the total number of notifications sent within a rolling time window."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Optional

from pipewatch.notifiers import Notifier, send as _send_protocol


@dataclass
class QuotaStore:
    db_path: str

    def __post_init__(self) -> None:
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS quota_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pipeline TEXT NOT NULL,
                    sent_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    def record(self, pipeline: str, ts: Optional[float] = None) -> None:
        ts = ts if ts is not None else time.time()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO quota_events (pipeline, sent_at) VALUES (?, ?)",
                (pipeline, ts),
            )
            conn.commit()

    def count_since(self, pipeline: str, since: float) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM quota_events WHERE pipeline = ? AND sent_at >= ?",
                (pipeline, since),
            ).fetchone()
        return row[0] if row else 0

    def is_over_quota(self, pipeline: str, max_count: int, window_seconds: int) -> bool:
        since = time.time() - window_seconds
        return self.count_since(pipeline, since) >= max_count


@dataclass
class QuotaNotifier:
    """Forwards to *inner* unless the per-pipeline quota is exhausted."""

    inner: Notifier
    store: QuotaStore
    max_count: int = 10
    window_seconds: int = 3600

    def send(self, result: _send_protocol) -> None:  # type: ignore[valid-type]
        pipeline = getattr(result, "pipeline_name", "unknown")
        if self.store.is_over_quota(pipeline, self.max_count, self.window_seconds):
            return
        self.inner.send(result)
        self.store.record(pipeline)
