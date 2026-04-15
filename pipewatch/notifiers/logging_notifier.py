"""A notifier that logs alert dispatches to the standard logging system."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class LoggingNotifier:
    """Wraps an inner notifier and emits structured log lines before/after dispatch.

    Useful for audit trails, debugging, and observability without a full
    AuditLog database dependency.
    """

    inner: Notifier
    level: int = logging.INFO
    include_error: bool = True
    _log: logging.Logger = field(default_factory=lambda: logger, init=False, repr=False)

    def send(self, result: object) -> None:
        pipeline = getattr(result, "pipeline_name", "<unknown>")
        success = getattr(result, "success", None)
        error = getattr(result, "error_message", None)

        status = "ok" if success else "fail"
        extra: dict = {"pipeline": pipeline, "status": status}

        if self.include_error and error:
            extra["error"] = error

        self._log.log(
            self.level,
            "[pipewatch] dispatching alert for pipeline=%s status=%s",
            pipeline,
            status,
            extra=extra,
        )

        try:
            self.inner.send(result)
        except Exception as exc:  # noqa: BLE001
            self._log.error(
                "[pipewatch] notifier failed for pipeline=%s: %s",
                pipeline,
                exc,
                exc_info=True,
            )
            raise

        self._log.log(
            self.level,
            "[pipewatch] alert dispatched successfully for pipeline=%s",
            pipeline,
        )
