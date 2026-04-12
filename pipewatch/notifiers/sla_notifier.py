"""Notifier that fires when an SLA breach is detected for a pipeline."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from pipewatch.monitor import CheckResult
from pipewatch.sla_tracker import SLABreach, SLATracker


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class SLANotifier:
    """Wraps an inner notifier; enriches the alert message with SLA breach info.

    On each `send` call the SLA window for the pipeline is cleared (the run
    completed — whether it passed or failed the SLA is no longer pending).
    If a breach is detected the inner notifier is called with an augmented
    result whose ``error_message`` describes the breach.
    """

    def __init__(
        self,
        inner: Notifier,
        tracker: SLATracker,
    ) -> None:
        self._inner = inner
        self._tracker = tracker

    def send(self, result: CheckResult) -> None:
        breach: SLABreach | None = self._tracker.check_breach(result.pipeline_name)
        # Clear the window now that the pipeline has been observed
        self._tracker.clear(result.pipeline_name)

        if breach is None:
            self._inner.send(result)
            return

        # Augment the result with SLA breach information
        original_error = result.error_message or ""
        sla_note = breach.reason
        combined = f"{original_error}\n[SLA] {sla_note}".strip()

        import dataclasses

        augmented = dataclasses.replace(result, error_message=combined)
        self._inner.send(augmented)
