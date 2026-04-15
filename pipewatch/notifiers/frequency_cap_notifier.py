"""FrequencyCapNotifier – limits how many alerts are sent per pipeline within a rolling window."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Protocol


class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class FrequencyCapStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS frequency_cap (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline  TEXT    NOT NULL,
                sent_at   REAL    NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, pipeline: str) -> None:
        self._conn.execute(
            "INSERT INTO frequency_cap (pipeline, sent_at) VALUES (?, ?)",
            (pipeline, time.time()),
        )
        self._conn.commit()

    def count_in_window(self, pipeline: str, window_seconds: float) -> int:
        cutoff = time.time() - window_seconds
        row = self._conn.execute(
            "SELECT COUNT(*) FROM frequency_cap WHERE pipeline = ? AND sent_at >= ?",
            (pipeline, cutoff),
        ).fetchone()
        return int(row[0]) if row else 0


@dataclass
class FrequencyCapNotifier:
    """Forwards alerts only until *max_count* notifications have been sent within *window_seconds*."""

    inner: Notifier
    store: FrequencyCapStore
    max_count: int = 5
    window_seconds: float = 3600.0

    def __post_init__(self) -> None:
        if self.max_count < 1:
            raise ValueError("max_count must be >= 1")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

    def send(self, result) -> None:
        pipeline = getattr(result, "pipeline_name", "unknown")
        current = self.store.count_in_window(pipeline, self.window_seconds)
        if current >= self.max_count:
            return
        self.inner.send(result)
        self.store.record(pipeline)
