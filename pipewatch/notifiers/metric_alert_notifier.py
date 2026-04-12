"""Notifier that fires when a pipeline's average duration exceeds a threshold."""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from pipewatch.metric_collector import MetricCollector
from pipewatch.monitor import CheckResult


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class MetricAlertNotifier:
    """Wraps an inner notifier and adds a synthetic failure when average
    pipeline duration exceeds *threshold_seconds*."""

    def __init__(
        self,
        inner: Notifier,
        collector: MetricCollector,
        threshold_seconds: float,
        window: int = 20,
    ) -> None:
        self._inner = inner
        self._collector = collector
        self._threshold = threshold_seconds
        self._window = window

    def send(self, result: CheckResult) -> None:
        avg = self._collector.average_duration(result.pipeline, limit=self._window)
        if avg is not None and avg > self._threshold:
            slow_result = CheckResult(
                pipeline=result.pipeline,
                success=False,
                error_message=(
                    f"Average duration {avg:.2f}s exceeds threshold "
                    f"{self._threshold:.2f}s (last {self._window} runs)"
                ),
            )
            self._inner.send(slow_result)
        else:
            self._inner.send(result)
