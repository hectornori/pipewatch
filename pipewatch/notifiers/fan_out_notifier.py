"""Fan-out notifier: broadcasts a result to multiple notifiers in parallel using threads."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class FanOutNotifier:
    """Send a result to all registered notifiers concurrently.

    Args:
        notifiers: List of notifiers to broadcast to.
        max_workers: Thread-pool size (defaults to number of notifiers).
        raise_on_all_failed: If True, raise RuntimeError when every notifier fails.
    """

    notifiers: List[Notifier] = field(default_factory=list)
    max_workers: int = 4
    raise_on_all_failed: bool = False

    def register(self, notifier: Notifier) -> None:
        """Add a notifier to the fan-out list."""
        self.notifiers.append(notifier)

    def send(self, result) -> None:
        """Broadcast *result* to all notifiers in parallel."""
        if not self.notifiers:
            logger.debug("FanOutNotifier: no notifiers registered, nothing to do.")
            return

        workers = min(self.max_workers, len(self.notifiers))
        failures: list[Exception] = []

        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_notifier = {
                pool.submit(n.send, result): n for n in self.notifiers
            }
            for future in as_completed(future_to_notifier):
                notifier = future_to_notifier[future]
                exc = future.exception()
                if exc is not None:
                    logger.warning(
                        "FanOutNotifier: notifier %s raised %s: %s",
                        type(notifier).__name__,
                        type(exc).__name__,
                        exc,
                    )
                    failures.append(exc)

        if self.raise_on_all_failed and len(failures) == len(self.notifiers):
            raise RuntimeError(
                f"All {len(self.notifiers)} notifiers failed; "
                f"last error: {failures[-1]}"
            )
