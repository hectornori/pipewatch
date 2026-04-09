"""Pipeline state snapshot — persists the last known status of each pipeline."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pipewatch.monitor import CheckResult


@dataclass
class PipelineSnapshot:
    pipeline_name: str
    status: str          # "ok" | "fail"
    last_checked: datetime
    last_error: Optional[str] = None


class SnapshotStore:
    """Stores and retrieves the most-recent check result per pipeline."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                pipeline_name TEXT PRIMARY KEY,
                status        TEXT NOT NULL,
                last_checked  TEXT NOT NULL,
                last_error    TEXT
            )
            """
        )
        self._conn.commit()

    def save(self, result: CheckResult) -> None:
        """Upsert the snapshot for a pipeline."""
        status = "ok" if result.success else "fail"
        self._conn.execute(
            """
            INSERT INTO snapshots (pipeline_name, status, last_checked, last_error)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(pipeline_name) DO UPDATE SET
                status       = excluded.status,
                last_checked = excluded.last_checked,
                last_error   = excluded.last_error
            """,
            (
                result.pipeline_name,
                status,
                datetime.utcnow().isoformat(),
                result.error_message,
            ),
        )
        self._conn.commit()

    def get(self, pipeline_name: str) -> Optional[PipelineSnapshot]:
        """Return the latest snapshot for *pipeline_name*, or None."""
        row = self._conn.execute(
            "SELECT pipeline_name, status, last_checked, last_error "
            "FROM snapshots WHERE pipeline_name = ?",
            (pipeline_name,),
        ).fetchone()
        if row is None:
            return None
        return PipelineSnapshot(
            pipeline_name=row[0],
            status=row[1],
            last_checked=datetime.fromisoformat(row[2]),
            last_error=row[3],
        )

    def all(self) -> list[PipelineSnapshot]:
        """Return snapshots for every known pipeline."""
        rows = self._conn.execute(
            "SELECT pipeline_name, status, last_checked, last_error FROM snapshots"
        ).fetchall()
        return [
            PipelineSnapshot(
                pipeline_name=r[0],
                status=r[1],
                last_checked=datetime.fromisoformat(r[2]),
                last_error=r[3],
            )
            for r in rows
        ]
