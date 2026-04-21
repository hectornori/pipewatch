"""Notifier that suppresses alerts for pipelines detected as stale.

If a pipeline hasn't produced a successful run within the configured
tolerance window, the alert is forwarded to a dedicated stale-pipeline
notifier instead of the normal inner notifier.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from pipewatch.stale_detector import StaleDetector


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class StaleAlertNotifier:
    """Routes results to *stale_notifier* when the pipeline is stale.

    Parameters
    ----------
    inner:
        Notifier used for healthy (non-stale) pipelines.
    stale_notifier:
        Notifier used when a pipeline is detected as stale.
    detector:
        :class:`~pipewatch.stale_detector.StaleDetector` instance used to
        check staleness.
    stale_only:
        When *True* (default) only stale pipelines are forwarded to
        *stale_notifier* and non-stale pipelines go to *inner*.
        When *False* stale pipelines are forwarded to **both** notifiers.
    """

    inner: Notifier
    stale_notifier: Notifier
    detector: StaleDetector
    stale_only: bool = True

    def send(self, result: object) -> None:
        pipeline_name: str = getattr(result, "pipeline_name", "")
        stale = self.detector.check(pipeline_name)

        if stale is not None:
            self.stale_notifier.send(result)
            if self.stale_only:
                return

        self.inner.send(result)
