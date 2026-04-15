"""Debounce notifier: suppresses rapid repeated alerts for the same pipeline.

Only forwards a notification if the pipeline has not been alerted within
the configured debounce window (in seconds).
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Protocol


class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class DebounceStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS debounce (
                pipeline TEXT PRIMARY KEY,
                last_sent_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, pipeline: str) -> None:
        self._conn.execute(
            """
            INSERT INTO debounce (pipeline, last_sent_at)
            VALUES (?, ?)
            ON CONFLICT(pipeline) DO UPDATE SET last_sent_at = excluded.last_sent_at
            """,
            (pipeline, time.time()),
        )
        self._conn.commit()

    def last_sent_at(self, pipeline: str) -> float | None:
        row = self._conn.execute(
            "SELECT last_sent_at FROM debounce WHERE pipeline = ?",
            (pipeline,),
        ).fetchone()
        return row[0] if row else None

    def is_debounced(self, pipeline: str, window_seconds: float) -> bool:
        last = self.last_sent_at(pipeline)
        if last is None:
            return False
        return (time.time() - last) < window_seconds


@dataclass
class DebounceNotifier:
    inner: Notifier
    store: DebounceStore
    window_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

    def send(self, result) -> None:
        pipeline = result.pipeline_name
        if self.store.is_debounced(pipeline, self.window_seconds):
            return
        self.inner.send(result)
        self.store.record(pipeline)
