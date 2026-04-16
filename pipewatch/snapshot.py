"""Persistent store for the most-recent CheckResult snapshot per pipeline."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class PipelineSnapshot:
    pipeline_name: str
    success: bool
    error_message: Optional[str]
    recorded_at: datetime


@dataclass
class SnapshotStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                pipeline_name TEXT PRIMARY KEY,
                success       INTEGER NOT NULL,
                error_message TEXT,
                recorded_at   TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def save(self, result) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO snapshots (pipeline_name, success, error_message, recorded_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(pipeline_name) DO UPDATE SET
                success       = excluded.success,
                error_message = excluded.error_message,
                recorded_at   = excluded.recorded_at
            """,
            (
                result.pipeline_name,
                int(result.success),
                result.error_message,
                now,
            ),
        )
        self._conn.commit()

    def get(self, pipeline_name: str) -> Optional[PipelineSnapshot]:
        row = self._conn.execute(
            "SELECT pipeline_name, success, error_message, recorded_at "
            "FROM snapshots WHERE pipeline_name = ?",
            (pipeline_name,),
        ).fetchone()
        if row is None:
            return None
        return PipelineSnapshot(
            pipeline_name=row[0],
            success=bool(row[1]),
            error_message=row[2],
            recorded_at=datetime.fromisoformat(row[3]),
        )

    def all(self) -> list[PipelineSnapshot]:
        rows = self._conn.execute(
            "SELECT pipeline_name, success, error_message, recorded_at FROM snapshots"
        ).fetchall()
        return [
            PipelineSnapshot(
                pipeline_name=r[0],
                success=bool(r[1]),
                error_message=r[2],
                recorded_at=datetime.fromisoformat(r[3]),
            )
            for r in rows
        ]
