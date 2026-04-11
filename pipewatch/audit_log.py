"""Append-only audit log for pipeline check events and alert dispatches."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class AuditEntry:
    id: int
    event_type: str        # e.g. "check", "alert", "mute", "escalation"
    pipeline_name: str
    detail: str
    ts: datetime


@dataclass
class AuditLog:
    db_path: str

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                pipeline   TEXT NOT NULL,
                detail     TEXT NOT NULL,
                ts         TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, event_type: str, pipeline_name: str, detail: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO audit_log (event_type, pipeline, detail, ts) VALUES (?, ?, ?, ?)",
            (event_type, pipeline_name, detail, ts),
        )
        self._conn.commit()

    def get_recent(self, pipeline_name: str, limit: int = 50) -> List[AuditEntry]:
        cur = self._conn.execute(
            "SELECT id, event_type, pipeline, detail, ts FROM audit_log "
            "WHERE pipeline = ? ORDER BY ts DESC LIMIT ?",
            (pipeline_name, limit),
        )
        return [
            AuditEntry(
                id=row[0],
                event_type=row[1],
                pipeline_name=row[2],
                detail=row[3],
                ts=datetime.fromisoformat(row[4]),
            )
            for row in cur.fetchall()
        ]

    def get_all(self, limit: int = 200) -> List[AuditEntry]:
        cur = self._conn.execute(
            "SELECT id, event_type, pipeline, detail, ts FROM audit_log "
            "ORDER BY ts DESC LIMIT ?",
            (limit,),
        )
        return [
            AuditEntry(
                id=row[0],
                event_type=row[1],
                pipeline_name=row[2],
                detail=row[3],
                ts=datetime.fromisoformat(row[4]),
            )
            for row in cur.fetchall()
        ]
