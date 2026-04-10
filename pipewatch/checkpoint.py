"""Checkpoint store: persist and retrieve the last successful run timestamp per pipeline."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class CheckpointStore:
    db_path: str = "pipewatch_checkpoints.db"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                pipeline_name TEXT PRIMARY KEY,
                last_success_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def record_success(self, pipeline_name: str, ts: Optional[datetime] = None) -> None:
        """Persist the timestamp of the last successful run for *pipeline_name*."""
        if ts is None:
            ts = datetime.now(timezone.utc)
        self._conn.execute(
            """
            INSERT INTO checkpoints (pipeline_name, last_success_at)
            VALUES (?, ?)
            ON CONFLICT(pipeline_name) DO UPDATE SET last_success_at = excluded.last_success_at
            """,
            (pipeline_name, ts.isoformat()),
        )
        self._conn.commit()

    def last_success_at(self, pipeline_name: str) -> Optional[datetime]:
        """Return the last success timestamp for *pipeline_name*, or None."""
        row = self._conn.execute(
            "SELECT last_success_at FROM checkpoints WHERE pipeline_name = ?",
            (pipeline_name,),
        ).fetchone()
        if row is None:
            return None
        return datetime.fromisoformat(row[0])

    def minutes_since_success(self, pipeline_name: str) -> Optional[float]:
        """Return minutes elapsed since last success, or None if never recorded."""
        last = self.last_success_at(pipeline_name)
        if last is None:
            return None
        now = datetime.now(timezone.utc)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return (now - last).total_seconds() / 60.0

    def clear(self, pipeline_name: str) -> None:
        """Remove the checkpoint for *pipeline_name*."""
        self._conn.execute(
            "DELETE FROM checkpoints WHERE pipeline_name = ?",
            (pipeline_name,),
        )
        self._conn.commit()
