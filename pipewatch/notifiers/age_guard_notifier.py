"""AgeGuardNotifier – suppress alerts for results older than a configurable threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class AgeGuardNotifier:
    """Wraps an inner notifier and drops results whose timestamp is too old.

    Args:
        inner: The downstream notifier to forward fresh results to.
        max_age_seconds: Maximum allowed age (in seconds) of a result's
            ``checked_at`` timestamp.  Results older than this are silently
            dropped.  Must be > 0.
        clock: Optional callable returning the current UTC datetime; defaults
            to ``datetime.now(timezone.utc)``.  Useful for testing.
    """

    inner: Notifier
    max_age_seconds: float
    clock: object = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.max_age_seconds <= 0:
            raise ValueError(
                f"max_age_seconds must be > 0, got {self.max_age_seconds}"
            )
        if self.clock is None:
            self.clock = lambda: datetime.now(timezone.utc)

    def send(self, result: object) -> None:
        checked_at: datetime | None = getattr(result, "checked_at", None)
        if checked_at is not None:
            now: datetime = self.clock()  # type: ignore[operator]
            # Ensure both datetimes are timezone-aware for comparison.
            if checked_at.tzinfo is None:
                checked_at = checked_at.replace(tzinfo=timezone.utc)
            age = (now - checked_at).total_seconds()
            if age > self.max_age_seconds:
                return
        self.inner.send(result)
