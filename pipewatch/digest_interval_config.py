"""Configuration for DigestIntervalNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class DigestIntervalConfig:
    interval_seconds: float = 300.0
    db_path: str = "pipewatch.db"

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")


def digest_interval_config_from_dict(data: Dict[str, Any]) -> DigestIntervalConfig:
    """Build a DigestIntervalConfig from a raw config dict."""
    return DigestIntervalConfig(
        interval_seconds=float(data.get("interval_seconds", 300.0)),
        db_path=str(data.get("db_path", "pipewatch.db")),
    )


def wrap_with_digest_interval(inner, data: Dict[str, Any]):
    """Wrap *inner* notifier with DigestIntervalNotifier using *data* config."""
    from pipewatch.notifiers.digest_interval_notifier import DigestIntervalNotifier

    cfg = digest_interval_config_from_dict(data)
    return DigestIntervalNotifier(inner=inner, interval_seconds=cfg.interval_seconds)
