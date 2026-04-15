"""Configuration helpers for DebounceNotifier."""
from __future__ import annotations

from dataclasses import dataclass

from pipewatch.notifiers.debounce_notifier import DebounceNotifier, DebounceStore


@dataclass
class DebounceConfig:
    window_seconds: float = 60.0
    db_path: str = ":memory:"

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")


def debounce_config_from_dict(data: dict) -> DebounceConfig:
    """Build a DebounceConfig from a plain dictionary (e.g. loaded from YAML)."""
    return DebounceConfig(
        window_seconds=float(data.get("window_seconds", 60.0)),
        db_path=str(data.get("db_path", ":memory:")),
    )


def wrap_with_debounce(inner, cfg: DebounceConfig) -> DebounceNotifier:
    """Wrap an existing notifier with debounce behaviour."""
    store = DebounceStore(db_path=cfg.db_path)
    return DebounceNotifier(
        inner=inner,
        store=store,
        window_seconds=cfg.window_seconds,
    )
