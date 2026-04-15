"""Configuration helpers for the acknowledge notifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from pipewatch.notifiers import Notifier
from pipewatch.notifiers.acknowledge_notifier import AcknowledgeStore, AcknowledgeNotifier


@dataclass
class AcknowledgeConfig:
    db_path: str = ":memory:"

    def __post_init__(self) -> None:
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def acknowledge_config_from_dict(raw: Dict[str, Any]) -> AcknowledgeConfig:
    """Build an AcknowledgeConfig from a raw config dictionary."""
    db_path = raw.get("db_path", ":memory:")
    if not isinstance(db_path, str):
        raise TypeError(f"db_path must be a string, got {type(db_path).__name__}")
    return AcknowledgeConfig(db_path=db_path)


def wrap_with_acknowledge(inner: Notifier, raw: Dict[str, Any]) -> AcknowledgeNotifier:
    """Wrap *inner* with an AcknowledgeNotifier built from *raw* config."""
    cfg = acknowledge_config_from_dict(raw)
    store = AcknowledgeStore(db_path=cfg.db_path)
    return AcknowledgeNotifier(inner=inner, store=store)
