"""Configuration helpers for QuotaNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from pipewatch.notifiers import Notifier
from pipewatch.notifiers.quota_notifier import QuotaNotifier, QuotaStore


@dataclass
class QuotaConfig:
    max_count: int
    window_seconds: int
    db_path: str = ":memory:"

    def __post_init__(self) -> None:
        if self.max_count < 1:
            raise ValueError("max_count must be >= 1")
        if self.window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")


def quota_config_from_dict(data: Dict[str, Any]) -> QuotaConfig:
    """Build a QuotaConfig from a plain dictionary (e.g. parsed YAML)."""
    max_count = data.get("max_count")
    window_seconds = data.get("window_seconds")
    if max_count is None:
        raise KeyError("quota config requires 'max_count'")
    if window_seconds is None:
        raise KeyError("quota config requires 'window_seconds'")
    return QuotaConfig(
        max_count=int(max_count),
        window_seconds=int(window_seconds),
        db_path=str(data.get("db_path", ":memory:")),
    )


def wrap_with_quota(inner: Notifier, cfg: QuotaConfig) -> QuotaNotifier:
    """Convenience factory: creates the store and wraps *inner*."""
    store = QuotaStore(db_path=cfg.db_path)
    return QuotaNotifier(
        inner=inner,
        store=store,
        max_count=cfg.max_count,
        window_seconds=cfg.window_seconds,
    )
