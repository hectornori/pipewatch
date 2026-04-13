"""WindowNotifier – only forwards alerts during a configured time-of-day window."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional

log = logging.getLogger(__name__)


class Notifier:
    """Protocol stub for type-checking."""
    def send(self, result) -> None: ...


@dataclass
class WindowNotifier:
    """Wraps an inner notifier and suppresses alerts outside a time window.

    Args:
        inner: Delegate notifier.
        start: Window start time (inclusive), e.g. time(8, 0).
        end:   Window end time (exclusive), e.g. time(20, 0).
        tz:    Optional timezone name (unused in core logic; callers should
               convert *result* timestamps before passing them in).
    """

    inner: Notifier
    start: time
    end: time
    tz: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError(
                f"Window start ({self.start}) must be before end ({self.end})"
            )

    def _in_window(self, now: time) -> bool:
        return self.start <= now < self.end

    def send(self, result) -> None:
        now = datetime.utcnow().time()
        if self._in_window(now):
            self.inner.send(result)
        else:
            log.debug(
                "WindowNotifier: suppressed alert for '%s' – current time %s "
                "is outside window [%s, %s)",
                getattr(result, "pipeline_name", "?"),
                now.strftime("%H:%M"),
                self.start.strftime("%H:%M"),
                self.end.strftime("%H:%M"),
            )
