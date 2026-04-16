"""OnceNotifier – forwards a notification only the first time a pipeline fails.

Subsequent failures for the same pipeline are suppressed until the pipeline
recovers (i.e. a success result is observed), at which point the latch resets.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None: ...


class OnceLatchStore:
    """Persists per-pipeline 'has been alerted' state in SQLite."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS once_latch (
                pipeline TEXT PRIMARY KEY,
                latched   INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.commit()

    def is_latched(self, pipeline: str) -> bool:
        row = self._conn.execute(
            "SELECT latched FROM once_latch WHERE pipeline = ?", (pipeline,)
        ).fetchone()
        return bool(row and row[0])

    def latch(self, pipeline: str) -> None:
        self._conn.execute(
            "INSERT INTO once_latch (pipeline, latched) VALUES (?, 1)"
            " ON CONFLICT(pipeline) DO UPDATE SET latched = 1",
            (pipeline,),
        )
        self._conn.commit()

    def reset(self, pipeline: str) -> None:
        self._conn.execute(
            "INSERT INTO once_latch (pipeline, latched) VALUES (?, 0)"
            " ON CONFLICT(pipeline) DO UPDATE SET latched = 0",
            (pipeline,),
        )
        self._conn.commit()


@dataclass
class OnceNotifier:
    """Wraps an inner notifier and fires at most once per failure streak."""

    inner: Notifier
    store: OnceLatchStore = field(default_factory=OnceLatchStore)

    def send(self, result) -> None:
        pipeline = result.pipeline_name
        if result.success:
            self.store.reset(pipeline)
            return
        if self.store.is_latched(pipeline):
            return
        self.store.latch(pipeline)
        self.inner.send(result)
