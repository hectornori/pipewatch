"""Tracks open incidents per pipeline to avoid duplicate alerting."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Incident:
    pipeline_name: str
    opened_at: datetime
    last_seen_at: datetime
    error_message: Optional[str]
    resolved: bool = False


@dataclass
class IncidentTracker:
    db_path: str
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                pipeline_name TEXT NOT NULL,
                opened_at     TEXT NOT NULL,
                last_seen_at  TEXT NOT NULL,
                error_message TEXT,
                resolved      INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.commit()

    def open_or_update(self, pipeline_name: str, error_message: Optional[str]) -> Incident:
        """Open a new incident or update last_seen_at on an existing open one."""
        now = datetime.now(timezone.utc).isoformat()
        row = self._conn.execute(
            "SELECT rowid, opened_at FROM incidents WHERE pipeline_name = ? AND resolved = 0",
            (pipeline_name,),
        ).fetchone()
        if row:
            self._conn.execute(
                "UPDATE incidents SET last_seen_at = ?, error_message = ? WHERE rowid = ?",
                (now, error_message, row[0]),
            )
            self._conn.commit()
            return Incident(
                pipeline_name=pipeline_name,
                opened_at=datetime.fromisoformat(row[1]),
                last_seen_at=datetime.fromisoformat(now),
                error_message=error_message,
            )
        self._conn.execute(
            "INSERT INTO incidents (pipeline_name, opened_at, last_seen_at, error_message) VALUES (?, ?, ?, ?)",
            (pipeline_name, now, now, error_message),
        )
        self._conn.commit()
        return Incident(
            pipeline_name=pipeline_name,
            opened_at=datetime.fromisoformat(now),
            last_seen_at=datetime.fromisoformat(now),
            error_message=error_message,
        )

    def resolve(self, pipeline_name: str) -> bool:
        """Mark the open incident for a pipeline as resolved. Returns True if one existed."""
        cursor = self._conn.execute(
            "UPDATE incidents SET resolved = 1 WHERE pipeline_name = ? AND resolved = 0",
            (pipeline_name,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def get_open(self, pipeline_name: str) -> Optional[Incident]:
        """Return the current open incident for a pipeline, or None."""
        row = self._conn.execute(
            "SELECT opened_at, last_seen_at, error_message FROM incidents WHERE pipeline_name = ? AND resolved = 0",
            (pipeline_name,),
        ).fetchone()
        if not row:
            return None
        return Incident(
            pipeline_name=pipeline_name,
            opened_at=datetime.fromisoformat(row[0]),
            last_seen_at=datetime.fromisoformat(row[1]),
            error_message=row[2],
        )

    def has_open(self, pipeline_name: str) -> bool:
        return self.get_open(pipeline_name) is not None
