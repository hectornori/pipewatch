"""Notifier that accumulates results and sends a digest summary."""
from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from pipewatch.digest import DigestReport
from pipewatch.monitor import CheckResult

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class DigestNotifier:
    """Wraps an inner notifier and sends a digest rather than per-result alerts.

    Call :meth:`flush` to dispatch the accumulated digest via the inner notifier.
    The inner notifier receives a synthetic :class:`CheckResult` whose
    ``error_message`` contains the formatted digest summary.
    """

    def __init__(self, inner: Notifier, *, label: str = "digest") -> None:
        self._inner = inner
        self._label = label
        self._results: list[CheckResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, result: CheckResult) -> None:
        """Buffer *result* for inclusion in the next digest."""
        self._results.append(result)
        logger.debug("DigestNotifier buffered result for '%s'", result.pipeline_name)

    @property
    def pending_count(self) -> int:
        """Number of results buffered since the last flush."""
        return len(self._results)

    def flush(self) -> None:
        """Send the accumulated digest and clear the buffer.

        If no results have been buffered this is a no-op.
        """
        if not self._results:
            logger.debug("DigestNotifier.flush called with empty buffer — skipping")
            return

        report = DigestReport(results=self._results)
        summary = (
            f"[{self._label}] "
            f"total={report.total} "
            f"passed={report.passed} "
            f"failed={report.failed} "
            f"failure_rate={report.failure_rate:.1%}"
        )

        # Build a synthetic result that carries the digest summary.
        synthetic = CheckResult(
            pipeline_name=self._label,
            success=report.failed == 0,
            error_message=summary if report.failed > 0 else None,
        )

        logger.info("DigestNotifier flushing: %s", summary)
        self._inner.send(synthetic)
        self._results.clear()
