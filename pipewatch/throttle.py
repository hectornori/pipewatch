"""Throttle: per-pipeline notification throttling with configurable min-interval."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ThrottleStore:
    db_path: str
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS throttle (
                pipeline TEXT NOT NULL,
                channel  TEXT NOT NULL,
                sent_at  TEXT NOT NULL,
                PRIMARY KEY (pipeline, channel)
            )
            """
        )
        self._conn.commit()

    def record(self, pipeline: str, channel: str) -> None:
        """Record that a notification was sent right now."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO throttle (pipeline, channel, sent_at)
            VALUES (?, ?, ?)
            ON CONFLICT(pipeline, channel) DO UPDATE SET sent_at = excluded.sent_at
            """,
            (pipeline, channel, now),
        )
        self._conn.commit()

    def last_sent_at(self, pipeline: str, channel: str) -> Optional[datetime]:
        """Return the timestamp of the last notification, or None."""
        row = self._conn.execute(
            "SELECT sent_at FROM throttle WHERE pipeline = ? AND channel = ?",
            (pipeline, channel),
        ).fetchone()
        if row is None:
            return None
        return datetime.fromisoformat(row[0])

    def is_throttled(self, pipeline: str, channel: str, min_interval_seconds: int) -> bool:
        """Return True if a notification was sent within *min_interval_seconds*."""
        last = self.last_sent_at(pipeline, channel)
        if last is None:
            return False
        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        return elapsed < min_interval_seconds

    def clear(self, pipeline: str, channel: str) -> None:
        """Remove the throttle record for a pipeline/channel pair."""
        self._conn.execute(
            "DELETE FROM throttle WHERE pipeline = ? AND channel = ?",
            (pipeline, channel),
        )
        self._conn.commit()
