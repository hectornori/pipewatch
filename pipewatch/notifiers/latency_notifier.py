"""Notifier that suppresses alerts when pipeline latency is within acceptable bounds."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class LatencyNotifier:
    """Only forwards alerts when duration_seconds exceeds the given threshold."""

    inner: Notifier
    threshold_seconds: float
    _sent_count: int = field(default=0, init=False, repr=False)
    _suppressed_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.threshold_seconds <= 0:
            raise ValueError("threshold_seconds must be positive")

    def send(self, result) -> None:
        duration = getattr(result, "duration_seconds", None)
        if duration is not None and duration <= self.threshold_seconds:
            self._suppressed_count += 1
            return
        self._sent_count += 1
        self.inner.send(result)

    @property
    def sent_count(self) -> int:
        return self._sent_count

    @property
    def suppressed_count(self) -> int:
        return self._suppressed_count
