"""MultiNotifier — fan-out notifications to several inner notifiers."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class MultiNotifier:
    """Sends a notification to every registered notifier.

    Failures in individual notifiers are caught and logged so that a
    single broken notifier cannot prevent the others from firing.
    """

    notifiers: List[Notifier] = field(default_factory=list)

    def register(self, notifier: Notifier) -> None:
        """Add a notifier to the fan-out list."""
        if not isinstance(notifier, Notifier):
            raise TypeError(f"{notifier!r} does not implement the Notifier protocol")
        self.notifiers.append(notifier)

    def send(self, result) -> None:
        """Forward *result* to every registered notifier.

        Exceptions raised by individual notifiers are logged at ERROR
        level but do not propagate, ensuring best-effort delivery.
        """
        if not self.notifiers:
            logger.debug("MultiNotifier.send called with no registered notifiers")
            return

        errors: list[tuple[Notifier, Exception]] = []
        for notifier in self.notifiers:
            try:
                notifier.send(result)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Notifier %r raised an error: %s",
                    notifier,
                    exc,
                    exc_info=True,
                )
                errors.append((notifier, exc))

        if errors:
            failed = ", ".join(repr(n) for n, _ in errors)
            logger.warning("%d notifier(s) failed: %s", len(errors), failed)
