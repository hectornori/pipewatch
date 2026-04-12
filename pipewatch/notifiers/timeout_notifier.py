"""Notifier wrapper that enforces a send timeout using a thread."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


class Notifier:
    """Protocol satisfied by all notifiers."""

    def send(self, result) -> None:  # pragma: no cover
        ...


@dataclass
class TimeoutNotifier:
    """Wraps an inner notifier and aborts the send if it exceeds *timeout_seconds*.

    If the inner notifier does not finish within the allowed time the call
    returns without raising so that the rest of the alerting chain is not
    blocked.  A warning is logged instead.
    """

    inner: Notifier
    timeout_seconds: float = 5.0
    _raised: Optional[Exception] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive number")

    def send(self, result) -> None:
        exc_holder: list[Exception] = []

        def _target() -> None:
            try:
                self.inner.send(result)
            except Exception as exc:  # noqa: BLE001
                exc_holder.append(exc)

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout_seconds)

        if thread.is_alive():
            log.warning(
                "TimeoutNotifier: send to %s timed out after %.1fs for pipeline '%s'",
                type(self.inner).__name__,
                self.timeout_seconds,
                getattr(result, "pipeline_name", "<unknown>"),
            )
            return

        if exc_holder:
            log.error(
                "TimeoutNotifier: inner notifier %s raised %s",
                type(self.inner).__name__,
                exc_holder[0],
            )
            raise exc_holder[0]
