"""Wraps any notifier with rate-limiting behaviour."""

from __future__ import annotations

import logging
from typing import Protocol, Optional

from pipewatch.monitor import CheckResult
from pipewatch.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    """Structural protocol satisfied by SlackNotifier and EmailNotifier."""

    def send(self, result: CheckResult) -> None:  # pragma: no cover
        ...


class RateLimitedNotifier:
    """Decorates a *notifier* so that it respects a :class:`RateLimiter`.

    If a notification for the same pipeline was already sent within the
    configured window the call is silently dropped and a debug log entry
    is written instead.
    """

    def __init__(
        self,
        notifier: Notifier,
        limiter: RateLimiter,
        window_seconds: Optional[int] = None,
    ) -> None:
        self._notifier = notifier
        self._limiter = limiter
        self._window = window_seconds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, result: CheckResult) -> None:
        """Forward *result* to the underlying notifier unless rate-limited."""
        name = result.pipeline_name
        if self._limiter.is_rate_limited(name, self._window):
            logger.debug(
                "Rate-limited: skipping notification for pipeline '%s'", name
            )
            return
        self._notifier.send(result)
        self._limiter.record_sent(name)
        logger.debug("Notification sent for pipeline '%s'; rate-limit window started.", name)

    # Convenience passthrough so the wrapper can be used transparently
    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RateLimitedNotifier(notifier={self._notifier!r}, "
            f"window={self._window}s)"
        )
