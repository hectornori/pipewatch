"""Rate limiter to throttle notifications per pipeline."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class RateLimiter:
    """Limits how frequently notifications are sent for a given pipeline."""

    db_path: str = ":memory:"
    default_window_seconds: int = 300  # 5 minutes
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.default_window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_limit (
                pipeline_name TEXT NOT NULL,
                sent_at       REAL NOT NULL
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rl_pipeline ON rate_limit (pipeline_name)"
        )
        self._conn.commit()

    def record_sent(self, pipeline_name: str) -> None:
        """Record that a notification was just sent for *pipeline_name*."""
        self._conn.execute(
            "INSERT INTO rate_limit (pipeline_name, sent_at) VALUES (?, ?)",
            (pipeline_name, time.time()),
        )
        self._conn.commit()

    def is_rate_limited(
        self, pipeline_name: str, window_seconds: Optional[int] = None
    ) -> bool:
        """Return True if a notification was sent within the configured window."""
        window = window_seconds if window_seconds is not None else self.default_window_seconds
        cutoff = time.time() - window
        row = self._conn.execute(
            "SELECT 1 FROM rate_limit WHERE pipeline_name = ? AND sent_at >= ? LIMIT 1",
            (pipeline_name, cutoff),
        ).fetchone()
        return row is not None

    def count_in_window(
        self, pipeline_name: str, window_seconds: Optional[int] = None
    ) -> int:
        """Return how many notifications were sent within the window."""
        window = window_seconds if window_seconds is not None else self.default_window_seconds
        cutoff = time.time() - window
        row = self._conn.execute(
            "SELECT COUNT(*) FROM rate_limit WHERE pipeline_name = ? AND sent_at >= ?",
            (pipeline_name, cutoff),
        ).fetchone()
        return row[0] if row else 0

    def purge_old_records(self, window_seconds: Optional[int] = None) -> int:
        """Delete records older than *window_seconds*. Returns number deleted."""
        window = window_seconds if window_seconds is not None else self.default_window_seconds
        cutoff = time.time() - window
        cur = self._conn.execute(
            "DELETE FROM rate_limit WHERE sent_at < ?", (cutoff,)
        )
        self._conn.commit()
        return cur.rowcount


def limiter_from_config(cfg: dict) -> RateLimiter:
    """Build a :class:`RateLimiter` from a plain config dict."""
    return RateLimiter(
        db_path=cfg.get("db_path", ":memory:"),
        default_window_seconds=int(cfg.get("window_seconds", 300)),
    )
