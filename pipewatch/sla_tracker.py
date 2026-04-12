"""SLA tracking: record expected completion times and detect breaches."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SLABreach:
    pipeline_name: str
    expected_by: datetime
    detected_at: datetime
    minutes_overdue: float

    @property
    def reason(self) -> str:
        return (
            f"Pipeline '{self.pipeline_name}' breached SLA by "
            f"{self.minutes_overdue:.1f} minutes "
            f"(expected by {self.expected_by.isoformat()})"
        )


@dataclass
class SLATracker:
    db_path: str
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sla_windows (
                pipeline_name TEXT PRIMARY KEY,
                expected_by   TEXT NOT NULL,
                registered_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def register(self, pipeline_name: str, expected_by: datetime) -> None:
        """Register or update the SLA deadline for a pipeline."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO sla_windows (pipeline_name, expected_by, registered_at)
            VALUES (?, ?, ?)
            ON CONFLICT(pipeline_name) DO UPDATE SET
                expected_by   = excluded.expected_by,
                registered_at = excluded.registered_at
            """,
            (pipeline_name, expected_by.isoformat(), now),
        )
        self._conn.commit()

    def clear(self, pipeline_name: str) -> None:
        """Remove the SLA entry once a pipeline has completed successfully."""
        self._conn.execute(
            "DELETE FROM sla_windows WHERE pipeline_name = ?",
            (pipeline_name,),
        )
        self._conn.commit()

    def check_breach(
        self, pipeline_name: str, now: Optional[datetime] = None
    ) -> Optional[SLABreach]:
        """Return an SLABreach if the deadline has passed, else None."""
        if now is None:
            now = datetime.now(timezone.utc)
        row = self._conn.execute(
            "SELECT expected_by FROM sla_windows WHERE pipeline_name = ?",
            (pipeline_name,),
        ).fetchone()
        if row is None:
            return None
        expected_by = datetime.fromisoformat(row[0])
        if expected_by.tzinfo is None:
            expected_by = expected_by.replace(tzinfo=timezone.utc)
        if now <= expected_by:
            return None
        minutes_overdue = (now - expected_by).total_seconds() / 60
        return SLABreach(
            pipeline_name=pipeline_name,
            expected_by=expected_by,
            detected_at=now,
            minutes_overdue=minutes_overdue,
        )

    def check_all_breaches(
        self, now: Optional[datetime] = None
    ) -> list[SLABreach]:
        """Return SLA breaches for every registered pipeline."""
        if now is None:
            now = datetime.now(timezone.utc)
        rows = self._conn.execute(
            "SELECT pipeline_name FROM sla_windows"
        ).fetchall()
        breaches = []
        for (name,) in rows:
            breach = self.check_breach(name, now=now)
            if breach is not None:
                breaches.append(breach)
        return breaches
