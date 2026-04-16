"""Configuration for the LatencyNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LatencyConfig:
    threshold_seconds: float
    db_path: str = "pipewatch_latency.db"

    def __post_init__(self) -> None:
        if self.threshold_seconds <= 0:
            raise ValueError("threshold_seconds must be positive")


def latency_config_from_dict(data: dict[str, Any]) -> LatencyConfig:
    if "threshold_seconds" not in data:
        raise KeyError("latency config requires 'threshold_seconds'")
    return LatencyConfig(
        threshold_seconds=float(data["threshold_seconds"]),
        db_path=data.get("db_path", "pipewatch_latency.db"),
    )


def wrap_with_latency(notifier, config: LatencyConfig):
    from pipewatch.notifiers.latency_notifier import LatencyNotifier
    return LatencyNotifier(inner=notifier, threshold_seconds=config.threshold_seconds)
