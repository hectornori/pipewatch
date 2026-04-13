"""Notifier that correlates related failures and annotates results with a shared correlation ID."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class CorrelationWindow:
    """Groups failures that occur within a time window into a correlation group."""
    window_seconds: int = 60
    _groups: dict[str, list[object]] = field(default_factory=dict, init=False, repr=False)
    _timestamps: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def correlation_id(self, pipeline_name: str, error_message: str | None) -> str:
        """Return a stable correlation ID for a pipeline + error combination."""
        raw = f"{pipeline_name}:{error_message or ''}"
        return hashlib.sha1(raw.encode()).hexdigest()[:12]

    def is_correlated(self, corr_id: str) -> bool:
        """Return True if this correlation ID is still within an active window."""
        ts = self._timestamps.get(corr_id)
        if ts is None:
            return False
        return (time.monotonic() - ts) < self.window_seconds

    def register(self, corr_id: str, result: object) -> None:
        now = time.monotonic()
        if corr_id not in self._timestamps:
            self._timestamps[corr_id] = now
            self._groups[corr_id] = []
        self._groups[corr_id].append(result)

    def group_size(self, corr_id: str) -> int:
        return len(self._groups.get(corr_id, []))


@dataclass
class _CorrelatedResult:
    _inner: object
    correlation_id: str
    group_size: int

    def __getattr__(self, item: str) -> object:
        return getattr(self._inner, item)

    def __repr__(self) -> str:
        return (
            f"CorrelatedResult(id={self.correlation_id!r}, "
            f"group_size={self.group_size}, inner={self._inner!r})"
        )


class CorrelationNotifier:
    """Wraps an inner notifier, annotating each result with a correlation ID
    that groups related failures occurring within a configurable time window.
    """

    def __init__(
        self,
        inner: Notifier,
        window: CorrelationWindow | None = None,
    ) -> None:
        self._inner = inner
        self._window = window or CorrelationWindow()

    def send(self, result: object) -> None:
        pipeline_name: str = getattr(result, "pipeline_name", "unknown")
        error_message: str | None = getattr(result, "error_message", None)
        success: bool = getattr(result, "success", True)

        if not success:
            corr_id = self._window.correlation_id(pipeline_name, error_message)
            self._window.register(corr_id, result)
            annotated = _CorrelatedResult(
                _inner=result,
                correlation_id=corr_id,
                group_size=self._window.group_size(corr_id),
            )
            self._inner.send(annotated)
        else:
            self._inner.send(result)
