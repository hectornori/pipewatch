"""Watermark notifier: only forwards alerts when a metric crosses a threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class WatermarkNotifier:
    """Forwards a result to *inner* only when the pipeline's failure count
    meets or exceeds *threshold* within the tracked window.

    A simple in-memory high-water-mark is maintained per pipeline name so
    that repeated failures keep triggering while the count stays above the
    threshold, but a single transient failure is silently dropped.
    """

    inner: Notifier
    threshold: int = 3
    _counts: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("threshold must be >= 1")

    def send(self, result) -> None:
        name: str = getattr(result, "pipeline_name", "")
        success: bool = getattr(result, "success", True)

        if success:
            # Reset watermark on recovery
            self._counts.pop(name, None)
            return

        self._counts[name] = self._counts.get(name, 0) + 1

        if self._counts[name] >= self.threshold:
            self.inner.send(result)

    def reset(self, pipeline_name: str) -> None:
        """Manually reset the watermark for *pipeline_name*."""
        self._counts.pop(pipeline_name, None)

    @property
    def counts(self) -> dict[str, int]:
        """Read-only view of current failure counts."""
        return dict(self._counts)
