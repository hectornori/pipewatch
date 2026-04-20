"""Configuration helpers for :class:`FingerprintNotifier`."""
from __future__ import annotations

from dataclasses import dataclass

from pipewatch.notifiers.fingerprint_notifier import (
    FingerprintNotifier,
    FingerprintStore,
    Notifier,
)


@dataclass
class FingerprintConfig:
    ttl_seconds: float = 300.0
    db_path: str = ":memory:"

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def fingerprint_config_from_dict(data: dict) -> FingerprintConfig:
    """Build a :class:`FingerprintConfig` from a plain mapping.

    Accepted keys:
        ``ttl_seconds`` (float, default 300)
        ``db_path``     (str,   default ":memory:")
    """
    return FingerprintConfig(
        ttl_seconds=float(data.get("ttl_seconds", 300.0)),
        db_path=str(data.get("db_path", ":memory:")),
    )


def wrap_with_fingerprint(inner: Notifier, cfg: FingerprintConfig) -> FingerprintNotifier:
    """Convenience factory: create a store and return a wrapped notifier."""
    store = FingerprintStore(db_path=cfg.db_path)
    return FingerprintNotifier(inner=inner, store=store, ttl_seconds=cfg.ttl_seconds)
