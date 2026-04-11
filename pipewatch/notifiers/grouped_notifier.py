"""Notifier that batches multiple CheckResults and sends a single grouped message."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Protocol

from pipewatch.monitor import CheckResult


class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


@dataclass
class GroupedNotifier:
    """Collects results and flushes them as a single batched notification.

    Useful for digest-style alerts where you want one message per run cycle
    rather than one message per failing pipeline.
    """

    inner: Notifier
    _buffer: List[CheckResult] = field(default_factory=list, init=False, repr=False)

    def send(self, result: CheckResult) -> None:
        """Buffer the result for later flushing."""
        self._buffer.append(result)

    def flush(self) -> None:
        """Send all buffered results as a single synthetic result and clear the buffer."""
        if not self._buffer:
            return

        failures = [r for r in self._buffer if not r.success]
        if not failures:
            self._buffer.clear()
            return

        # Build a synthetic result that summarises all failures.
        names = ", ".join(r.pipeline_name for r in failures)
        errors = "; ".join(
            f"{r.pipeline_name}: {r.error_message}" for r in failures if r.error_message
        )
        summary = CheckResult(
            pipeline_name=f"[grouped] {names}",
            success=False,
            error_message=errors or "Multiple pipelines failed",
        )
        self._buffer.clear()
        self.inner.send(summary)

    @property
    def buffered(self) -> List[CheckResult]:
        """Return a copy of the current buffer (read-only view)."""
        return list(self._buffer)
