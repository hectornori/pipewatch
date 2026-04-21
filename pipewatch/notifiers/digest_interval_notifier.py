"""Notifier that accumulates results and flushes on a time interval."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Protocol


class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class DigestIntervalNotifier:
    """Buffers results and forwards a digest after *interval_seconds* have elapsed."""

    inner: Notifier
    interval_seconds: float
    _buffer: List = field(default_factory=list, init=False, repr=False)
    _last_flush: float = field(default_factory=time.monotonic, init=False, repr=False)

    def send(self, result) -> None:
        self._buffer.append(result)
        if time.monotonic() - self._last_flush >= self.interval_seconds:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        batch = list(self._buffer)
        self._buffer.clear()
        self._last_flush = time.monotonic()
        digest = _IntervalDigestResult(batch)
        self.inner.send(digest)

    @property
    def pending_count(self) -> int:
        return len(self._buffer)


@dataclass
class _IntervalDigestResult:
    results: List

    @property
    def pipeline_name(self) -> str:
        names = {getattr(r, 'pipeline_name', '?') for r in self.results}
        return ', '.join(sorted(names)) if names else 'unknown'

    @property
    def success(self) -> bool:
        return all(getattr(r, 'success', True) for r in self.results)

    @property
    def error_message(self):
        errors = [getattr(r, 'error_message', None) for r in self.results if not getattr(r, 'success', True)]
        return '; '.join(str(e) for e in errors if e) or None

    def __repr__(self) -> str:
        return f'_IntervalDigestResult(count={len(self.results)}, success={self.success})'
