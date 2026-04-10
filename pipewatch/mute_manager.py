"""Mute manager: temporarily silence alerts for specific pipelines."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class MuteManager:
    """Persist and query per-pipeline mute windows backed by SQLite."""

    db_path: str = "pipewatch_mutes.db"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mutes (
                pipeline_name TEXT NOT NULL,
                muted_until    TEXT NOT NULL,
                reason         TEXT,
                PRIMARY KEY (pipeline_name)
            )
            """
        )
        self._conn.commit()

    def mute(self, pipeline_name: str, until: datetime, reason: str = "") -> None:
        """Mute *pipeline_name* until *until* (timezone-aware recommended)."""
        self._conn.execute(
            """
            INSERT INTO mutes (pipeline_name, muted_until, reason)
            VALUES (?, ?, ?)
            ON CONFLICT(pipeline_name) DO UPDATE
                SET muted_until = excluded.muted_until,
                    reason      = excluded.reason
            """,
            (pipeline_name, until.isoformat(), reason),
        )
        self._conn.commit()

    def unmute(self, pipeline_name: str) -> None:
        """Remove any active mute for *pipeline_name*."""
        self._conn.execute(
            "DELETE FROM mutes WHERE pipeline_name = ?", (pipeline_name,)
        )
        self._conn.commit()

    def is_muted(self, pipeline_name: str) -> bool:
        """Return True if *pipeline_name* is currently muted."""
        now = datetime.now(tz=timezone.utc).isoformat()
        row = self._conn.execute(
            "SELECT muted_until FROM mutes WHERE pipeline_name = ? AND muted_until > ?",
            (pipeline_name, now),
        ).fetchone()
        return row is not None

    def muted_until(self, pipeline_name: str) -> Optional[datetime]:
        """Return the expiry timestamp for an active mute, or None."""
        now = datetime.now(tz=timezone.utc).isoformat()
        row = self._conn.execute(
            "SELECT muted_until FROM mutes WHERE pipeline_name = ? AND muted_until > ?",
            (pipeline_name, now),
        ).fetchone()
        if row is None:
            return None
        return datetime.fromisoformat(row[0])

    def active_mutes(self) -> list[dict]:
        """Return all currently active mute records."""
        now = datetime.now(tz=timezone.utc).isoformat()
        rows = self._conn.execute(
            "SELECT pipeline_name, muted_until, reason FROM mutes WHERE muted_until > ?",
            (now,),
        ).fetchall()
        return [
            {"pipeline_name": r[0], "muted_until": r[1], "reason": r[2]}
            for r in rows
        ]
