"""Notifier that only forwards alerts when a metric spike is detected.

A spike is defined as the current duration exceeding the rolling average
by more than a configurable multiplier (e.g. 2x the mean).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from pipewatch.metric_collector import MetricCollector


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None: ...


@dataclass
class SpikeNotifier:
    """Wraps an inner notifier and only forwards when a duration spike occurs."""

    inner: Notifier
    collector: MetricCollector
    multiplier: float = 2.0
    min_samples: int = 3
    _forwarded: int = field(default=0, init=False, repr=False)
    _suppressed: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.multiplier <= 1.0:
            raise ValueError("multiplier must be greater than 1.0")
        if self.min_samples < 1:
            raise ValueError("min_samples must be at least 1")

    def send(self, result: object) -> None:
        pipeline = getattr(result, "pipeline_name", None)
        duration = getattr(result, "duration_seconds", None)

        if pipeline is None or duration is None:
            self.inner.send(result)
            return

        avg = self.collector.average_duration(pipeline, limit=self.min_samples)
        if avg is None:
            # Not enough history — forward unconditionally
            self.inner.send(result)
            self._forwarded += 1
            return

        if duration >= avg * self.multiplier:
            self.inner.send(result)
            self._forwarded += 1
        else:
            self._suppressed += 1

    @property
    def forwarded(self) -> int:
        return self._forwarded

    @property
    def suppressed(self) -> int:
        return self._suppressed
