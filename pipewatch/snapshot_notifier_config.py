"""Configuration helpers for SnapshotNotifier."""
from __future__ import annotations

from dataclasses import dataclass

from pipewatch.snapshot import SnapshotStore
from pipewatch.notifiers.snapshot_notifier import SnapshotNotifier


@dataclass
class SnapshotNotifierConfig:
    db_path: str = ":memory:"

    def __post_init__(self) -> None:
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def snapshot_notifier_config_from_dict(raw: dict) -> SnapshotNotifierConfig:
    return SnapshotNotifierConfig(
        db_path=raw.get("db_path", ":memory:"),
    )


def wrap_with_snapshot(inner, config: SnapshotNotifierConfig) -> SnapshotNotifier:
    store = SnapshotStore(db_path=config.db_path)
    return SnapshotNotifier(inner=inner, store=store)
