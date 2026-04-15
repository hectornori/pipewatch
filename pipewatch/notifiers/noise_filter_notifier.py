"""Notifier wrapper that suppresses alerts below a minimum failure count threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from pipewatch.monitor import CheckResult


class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


@dataclass
class NoiseFilterNotifier:
    """Suppress alerts until a pipeline has failed at least *min_failures* times
    within the current in-memory window.  Resets on success."""

    inner: Notifier
    min_failures: int = 3
    _counts: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.min_failures < 1:
            raise ValueError("min_failures must be >= 1")

    def send(self, result: CheckResult) -> None:
        name = result.pipeline_name
        if result.success:
            self._counts[name] = 0
            return

        self._counts[name] = self._counts.get(name, 0) + 1
        if self._counts[name] >= self.min_failures:
            self.inner.send(result)

    def reset(self, pipeline_name: str) -> None:
        """Manually reset the failure counter for a pipeline."""
        self._counts.pop(pipeline_name, None)

    @property
    def counts(self) -> dict[str, int]:
        return dict(self._counts)
