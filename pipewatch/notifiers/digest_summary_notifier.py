"""Notifier that sends a summary digest after a batch of checks completes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from pipewatch.notifiers import Notifier
from pipewatch.monitor import CheckResult
from pipewatch.digest import DigestReport


@dataclass
class DigestSummaryNotifier:
    """Accumulates results and forwards a digest summary to an inner notifier.

    Call ``flush()`` to send the accumulated digest as a synthetic result.
    The inner notifier receives a *CheckResult-like* object whose
    ``error_message`` contains the formatted digest text.
    """

    inner: Notifier
    label: str = "digest-summary"
    _buffer: List[CheckResult] = field(default_factory=list, init=False, repr=False)

    # ------------------------------------------------------------------
    # Notifier protocol
    # ------------------------------------------------------------------

    def send(self, result: CheckResult) -> None:  # noqa: D401
        """Buffer *result* without forwarding immediately."""
        self._buffer.append(result)

    # ------------------------------------------------------------------
    # Flush
    # ------------------------------------------------------------------

    def flush(self) -> None:
        """Build a :class:`DigestReport` from buffered results and send it.

        The buffer is cleared after the summary is forwarded so that
        subsequent calls produce fresh summaries.
        """
        if not self._buffer:
            return

        report = DigestReport(results=list(self._buffer))
        summary_text = (
            f"[{self.label}] "
            f"total={report.total} "
            f"passed={report.passed} "
            f"failed={report.failed} "
            f"failure_rate={report.failure_rate:.1%}"
        )

        # Build a synthetic result that carries the digest text.
        synthetic = _DigestResult(
            pipeline_name=self.label,
            success=report.failed == 0,
            error_message=summary_text if report.failed > 0 else None,
        )

        self._buffer.clear()
        self.inner.send(synthetic)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def pending_count(self) -> int:  # noqa: D401
        """Number of results buffered since the last flush."""
        return len(self._buffer)


@dataclass
class _DigestResult:
    """Minimal CheckResult-compatible object used for digest notifications."""

    pipeline_name: str
    success: bool
    error_message: str | None = None
