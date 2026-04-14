"""Notifier wrapper that suppresses duplicate alerts using DeduplicationStore."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from pipewatch.deduplication import DeduplicationStore
from pipewatch.monitor import CheckResult

logger = logging.getLogger(__name__)


class Notifier:
    """Protocol-compatible interface."""

    def send(self, result: CheckResult) -> None:  # pragma: no cover
        raise NotImplementedError


@dataclass
class DeduplicatedNotifier:
    """Wraps an inner notifier and skips sending if the alert is a duplicate.

    Two alerts are considered duplicates when they share the same pipeline name
    and error message and the previous alert has not yet expired (ttl_seconds).
    """

    inner: Notifier
    store: DeduplicationStore
    ttl_seconds: int = 3600

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer")

    def send(self, result: CheckResult) -> None:
        key = self.store.make_key(
            pipeline=result.pipeline_name,
            error=result.error_message,
        )
        if self.store.is_duplicate(key, ttl_seconds=self.ttl_seconds):
            logger.debug(
                "Suppressing duplicate alert for pipeline '%s' (key=%s)",
                result.pipeline_name,
                key,
            )
            return
        self.store.record(key)
        self.inner.send(result)
