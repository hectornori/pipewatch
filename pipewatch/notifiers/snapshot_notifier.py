"""Notifier that only sends if the pipeline state has changed since the last snapshot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from pipewatch.snapshot import SnapshotStore


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None: ...


@dataclass
class SnapshotNotifier:
    """Suppress notifications when pipeline status has not changed."""

    inner: Notifier
    store: SnapshotStore
    _sent_count: int = field(default=0, init=False, repr=False)

    def send(self, result) -> None:
        previous = self.store.get(result.pipeline_name)

        state_changed = (
            previous is None
            or previous.success != result.success
            or previous.error_message != result.error_message
        )

        self.store.save(result)

        if state_changed:
            self._sent_count += 1
            self.inner.send(result)

    @property
    def sent_count(self) -> int:
        return self._sent_count
