"""Notifier wrapper that suppresses alerts during a cooldown period per pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from pipewatch.suppression import SuppressionStore


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class SuppressionNotifier:
    """Wraps an inner notifier and suppresses duplicate alerts within a cooldown window.

    Args:
        inner: The notifier to delegate to when not suppressed.
        store: A :class:`SuppressionStore` used to track last-alerted timestamps.
        cooldown_minutes: Minimum minutes between alerts for the same pipeline.
    """

    inner: Notifier
    store: SuppressionStore
    cooldown_minutes: int = 60

    def __post_init__(self) -> None:
        if self.cooldown_minutes < 0:
            raise ValueError("cooldown_minutes must be non-negative")

    def send(self, result: object) -> None:
        pipeline = getattr(result, "pipeline_name", None) or "unknown"
        success = getattr(result, "success", True)

        if success:
            self.inner.send(result)
            return

        if self.store.is_suppressed(pipeline, self.cooldown_minutes):
            return

        self.store.record_alert(pipeline)
        self.inner.send(result)
