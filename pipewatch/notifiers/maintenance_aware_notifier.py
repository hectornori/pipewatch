"""Wraps any Notifier and silences it while a pipeline is in maintenance."""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from pipewatch.maintenance_window import MaintenanceStore
from pipewatch.monitor import CheckResult

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class MaintenanceAwareNotifier:
    """Decorator that suppresses notifications for pipelines in maintenance."""

    def __init__(self, inner: Notifier, store: MaintenanceStore) -> None:
        self._inner = inner
        self._store = store

    def send(self, result: CheckResult) -> None:
        pipeline = result.pipeline_name
        if self._store.is_in_maintenance(pipeline):
            logger.info(
                "[maintenance] Suppressing alert for '%s' — pipeline is in a maintenance window.",
                pipeline,
            )
            return
        self._inner.send(result)
