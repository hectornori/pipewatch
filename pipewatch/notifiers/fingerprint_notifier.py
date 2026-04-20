"""Notifier that suppresses alerts whose fingerprint matches a recent send.

A fingerprint is a short hash derived from the pipeline name, success flag,
and (optionally) the error message.  If the same fingerprint was forwarded
within *ttl_seconds* the alert is dropped, preventing duplicate pages when
the same failure fires repeatedly across short polling intervals.
"""
from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class FingerprintStore:
    db_path: str = ":memory:"
    _conn: sqlite3.Connection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fingerprints (
                fingerprint TEXT PRIMARY KEY,
                sent_at     REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, fingerprint: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO fingerprints (fingerprint, sent_at) VALUES (?, ?)",
            (fingerprint, time.time()),
        )
        self._conn.commit()

    def is_known(self, fingerprint: str, ttl_seconds: float) -> bool:
        cutoff = time.time() - ttl_seconds
        row = self._conn.execute(
            "SELECT sent_at FROM fingerprints WHERE fingerprint = ? AND sent_at >= ?",
            (fingerprint, cutoff),
        ).fetchone()
        return row is not None


def _make_fingerprint(result) -> str:
    pipeline = getattr(result, "pipeline_name", "")
    success = str(getattr(result, "success", ""))
    error = getattr(result, "error_message", "") or ""
    raw = f"{pipeline}:{success}:{error}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class FingerprintNotifier:
    """Wrap *inner* and drop alerts whose fingerprint was seen within *ttl_seconds*."""

    inner: Notifier
    store: FingerprintStore
    ttl_seconds: float = 300.0

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

    def send(self, result) -> None:
        fp = _make_fingerprint(result)
        if self.store.is_known(fp, self.ttl_seconds):
            return
        self.store.record(fp)
        self.inner.send(result)
