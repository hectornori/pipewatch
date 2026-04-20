"""Notifier that appends every alert to a persistent event log with sequence numbers."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class Notifier(Protocol):
    def send(self, result: Any) -> None: ...


@dataclass
class EventLogEntry:
    seq: int
    pipeline: str
    success: bool
    error_message: str | None
    timestamp: float


@dataclass
class EventLogStore:
    db_path: str = "pipewatch_events.db"

    def __post_init__(self) -> None:
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_log (
                    seq       INTEGER PRIMARY KEY AUTOINCREMENT,
                    pipeline  TEXT    NOT NULL,
                    success   INTEGER NOT NULL,
                    error_msg TEXT,
                    ts        REAL    NOT NULL
                )
                """
            )

    def append(self, pipeline: str, success: bool, error_message: str | None) -> int:
        ts = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO event_log (pipeline, success, error_msg, ts) VALUES (?, ?, ?, ?)",
                (pipeline, int(success), error_message, ts),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def get_recent(self, pipeline: str, limit: int = 50) -> list[EventLogEntry]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT seq, pipeline, success, error_msg, ts FROM event_log "
                "WHERE pipeline = ? ORDER BY seq DESC LIMIT ?",
                (pipeline, limit),
            ).fetchall()
        return [
            EventLogEntry(seq=r[0], pipeline=r[1], success=bool(r[2]), error_message=r[3], timestamp=r[4])
            for r in rows
        ]

    def count(self, pipeline: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM event_log WHERE pipeline = ?", (pipeline,)
            ).fetchone()
        return row[0] if row else 0


@dataclass
class EventLogNotifier:
    inner: Notifier
    store: EventLogStore = field(default_factory=EventLogStore)

    def send(self, result: Any) -> None:
        pipeline = getattr(result, "pipeline_name", "unknown")
        success = getattr(result, "success", False)
        error_message = getattr(result, "error_message", None)
        self.store.append(pipeline, success, error_message)
        self.inner.send(result)
