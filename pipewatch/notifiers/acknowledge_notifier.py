"""Notifier wrapper that suppresses alerts for acknowledged pipelines."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from pipewatch.notifiers import Notifier, send


@dataclass
class AcknowledgeStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS acknowledgements (
                pipeline TEXT PRIMARY KEY,
                acknowledged_until TEXT NOT NULL,
                reason TEXT
            )
            """
        )
        self._conn.commit()

    def acknowledge(self, pipeline: str, until: datetime, reason: Optional[str] = None) -> None:
        self._conn.execute(
            """
            INSERT INTO acknowledgements (pipeline, acknowledged_until, reason)
            VALUES (?, ?, ?)
            ON CONFLICT(pipeline) DO UPDATE SET
                acknowledged_until = excluded.acknowledged_until,
                reason = excluded.reason
            """,
            (pipeline, until.isoformat(), reason),
        )
        self._conn.commit()

    def unacknowledge(self, pipeline: str) -> None:
        self._conn.execute(
            "DELETE FROM acknowledgements WHERE pipeline = ?", (pipeline,)
        )
        self._conn.commit()

    def is_acknowledged(self, pipeline: str) -> bool:
        now = datetime.now(tz=timezone.utc).isoformat()
        row = self._conn.execute(
            "SELECT acknowledged_until FROM acknowledgements WHERE pipeline = ? AND acknowledged_until > ?",
            (pipeline, now),
        ).fetchone()
        return row is not None

    def get_reason(self, pipeline: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT reason FROM acknowledgements WHERE pipeline = ?", (pipeline,)
        ).fetchone()
        return row[0] if row else None


@dataclass
class AcknowledgeNotifier:
    """Wraps an inner notifier and skips sending if the pipeline is acknowledged."""
    inner: Notifier
    store: AcknowledgeStore

    def send(self, result: send.__class__) -> None:  # type: ignore[valid-type]
        pipeline = getattr(result, "pipeline", None)
        if pipeline and self.store.is_acknowledged(pipeline):
            return
        self.inner.send(result)
