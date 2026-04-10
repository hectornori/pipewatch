"""Pipeline ownership registry — maps pipelines to owning teams or individuals."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class OwnershipEntry:
    pipeline_name: str
    owner: str          # e.g. "team-data-eng" or "alice@example.com"
    notes: str = ""
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class OwnershipStore:
    db_path: str = ":memory:"

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ownership (
                pipeline_name TEXT PRIMARY KEY,
                owner         TEXT NOT NULL,
                notes         TEXT NOT NULL DEFAULT '',
                updated_at    TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def upsert(self, entry: OwnershipEntry) -> None:
        """Insert or replace an ownership record."""
        self._conn.execute(
            """
            INSERT INTO ownership (pipeline_name, owner, notes, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(pipeline_name) DO UPDATE SET
                owner      = excluded.owner,
                notes      = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                entry.pipeline_name,
                entry.owner,
                entry.notes,
                entry.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get(self, pipeline_name: str) -> Optional[OwnershipEntry]:
        """Return the ownership entry for *pipeline_name*, or None."""
        row = self._conn.execute(
            "SELECT pipeline_name, owner, notes, updated_at FROM ownership WHERE pipeline_name = ?",
            (pipeline_name,),
        ).fetchone()
        if row is None:
            return None
        return OwnershipEntry(
            pipeline_name=row[0],
            owner=row[1],
            notes=row[2],
            updated_at=datetime.fromisoformat(row[3]),
        )

    def all(self) -> list[OwnershipEntry]:
        """Return all ownership entries ordered by pipeline name."""
        rows = self._conn.execute(
            "SELECT pipeline_name, owner, notes, updated_at FROM ownership ORDER BY pipeline_name"
        ).fetchall()
        return [
            OwnershipEntry(
                pipeline_name=r[0],
                owner=r[1],
                notes=r[2],
                updated_at=datetime.fromisoformat(r[3]),
            )
            for r in rows
        ]

    def delete(self, pipeline_name: str) -> bool:
        """Remove an entry; returns True if a row was deleted."""
        cursor = self._conn.execute(
            "DELETE FROM ownership WHERE pipeline_name = ?", (pipeline_name,)
        )
        self._conn.commit()
        return cursor.rowcount > 0
