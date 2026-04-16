"""Heartbeat notifier — suppresses alerts while a pipeline is actively beating."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class HeartbeatStore:
    db_path: str = "pipewatch_heartbeat.db"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS heartbeats "
            "(pipeline TEXT PRIMARY KEY, last_beat REAL NOT NULL)"
        )
        self._conn.commit()

    def beat(self, pipeline: str) -> None:
        self._conn.execute(
            "INSERT INTO heartbeats (pipeline, last_beat) VALUES (?, ?) "
            "ON CONFLICT(pipeline) DO UPDATE SET last_beat=excluded.last_beat",
            (pipeline, time.time()),
        )
        self._conn.commit()

    def last_beat_at(self, pipeline: str) -> float | None:
        row = self._conn.execute(
            "SELECT last_beat FROM heartbeats WHERE pipeline=?", (pipeline,)
        ).fetchone()
        return row[0] if row else None

    def is_alive(self, pipeline: str, ttl_seconds: float) -> bool:
        ts = self.last_beat_at(pipeline)
        if ts is None:
            return False
        return (time.time() - ts) <= ttl_seconds


@dataclass
class HeartbeatNotifier:
    """Forwards alerts only when the pipeline heartbeat has gone stale."""
    inner: Notifier
    store: HeartbeatStore
    ttl_seconds: float = 300.0

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

    def send(self, result) -> None:
        pipeline = getattr(result, "pipeline_name", "")
        if self.store.is_alive(pipeline, self.ttl_seconds):
            return
        self.inner.send(result)
