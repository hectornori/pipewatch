"""Circuit breaker wrapper for notifiers.

Opens the circuit after a configurable number of consecutive send
failures, preventing further attempts until a cooldown window elapses.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


class Notifier:
    """Structural protocol – any object with a send(result) method."""
    def send(self, result) -> None:  # pragma: no cover
        ...


@dataclass
class CircuitBreakerNotifier:
    """Wraps an inner notifier with a circuit-breaker.

    Args:
        inner: The notifier to protect.
        failure_threshold: Consecutive failures before the circuit opens.
        recovery_timeout: Seconds to wait in OPEN state before trying again.
    """
    inner: Notifier
    failure_threshold: int = 3
    recovery_timeout: float = 60.0

    _consecutive_failures: int = field(default=0, init=False, repr=False)
    _opened_at: Optional[float] = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    @property
    def is_open(self) -> bool:
        """Return True when the circuit is open (blocking sends)."""
        if self._opened_at is None:
            return False
        elapsed = time.monotonic() - self._opened_at
        if elapsed >= self.recovery_timeout:
            # Allow one probe attempt (half-open)
            return False
        return True

    @property
    def state(self) -> str:
        if self._opened_at is None:
            return "closed"
        elapsed = time.monotonic() - self._opened_at
        if elapsed >= self.recovery_timeout:
            return "half-open"
        return "open"

    def send(self, result) -> None:
        """Forward *result* to the inner notifier, respecting circuit state."""
        if self.is_open:
            logger.warning(
                "Circuit breaker OPEN – suppressing notification for '%s'",
                getattr(result, "pipeline_name", "unknown"),
            )
            return

        try:
            self.inner.send(result)
        except Exception as exc:  # noqa: BLE001
            self._consecutive_failures += 1
            logger.error(
                "Notifier failure (%d/%d): %s",
                self._consecutive_failures,
                self.failure_threshold,
                exc,
            )
            if self._consecutive_failures >= self.failure_threshold:
                self._opened_at = time.monotonic()
                logger.warning(
                    "Circuit breaker tripped after %d consecutive failures.",
                    self._consecutive_failures,
                )
            raise
        else:
            # Successful send – reset counters
            self._consecutive_failures = 0
            self._opened_at = None

    def reset(self) -> None:
        """Manually close the circuit (useful in tests or admin tooling)."""
        self._consecutive_failures = 0
        self._opened_at = None
