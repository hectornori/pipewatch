"""Configuration helpers for ArchiveNotifier."""
from __future__ import annotations

from dataclasses import dataclass

from pipewatch.notifiers.archive_notifier import ArchiveNotifier, ArchiveStore


@dataclass
class ArchiveConfig:
    db_path: str = "pipewatch_archive.db"

    def __post_init__(self) -> None:
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def archive_config_from_dict(data: dict) -> ArchiveConfig:
    return ArchiveConfig(
        db_path=data.get("db_path", "pipewatch_archive.db"),
    )


def wrap_with_archive(inner, cfg: ArchiveConfig) -> ArchiveNotifier:
    """Wrap *inner* notifier with archiving using *cfg*."""
    store = ArchiveStore(db_path=cfg.db_path)
    return ArchiveNotifier(inner=inner, store=store)
