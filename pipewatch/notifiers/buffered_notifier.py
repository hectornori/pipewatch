"""Buffered notifier: accumulates results and flushes after a time window or count threshold."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None: ...


@dataclass
class BufferedNotifier:
    """Wraps an inner notifier and buffers results, flushing when the buffer
    reaches *max_size* items or *max_age_seconds* have elapsed since the first
    buffered item was added.
    """

    inner: Notifier
    max_size: int = 10
    max_age_seconds: float = 60.0

    _buffer: List[object] = field(default_factory=list, init=False, repr=False)
    _window_start: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_size < 1:
            raise ValueError("max_size must be >= 1")
        if self.max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be > 0")

    def send(self, result: object) -> None:
        """Buffer *result*; flush automatically when thresholds are exceeded."""
        if not self._buffer:
            self._window_start = time.monotonic()

        self._buffer.append(result)
        logger.debug("Buffered result; buffer size=%d", len(self._buffer))

        if self._should_flush():
            self.flush()

    def flush(self) -> None:
        """Forward all buffered results to the inner notifier and clear the buffer."""
        if not self._buffer:
            return
        logger.info("Flushing %d buffered results", len(self._buffer))
        items = list(self._buffer)
        self._buffer.clear()
        self._window_start = 0.0
        for item in items:
            try:
                self.inner.send(item)
            except Exception:
                logger.exception("Inner notifier raised while flushing")

    @property
    def pending_count(self) -> int:
        return len(self._buffer)

    def _should_flush(self) -> bool:
        if len(self._buffer) >= self.max_size:
            return True
        age = time.monotonic() - self._window_start
        return age >= self.max_age_seconds
