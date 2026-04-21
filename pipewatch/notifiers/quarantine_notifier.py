"""Quarantine notifier: silences a pipeline after N consecutive failures.

Once quarantined, alerts are suppressed until the pipeline recovers
(i.e. a success result is observed), preventing alert storms.
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class QuarantineStore:
    db_path: str
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quarantine (
                pipeline TEXT PRIMARY KEY,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                quarantined_at REAL
            )
            """
        )
        self._conn.commit()

    def record_failure(self, pipeline: str) -> int:
        """Increment failure count and return the new total."""
        self._conn.execute(
            """
            INSERT INTO quarantine (pipeline, consecutive_failures)
            VALUES (?, 1)
            ON CONFLICT(pipeline) DO UPDATE SET
                consecutive_failures = consecutive_failures + 1
            """,
            (pipeline,),
        )
        self._conn.commit()
        row = self._conn.execute(
            "SELECT consecutive_failures FROM quarantine WHERE pipeline = ?",
            (pipeline,),
        ).fetchone()
        return row[0] if row else 1

    def quarantine(self, pipeline: str) -> None:
        self._conn.execute(
            "UPDATE quarantine SET quarantined_at = ? WHERE pipeline = ?",
            (time.time(), pipeline),
        )
        self._conn.commit()

    def clear(self, pipeline: str) -> None:
        self._conn.execute(
            "UPDATE quarantine SET consecutive_failures = 0, quarantined_at = NULL WHERE pipeline = ?",
            (pipeline,),
        )
        self._conn.commit()

    def is_quarantined(self, pipeline: str) -> bool:
        row = self._conn.execute(
            "SELECT quarantined_at FROM quarantine WHERE pipeline = ?",
            (pipeline,),
        ).fetchone()
        return bool(row and row[0] is not None)


@dataclass
class QuarantineNotifier:
    """Wraps an inner notifier and suppresses alerts for quarantined pipelines."""

    inner: Notifier
    store: QuarantineStore
    threshold: int = 3

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("threshold must be >= 1")

    def send(self, result) -> None:
        name = getattr(result, "pipeline", None) or "unknown"
        success = getattr(result, "success", True)

        if success:
            self.store.clear(name)
            self.inner.send(result)
            return

        if self.store.is_quarantined(name):
            return

        count = self.store.record_failure(name)
        if count >= self.threshold:
            self.store.quarantine(name)

        self.inner.send(result)
