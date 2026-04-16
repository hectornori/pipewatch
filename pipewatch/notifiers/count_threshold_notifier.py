"""Notifier that only forwards alerts after a minimum event count threshold is reached."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class CountThresholdStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS count_threshold_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, pipeline: str) -> None:
        self._conn.execute(
            "INSERT INTO count_threshold_events (pipeline, recorded_at) VALUES (?, ?)",
            (pipeline, datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()

    def count(self, pipeline: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM count_threshold_events WHERE pipeline = ?",
            (pipeline,),
        ).fetchone()
        return row[0] if row else 0

    def reset(self, pipeline: str) -> None:
        self._conn.execute(
            "DELETE FROM count_threshold_events WHERE pipeline = ?", (pipeline,)
        )
        self._conn.commit()


@dataclass
class CountThresholdNotifier:
    inner: Notifier
    threshold: int
    store: CountThresholdStore = field(default_factory=CountThresholdStore)
    reset_after_send: bool = True

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("threshold must be >= 1")

    def send(self, result) -> None:
        pipeline = getattr(result, "pipeline_name", "unknown")
        self.store.record(pipeline)
        if self.store.count(pipeline) >= self.threshold:
            self.inner.send(result)
            if self.reset_after_send:
                self.store.reset(pipeline)
