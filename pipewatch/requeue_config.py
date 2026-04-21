"""Configuration helpers for RequeueNotifier."""
from __future__ import annotations

from dataclasses import dataclass

from pipewatch.notifiers.requeue_notifier import RequeueNotifier, RequeueStore


@dataclass
class RequeueConfig:
    db_path: str = "pipewatch_requeue.db"
    flush_limit: int = 10

    def __post_init__(self) -> None:
        if not self.db_path:
            raise ValueError("db_path must not be empty")
        if self.flush_limit < 1:
            raise ValueError("flush_limit must be >= 1")


def requeue_config_from_dict(data: dict) -> RequeueConfig:
    return RequeueConfig(
        db_path=data.get("db_path", "pipewatch_requeue.db"),
        flush_limit=int(data.get("flush_limit", 10)),
    )


def wrap_with_requeue(inner, cfg: RequeueConfig) -> RequeueNotifier:
    store = RequeueStore(db_path=cfg.db_path)
    return RequeueNotifier(inner=inner, store=store)
