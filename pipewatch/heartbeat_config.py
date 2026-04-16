"""Configuration helpers for HeartbeatNotifier."""
from __future__ import annotations

from dataclasses import dataclass

from pipewatch.notifiers.heartbeat_notifier import HeartbeatNotifier, HeartbeatStore


@dataclass
class HeartbeatConfig:
    ttl_seconds: float = 300.0
    db_path: str = "pipewatch_heartbeat.db"

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def heartbeat_config_from_dict(data: dict) -> HeartbeatConfig:
    return HeartbeatConfig(
        ttl_seconds=float(data.get("ttl_seconds", 300.0)),
        db_path=data.get("db_path", "pipewatch_heartbeat.db"),
    )


def wrap_with_heartbeat(inner, config: HeartbeatConfig) -> HeartbeatNotifier:
    store = HeartbeatStore(db_path=config.db_path)
    return HeartbeatNotifier(inner=inner, store=store, ttl_seconds=config.ttl_seconds)
