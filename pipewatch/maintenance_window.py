"""Maintenance window support — suppress alerts during scheduled downtime."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class MaintenanceWindow:
    pipeline_name: str
    start: datetime
    end: datetime
    reason: str = ""

    def is_active(self, at: Optional[datetime] = None) -> bool:
        """Return True if the window covers *at* (default: now)."""
        now = at or datetime.utcnow()
        return self.start <= now <= self.end


@dataclass
class MaintenanceStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_windows (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline    TEXT    NOT NULL,
                start_ts    TEXT    NOT NULL,
                end_ts      TEXT    NOT NULL,
                reason      TEXT    DEFAULT ''
            )
            """
        )
        self._conn.commit()

    def add(self, window: MaintenanceWindow) -> None:
        self._conn.execute(
            "INSERT INTO maintenance_windows (pipeline, start_ts, end_ts, reason) VALUES (?, ?, ?, ?)",
            (window.pipeline_name, window.start.isoformat(), window.end.isoformat(), window.reason),
        )
        self._conn.commit()

    def is_in_maintenance(self, pipeline_name: str, at: Optional[datetime] = None) -> bool:
        """Return True if *pipeline_name* has an active window at *at*."""
        now = (at or datetime.utcnow()).isoformat()
        row = self._conn.execute(
            "SELECT 1 FROM maintenance_windows WHERE pipeline = ? AND start_ts <= ? AND end_ts >= ? LIMIT 1",
            (pipeline_name, now, now),
        ).fetchone()
        return row is not None

    def active_windows(self, at: Optional[datetime] = None) -> List[MaintenanceWindow]:
        now = (at or datetime.utcnow()).isoformat()
        rows = self._conn.execute(
            "SELECT pipeline, start_ts, end_ts, reason FROM maintenance_windows WHERE start_ts <= ? AND end_ts >= ?",
            (now, now),
        ).fetchall()
        return [
            MaintenanceWindow(
                pipeline_name=r[0],
                start=datetime.fromisoformat(r[1]),
                end=datetime.fromisoformat(r[2]),
                reason=r[3],
            )
            for r in rows
        ]

    def remove_expired(self, at: Optional[datetime] = None) -> int:
        now = (at or datetime.utcnow()).isoformat()
        cur = self._conn.execute(
            "DELETE FROM maintenance_windows WHERE end_ts < ?", (now,)
        )
        self._conn.commit()
        return cur.rowcount
