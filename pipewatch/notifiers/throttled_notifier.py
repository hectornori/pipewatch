"""ThrottledNotifier: wraps another notifier and skips sends within the cooldown window."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pipewatch.monitor import CheckResult
from pipewatch.throttle import ThrottleStore


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class ThrottledNotifier:
    """Decorator that suppresses duplicate notifications within *min_interval_seconds*."""

    def __init__(
        self,
        inner: Notifier,
        store: ThrottleStore,
        channel: str,
        min_interval_seconds: int = 300,
    ) -> None:
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be >= 0")
        self._inner = inner
        self._store = store
        self._channel = channel
        self._min_interval = min_interval_seconds

    def send(self, result: CheckResult) -> None:
        pipeline = result.pipeline_name
        if self._store.is_throttled(pipeline, self._channel, self._min_interval):
            return
        self._inner.send(result)
        self._store.record(pipeline, self._channel)

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def min_interval_seconds(self) -> int:
        return self._min_interval
