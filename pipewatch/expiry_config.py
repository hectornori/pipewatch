"""Configuration helpers for ExpiryNotifier."""
from __future__ import annotations

from dataclasses import dataclass

from pipewatch.notifiers.expiry_notifier import ExpiryNotifier, ExpiryStore


@dataclass
class ExpiryConfig:
    ttl_seconds: float
    db_path: str = "pipewatch_expiry.db"

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def expiry_config_from_dict(data: dict) -> ExpiryConfig:
    """Build an ExpiryConfig from a raw config dictionary."""
    if "ttl_seconds" not in data:
        raise KeyError("expiry config requires 'ttl_seconds'")
    return ExpiryConfig(
        ttl_seconds=float(data["ttl_seconds"]),
        db_path=data.get("db_path", "pipewatch_expiry.db"),
    )


def wrap_with_expiry(inner, cfg: ExpiryConfig) -> ExpiryNotifier:
    """Wrap *inner* notifier with expiry suppression."""
    store = ExpiryStore(db_path=cfg.db_path)
    return ExpiryNotifier(inner=inner, store=store, ttl_seconds=cfg.ttl_seconds)
