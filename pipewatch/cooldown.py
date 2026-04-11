"""Cooldown tracking: prevent repeated alerts within a minimum interval."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CooldownStore:
    db_path: str
    default_minutes: int = 60
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.default_minutes < 0:
            raise ValueError("default_minutes must be >= 0")
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cooldowns (
                pipeline TEXT PRIMARY KEY,
                last_alerted_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, pipeline: str) -> None:
        """Record that an alert was sent for *pipeline* right now."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO cooldowns (pipeline, last_alerted_at)
            VALUES (?, ?)
            ON CONFLICT(pipeline) DO UPDATE SET last_alerted_at = excluded.last_alerted_at
            """,
            (pipeline, now),
        )
        self._conn.commit()

    def last_alerted_at(self, pipeline: str) -> Optional[datetime]:
        """Return the UTC datetime of the last alert for *pipeline*, or None."""
        row = self._conn.execute(
            "SELECT last_alerted_at FROM cooldowns WHERE pipeline = ?",
            (pipeline,),
        ).fetchone()
        if row is None:
            return None
        return datetime.fromisoformat(row[0])

    def is_cooling_down(
        self, pipeline: str, cooldown_minutes: Optional[int] = None
    ) -> bool:
        """Return True if *pipeline* is still within its cooldown window."""
        minutes = cooldown_minutes if cooldown_minutes is not None else self.default_minutes
        last = self.last_alerted_at(pipeline)
        if last is None:
            return False
        elapsed = (datetime.now(timezone.utc) - last).total_seconds() / 60.0
        return elapsed < minutes

    def clear(self, pipeline: str) -> None:
        """Remove the cooldown record for *pipeline* (e.g. after a recovery)."""
        self._conn.execute(
            "DELETE FROM cooldowns WHERE pipeline = ?", (pipeline,)
        )
        self._conn.commit()
