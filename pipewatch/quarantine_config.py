"""Configuration helpers for QuarantineNotifier."""
from __future__ import annotations

from dataclasses import dataclass

from pipewatch.notifiers.quarantine_notifier import QuarantineNotifier, QuarantineStore


@dataclass
class QuarantineConfig:
    threshold: int = 3
    db_path: str = "pipewatch_quarantine.db"

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("threshold must be >= 1")
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def quarantine_config_from_dict(data: dict) -> QuarantineConfig:
    """Build a QuarantineConfig from a raw mapping (e.g. parsed YAML)."""
    return QuarantineConfig(
        threshold=int(data.get("threshold", 3)),
        db_path=data.get("db_path", "pipewatch_quarantine.db"),
    )


def wrap_with_quarantine(inner, cfg: QuarantineConfig) -> QuarantineNotifier:
    """Convenience factory used by the builder layer."""
    store = QuarantineStore(db_path=cfg.db_path)
    return QuarantineNotifier(inner=inner, store=store, threshold=cfg.threshold)
