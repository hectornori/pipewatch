"""Runbook links: attach documentation URLs to pipelines for alert context."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RunbookEntry:
    pipeline_name: str
    url: str
    description: str = ""
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RunbookStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runbooks (
                pipeline_name TEXT PRIMARY KEY,
                url           TEXT NOT NULL,
                description   TEXT NOT NULL DEFAULT '',
                updated_at    TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def upsert(self, entry: RunbookEntry) -> None:
        self._conn.execute(
            """
            INSERT INTO runbooks (pipeline_name, url, description, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(pipeline_name) DO UPDATE SET
                url = excluded.url,
                description = excluded.description,
                updated_at  = excluded.updated_at
            """,
            (
                entry.pipeline_name,
                entry.url,
                entry.description,
                entry.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get(self, pipeline_name: str) -> Optional[RunbookEntry]:
        row = self._conn.execute(
            "SELECT pipeline_name, url, description, updated_at FROM runbooks WHERE pipeline_name = ?",
            (pipeline_name,),
        ).fetchone()
        if row is None:
            return None
        return RunbookEntry(
            pipeline_name=row[0],
            url=row[1],
            description=row[2],
            updated_at=datetime.fromisoformat(row[3]),
        )

    def all(self) -> list[RunbookEntry]:
        rows = self._conn.execute(
            "SELECT pipeline_name, url, description, updated_at FROM runbooks ORDER BY pipeline_name"
        ).fetchall()
        return [
            RunbookEntry(
                pipeline_name=r[0],
                url=r[1],
                description=r[2],
                updated_at=datetime.fromisoformat(r[3]),
            )
            for r in rows
        ]

    def delete(self, pipeline_name: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM runbooks WHERE pipeline_name = ?", (pipeline_name,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def format_for_alert(self, pipeline_name: str) -> str:
        """Return a short string suitable for embedding in alert messages."""
        entry = self.get(pipeline_name)
        if entry is None:
            return ""
        parts = [f"Runbook: {entry.url}"]
        if entry.description:
            parts.append(f"({entry.description})")
        return " ".join(parts)
