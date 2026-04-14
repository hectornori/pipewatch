"""Notifier wrapper that applies exponential backoff between repeated failures."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

log = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class BackoffNotifier:
    """Wraps an inner notifier and applies exponential backoff after consecutive send failures.

    Args:
        inner: The underlying notifier to delegate to.
        base_delay: Initial delay in seconds after the first failure.
        max_delay: Upper bound on the delay (seconds).
        multiplier: Factor by which the delay grows each failure.
    """

    inner: Notifier
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    _consecutive_failures: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.multiplier < 1.0:
            raise ValueError("multiplier must be >= 1.0")

    def _current_delay(self) -> float:
        if self._consecutive_failures == 0:
            return 0.0
        delay = self.base_delay * (self.multiplier ** (self._consecutive_failures - 1))
        return min(delay, self.max_delay)

    def send(self, result) -> None:
        delay = self._current_delay()
        if delay > 0:
            log.debug(
                "BackoffNotifier sleeping %.1fs before send (consecutive_failures=%d)",
                delay,
                self._consecutive_failures,
            )
            time.sleep(delay)
        try:
            self.inner.send(result)
            self._consecutive_failures = 0
        except Exception as exc:
            self._consecutive_failures += 1
            log.warning(
                "BackoffNotifier: inner send failed (failure #%d): %s",
                self._consecutive_failures,
                exc,
            )
            raise
