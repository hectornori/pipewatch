"""Collect and store per-pipeline runtime metrics (duration, exit code)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from pipewatch.monitor import CheckResult


@dataclass
class PipelineMetric:
    pipeline: str
    success: bool
    duration_seconds: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None


@dataclass
class MetricCollector:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline TEXT NOT NULL,
                success INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                error_message TEXT,
                recorded_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, result: CheckResult, duration_seconds: float) -> None:
        self._conn.execute(
            """
            INSERT INTO pipeline_metrics
                (pipeline, success, duration_seconds, error_message, recorded_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                result.pipeline,
                int(result.success),
                duration_seconds,
                result.error_message,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def get_recent(self, pipeline: str, limit: int = 20) -> List[PipelineMetric]:
        rows = self._conn.execute(
            """
            SELECT pipeline, success, duration_seconds, error_message, recorded_at
            FROM pipeline_metrics
            WHERE pipeline = ?
            ORDER BY recorded_at DESC
            LIMIT ?
            """,
            (pipeline, limit),
        ).fetchall()
        return [
            PipelineMetric(
                pipeline=r[0],
                success=bool(r[1]),
                duration_seconds=r[2],
                error_message=r[3],
                recorded_at=datetime.fromisoformat(r[4]),
            )
            for r in rows
        ]

    def average_duration(self, pipeline: str, limit: int = 20) -> Optional[float]:
        row = self._conn.execute(
            """
            SELECT AVG(duration_seconds)
            FROM (
                SELECT duration_seconds FROM pipeline_metrics
                WHERE pipeline = ?
                ORDER BY recorded_at DESC
                LIMIT ?
            )
            """,
            (pipeline, limit),
        ).fetchone()
        return row[0] if row and row[0] is not None else None
