"""Configuration helpers for :class:`SuppressionNotifier`."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pipewatch.suppression import SuppressionStore
from pipewatch.notifiers.suppression_notifier import SuppressionNotifier

_DEFAULT_DB = "pipewatch_suppression.db"
_DEFAULT_COOLDOWN = 60


@dataclass
class SuppressionConfig:
    """Validated configuration for the suppression notifier."""

    cooldown_minutes: int = _DEFAULT_COOLDOWN
    db_path: str = _DEFAULT_DB

    def __post_init__(self) -> None:
        if self.cooldown_minutes < 0:
            raise ValueError("cooldown_minutes must be non-negative")
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def suppression_config_from_dict(data: dict[str, Any]) -> SuppressionConfig:
    """Build a :class:`SuppressionConfig` from a raw mapping."""
    return SuppressionConfig(
        cooldown_minutes=int(data.get("cooldown_minutes", _DEFAULT_COOLDOWN)),
        db_path=str(data.get("db_path", _DEFAULT_DB)),
    )


def wrap_with_suppression(notifier: object, cfg: SuppressionConfig) -> SuppressionNotifier:
    """Wrap *notifier* with a :class:`SuppressionNotifier` using *cfg*."""
    store = SuppressionStore(db_path=cfg.db_path)
    return SuppressionNotifier(
        inner=notifier,  # type: ignore[arg-type]
        store=store,
        cooldown_minutes=cfg.cooldown_minutes,
    )
