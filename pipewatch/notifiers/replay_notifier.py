"""ReplayNotifier – re-sends previously failed (dead-letter) notifications."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from pipewatch.notifiers.dead_letter_notifier import DeadLetterStore, DeadLetterEntry
from pipewatch.notifiers import Notifier

logger = logging.getLogger(__name__)


@dataclass
class ReplayNotifier:
    """Reads entries from a DeadLetterStore and re-delivers them via *inner*.

    Entries that succeed on replay are removed from the store.  Entries that
    fail again are left in place so a subsequent replay can retry them.
    """

    inner: Notifier
    store: DeadLetterStore
    max_entries: int = 50

    def replay(self) -> ReplaySummary:
        """Attempt to replay all pending dead-letter entries.

        Returns a :class:`ReplaySummary` describing what happened.
        """
        entries: List[DeadLetterEntry] = self.store.get_pending(limit=self.max_entries)
        succeeded: List[str] = []
        failed: List[str] = []

        for entry in entries:
            try:
                self.inner.send(entry.result)
                self.store.mark_replayed(entry.id)
                succeeded.append(entry.pipeline)
                logger.info("replay: delivered dead-letter entry %s (%s)", entry.id, entry.pipeline)
            except Exception as exc:  # noqa: BLE001
                failed.append(entry.pipeline)
                logger.warning(
                    "replay: failed to deliver entry %s (%s): %s",
                    entry.id,
                    entry.pipeline,
                    exc,
                )

        return ReplaySummary(succeeded=succeeded, failed=failed)


@dataclass
class ReplaySummary:
    """Result of a replay pass."""

    succeeded: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.succeeded) + len(self.failed)

    @property
    def success_count(self) -> int:
        return len(self.succeeded)

    @property
    def failure_count(self) -> int:
        return len(self.failed)
