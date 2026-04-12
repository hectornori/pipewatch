"""Notifier wrapper that suppresses alerts for healthy pipelines."""
from __future__ import annotations

from typing import Protocol

from pipewatch.monitor import CheckResult
from pipewatch.pipeline_health import HealthScore


class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class HealthAlertNotifier:
    """Only forwards to *inner* when the pipeline's health score is below *threshold*.

    Parameters
    ----------
    inner:
        Downstream notifier.
    score:
        Pre-computed HealthScore for the pipeline being monitored.
    threshold:
        Minimum score (exclusive) below which alerts are sent.  Default 0.75.
    """

    def __init__(
        self,
        inner: Notifier,
        score: HealthScore,
        threshold: float = 0.75,
    ) -> None:
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("threshold must be between 0.0 and 1.0")
        self._inner = inner
        self._score = score
        self._threshold = threshold

    def send(self, result: CheckResult) -> None:
        if self._score.score < self._threshold:
            self._inner.send(result)

    @property
    def health_score(self) -> HealthScore:
        return self._score
