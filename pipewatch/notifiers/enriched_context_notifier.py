"""Notifier decorator that enriches CheckResult with pipeline ownership and on-call info."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from pipewatch.notifiers import Notifier, send as _send_proto
from pipewatch.ownership import OwnershipStore
from pipewatch.on_call import OnCallStore

logger = logging.getLogger(__name__)


class Notifier:  # noqa: F811  – local protocol mirror
    def send(self, result) -> None: ...


@dataclass
class EnrichedContextNotifier:
    """Wraps an inner notifier and attaches owner/on-call metadata to results.

    The enriched attributes are written onto a shallow copy-like namespace so
    the original CheckResult dataclass is not mutated.
    """

    inner: object
    ownership_store: OwnershipStore
    on_call_store: OnCallStore

    def send(self, result) -> None:
        enriched = _enrich(result, self.ownership_store, self.on_call_store)
        self.inner.send(enriched)


@dataclass
class _EnrichedResult:
    """Thin wrapper that delegates attribute access to the original result."""

    _original: object
    owner: Optional[str] = field(default=None)
    on_call: Optional[str] = field(default=None)

    def __getattr__(self, name: str):
        return getattr(self._original, name)


def _enrich(result, ownership_store: OwnershipStore, on_call_store: OnCallStore) -> _EnrichedResult:
    pipeline_name: str = getattr(result, "pipeline_name", "")

    owner: Optional[str] = None
    entry = ownership_store.get(pipeline_name)
    if entry is not None:
        owner = entry.owner

    on_call: Optional[str] = None
    active = on_call_store.active_for(pipeline_name)
    if active:
        on_call = active[0].contact

    enriched = _EnrichedResult(_original=result, owner=owner, on_call=on_call)
    logger.debug(
        "Enriched result for '%s': owner=%s on_call=%s",
        pipeline_name,
        owner,
        on_call,
    )
    return enriched
