"""Configuration helpers for EventLogNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pipewatch.notifiers.event_log_notifier import EventLogNotifier, EventLogStore


@dataclass
class EventLogConfig:
    db_path: str = "pipewatch_events.db"

    def __post_init__(self) -> None:
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def event_log_config_from_dict(raw: dict[str, Any]) -> EventLogConfig:
    """Parse an EventLogConfig from a raw config dictionary."""
    return EventLogConfig(
        db_path=raw.get("db_path", "pipewatch_events.db"),
    )


def wrap_with_event_log(inner: Any, raw: dict[str, Any] | None = None) -> EventLogNotifier:
    """Wrap *inner* notifier with an EventLogNotifier built from *raw* config."""
    cfg = event_log_config_from_dict(raw or {})
    store = EventLogStore(db_path=cfg.db_path)
    return EventLogNotifier(inner=inner, store=store)
