"""Notifier decorator that suppresses alerts while a pipeline is cooling down."""

from __future__ import annotations

import logging
from typing import Optional, Protocol

from pipewatch.cooldown import CooldownStore
from pipewatch.monitor import CheckResult

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class CooldownNotifier:
    """Wraps another notifier and skips sending if the pipeline is in cooldown.

    After a successful send, the cooldown timestamp is recorded.  On pipeline
    recovery (``result.success is True``) the cooldown is cleared so the next
    failure triggers a fresh alert immediately.
    """

    def __init__(
        self,
        inner: Notifier,
        store: CooldownStore,
        cooldown_minutes: Optional[int] = None,
    ) -> None:
        self._inner = inner
        self._store = store
        self._cooldown_minutes = cooldown_minutes

    def send(self, result: CheckResult) -> None:
        pipeline = result.pipeline_name

        if result.success:
            # Recovery — clear any existing cooldown so next failure is fresh.
            self._store.clear(pipeline)
            self._inner.send(result)
            return

        if self._store.is_cooling_down(pipeline, self._cooldown_minutes):
            logger.debug(
                "Cooldown active for '%s'; suppressing alert.", pipeline
            )
            return

        self._inner.send(result)
        self._store.record(pipeline)
        logger.debug("Alert sent for '%s'; cooldown started.", pipeline)
