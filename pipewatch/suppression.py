"""Alert suppression: silence alerts for a pipeline within a cooldown window."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SuppressionStore:
    """Tracks when alerts were last sent to avoid spamming during repeated failures."""

    db_path: str = ":memory:"

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS suppression (
                pipeline_name TEXT PRIMARY KEY,
                last_alerted_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def record_alert(self, pipeline_name: str) -> None:
        """Record that an alert was just sent for *pipeline_name*."""
        self._conn.execute(
            """
            INSERT INTO suppression (pipeline_name, last_alerted_at)
            VALUES (?, ?)
            ON CONFLICT(pipeline_name) DO UPDATE SET last_alerted_at = excluded.last_alerted_at
            """,
            (pipeline_name, time.time()),
        )
        self._conn.commit()

    def last_alerted_at(self, pipeline_name: str) -> Optional[float]:
        """Return epoch timestamp of the last alert for *pipeline_name*, or None."""
        row = self._conn.execute(
            "SELECT last_alerted_at FROM suppression WHERE pipeline_name = ?",
            (pipeline_name,),
        ).fetchone()
        return row[0] if row else None

    def is_suppressed(self, pipeline_name: str, cooldown_seconds: int) -> bool:
        """Return True if an alert was sent within *cooldown_seconds* ago."""
        last = self.last_alerted_at(pipeline_name)
        if last is None:
            return False
        return (time.time() - last) < cooldown_seconds

    def clear(self, pipeline_name: str) -> None:
        """Remove suppression record for *pipeline_name* (e.g. after a recovery)."""
        self._conn.execute(
            "DELETE FROM suppression WHERE pipeline_name = ?",
            (pipeline_name,),
        )
        self._conn.commit()
