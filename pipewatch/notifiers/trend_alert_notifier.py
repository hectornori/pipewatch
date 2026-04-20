"""Notifier that fires only when a pipeline's trend worsens beyond a threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from pipewatch.trend import TrendSummary, analyse
from pipewatch.metric_collector import MetricCollector


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class TrendAlertNotifier:
    """Wraps an inner notifier and only forwards when failure_rate >= threshold."""

    inner: Notifier
    collector: MetricCollector
    failure_rate_threshold: float = 0.5
    lookback: int = 10
    _sent_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not 0.0 <= self.failure_rate_threshold <= 1.0:
            raise ValueError(
                f"failure_rate_threshold must be between 0 and 1, "
                f"got {self.failure_rate_threshold}"
            )
        if self.lookback < 1:
            raise ValueError(f"lookback must be >= 1, got {self.lookback}")

    def send(self, result) -> None:
        pipeline = getattr(result, "pipeline", None)
        if pipeline is None:
            self.inner.send(result)
            return

        recent = self.collector.get_recent(pipeline, limit=self.lookback)
        summary: TrendSummary = analyse(recent)

        if summary.failure_rate >= self.failure_rate_threshold:
            self._sent_count += 1
            self.inner.send(result)

    @property
    def sent_count(self) -> int:
        return self._sent_count
