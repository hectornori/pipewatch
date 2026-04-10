"""On-call schedule management for routing alerts to the right person."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class OnCallEntry:
    name: str
    contact: str  # email or Slack user ID
    start_utc: datetime
    end_utc: datetime

    def is_active(self, at: Optional[datetime] = None) -> bool:
        """Return True if this entry covers the given moment (default: now)."""
        now = at or datetime.now(timezone.utc)
        # Ensure timezone-aware comparison
        start = self.start_utc.replace(tzinfo=timezone.utc) if self.start_utc.tzinfo is None else self.start_utc
        end = self.end_utc.replace(tzinfo=timezone.utc) if self.end_utc.tzinfo is None else self.end_utc
        return start <= now < end


@dataclass
class OnCallStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS on_call (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL,
                contact TEXT NOT NULL,
                start_utc TEXT NOT NULL,
                end_utc   TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def add(self, entry: OnCallEntry) -> None:
        """Insert an on-call rotation entry."""
        self._conn.execute(
            "INSERT INTO on_call (name, contact, start_utc, end_utc) VALUES (?, ?, ?, ?)",
            (
                entry.name,
                entry.contact,
                entry.start_utc.isoformat(),
                entry.end_utc.isoformat(),
            ),
        )
        self._conn.commit()

    def current(self, at: Optional[datetime] = None) -> Optional[OnCallEntry]:
        """Return the active on-call entry at *at* (default: now)."""
        now = at or datetime.now(timezone.utc)
        row = self._conn.execute(
            """
            SELECT name, contact, start_utc, end_utc FROM on_call
            WHERE start_utc <= ? AND end_utc > ?
            ORDER BY start_utc DESC LIMIT 1
            """,
            (now.isoformat(), now.isoformat()),
        ).fetchone()
        if row is None:
            return None
        return OnCallEntry(
            name=row[0],
            contact=row[1],
            start_utc=datetime.fromisoformat(row[2]),
            end_utc=datetime.fromisoformat(row[3]),
        )

    def all_entries(self) -> list[OnCallEntry]:
        """Return all stored on-call entries ordered by start time."""
        rows = self._conn.execute(
            "SELECT name, contact, start_utc, end_utc FROM on_call ORDER BY start_utc"
        ).fetchall()
        return [
            OnCallEntry(
                name=r[0],
                contact=r[1],
                start_utc=datetime.fromisoformat(r[2]),
                end_utc=datetime.fromisoformat(r[3]),
            )
            for r in rows
        ]
