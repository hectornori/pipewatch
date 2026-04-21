"""Configuration helpers for BurstNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pipewatch.notifiers.burst_notifier import BurstNotifier, BurstStore

_DEFAULT_DB = "pipewatch_burst.db"


@dataclass
class BurstConfig:
    max_count: int
    window_seconds: float
    db_path: str = _DEFAULT_DB

    def __post_init__(self) -> None:
        if self.max_count < 1:
            raise ValueError("max_count must be >= 1")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def burst_config_from_dict(data: dict[str, Any]) -> BurstConfig:
    """Build a :class:`BurstConfig` from a raw config dictionary."""
    if "max_count" not in data:
        raise KeyError("burst config requires 'max_count'")
    if "window_seconds" not in data:
        raise KeyError("burst config requires 'window_seconds'")
    return BurstConfig(
        max_count=int(data["max_count"]),
        window_seconds=float(data["window_seconds"]),
        db_path=str(data.get("db_path", _DEFAULT_DB)),
    )


def wrap_with_burst(inner: object, cfg: BurstConfig) -> BurstNotifier:
    """Wrap *inner* notifier with burst-limiting behaviour."""
    store = BurstStore(db_path=cfg.db_path)
    return BurstNotifier(
        inner=inner,  # type: ignore[arg-type]
        store=store,
        max_count=cfg.max_count,
        window_seconds=cfg.window_seconds,
    )
