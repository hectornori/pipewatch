"""Notifier that suppresses alerts outside a defined schedule."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class ScheduleAwareNotifier:
    """Wraps an inner notifier and only forwards during allowed hours."""

    inner: Notifier
    allowed_days: list[int] = field(default_factory=lambda: list(range(7)))  # 0=Mon
    start_time: time = time(0, 0)
    end_time: time = time(23, 59, 59)
    _clock: object = field(default=None, repr=False)

    def _now(self) -> datetime:
        if self._clock is not None:
            return self._clock()
        return datetime.now()

    def _in_schedule(self) -> bool:
        now = self._now()
        if now.weekday() not in self.allowed_days:
            return False
        current = now.time().replace(tzinfo=None)
        return self.start_time <= current <= self.end_time

    def send(self, result: object) -> None:
        if self._in_schedule():
            self.inner.send(result)
