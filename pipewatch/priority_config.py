"""Configuration helpers for the priority notifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PriorityConfig:
    """Parsed priority routing configuration."""
    routes: list[dict[str, Any]]
    default_notifier: str | None = None

    def __post_init__(self) -> None:
        for route in self.routes:
            if "min_priority" not in route:
                raise ValueError("Each priority route must include 'min_priority'.")
            if not isinstance(route["min_priority"], int):
                raise TypeError("'min_priority' must be an integer.")
            if route["min_priority"] < 0:
                raise ValueError("'min_priority' must be >= 0.")
            if "notifier" not in route:
                raise ValueError("Each priority route must include 'notifier'.")


def priority_config_from_dict(data: dict[str, Any]) -> PriorityConfig:
    """Build a PriorityConfig from a raw config dictionary."""
    routes = data.get("routes", [])
    default_notifier = data.get("default_notifier")
    return PriorityConfig(routes=routes, default_notifier=default_notifier)
