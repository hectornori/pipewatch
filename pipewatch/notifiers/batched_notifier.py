"""Batched notifier: accumulates alerts and flushes when batch size or timeout is reached."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class BatchedNotifier:
    """Wraps an inner notifier and batches results before forwarding.

    Flushes automatically when *max_size* results have accumulated or when
    *max_age_seconds* seconds have passed since the first item was added.
    Call :meth:`flush` explicitly to force delivery.
    """

    inner: Notifier
    max_size: int = 10
    max_age_seconds: float = 60.0

    _batch: List = field(default_factory=list, init=False, repr=False)
    _batch_start: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_size < 1:
            raise ValueError("max_size must be >= 1")
        if self.max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be > 0")

    def send(self, result) -> None:
        """Add *result* to the current batch, flushing if thresholds are met."""
        if not self._batch:
            self._batch_start = time.monotonic()

        self._batch.append(result)

        age = time.monotonic() - self._batch_start
        if len(self._batch) >= self.max_size or age >= self.max_age_seconds:
            self.flush()

    def flush(self) -> None:
        """Send all buffered results to the inner notifier and clear the batch."""
        if not self._batch:
            return
        for result in self._batch:
            self.inner.send(result)
        self._batch.clear()
        self._batch_start = 0.0

    @property
    def pending(self) -> int:
        """Number of results currently buffered."""
        return len(self._batch)
