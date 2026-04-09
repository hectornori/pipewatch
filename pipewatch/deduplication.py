"""Alert deduplication: prevent sending the same alert multiple times within a window."""

from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeduplicationStore:
    """Tracks recently sent alerts to avoid duplicates within a time window."""

    db_path: str = ":memory:"
    window_seconds: int = 3600  # default: 1 hour dedup window
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dedup_log (
                alert_key TEXT NOT NULL,
                sent_at   REAL NOT NULL
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_dedup_key ON dedup_log (alert_key)"
        )
        self._conn.commit()

    @staticmethod
    def make_key(pipeline_name: str, error_message: Optional[str]) -> str:
        """Produce a stable hash key for a (pipeline, error) pair."""
        raw = f"{pipeline_name}:{error_message or ''}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def is_duplicate(self, alert_key: str) -> bool:
        """Return True if the same alert was already sent within the dedup window."""
        cutoff = time.time() - self.window_seconds
        row = self._conn.execute(
            "SELECT 1 FROM dedup_log WHERE alert_key = ? AND sent_at >= ? LIMIT 1",
            (alert_key, cutoff),
        ).fetchone()
        return row is not None

    def record(self, alert_key: str) -> None:
        """Mark an alert as sent right now."""
        self._conn.execute(
            "INSERT INTO dedup_log (alert_key, sent_at) VALUES (?, ?)",
            (alert_key, time.time()),
        )
        self._conn.commit()

    def purge_expired(self) -> int:
        """Remove entries older than the dedup window. Returns count deleted."""
        cutoff = time.time() - self.window_seconds
        cur = self._conn.execute(
            "DELETE FROM dedup_log WHERE sent_at < ?", (cutoff,)
        )
        self._conn.commit()
        return cur.rowcount
