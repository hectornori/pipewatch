"""Configuration helpers for the ReplayNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ReplayConfig:
    """Settings that control dead-letter replay behaviour."""

    enabled: bool = True
    max_entries: int = 50
    db_path: str = "pipewatch_dead_letters.db"

    def __post_init__(self) -> None:
        if self.max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def replay_config_from_dict(data: Dict[str, Any]) -> ReplayConfig:
    """Build a :class:`ReplayConfig` from a plain mapping (e.g. parsed YAML).

    Only keys recognised by :class:`ReplayConfig` are forwarded; unknown keys
    are silently ignored so that future YAML additions don't break older
    versions.
    """
    known = {"enabled", "max_entries", "db_path"}
    filtered = {k: v for k, v in data.items() if k in known}
    return ReplayConfig(**filtered)
