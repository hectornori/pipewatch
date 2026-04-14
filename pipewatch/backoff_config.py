"""Configuration helpers for BackoffNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pipewatch.notifiers.backoff_notifier import BackoffNotifier, Notifier


@dataclass
class BackoffConfig:
    """Validated configuration for BackoffNotifier."""

    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0

    def __post_init__(self) -> None:
        if self.base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.multiplier < 1.0:
            raise ValueError("multiplier must be >= 1.0")


def backoff_config_from_dict(data: dict[str, Any]) -> BackoffConfig:
    """Build a BackoffConfig from a raw config dictionary."""
    return BackoffConfig(
        base_delay=float(data.get("base_delay", 1.0)),
        max_delay=float(data.get("max_delay", 60.0)),
        multiplier=float(data.get("multiplier", 2.0)),
    )


def wrap_with_backoff(inner: Notifier, data: dict[str, Any]) -> BackoffNotifier:
    """Wrap *inner* with a BackoffNotifier built from *data*."""
    cfg = backoff_config_from_dict(data)
    return BackoffNotifier(
        inner=inner,
        base_delay=cfg.base_delay,
        max_delay=cfg.max_delay,
        multiplier=cfg.multiplier,
    )
