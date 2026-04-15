"""Notifier that attaches a fixed set of tags to every result before forwarding."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class Notifier(Protocol):
    def send(self, result: Any) -> None:
        ...


@dataclass
class _TaggedResult:
    """Thin wrapper that merges extra tags onto an existing result."""

    _inner: Any
    _extra_tags: dict[str, str]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    @property
    def tags(self) -> dict[str, str]:
        base: dict[str, str] = getattr(self._inner, "tags", {}) or {}
        return {**base, **self._extra_tags}


@dataclass
class TaggedNotifier:
    """Wraps an inner notifier and injects static tags into every result.

    Example usage::

        notifier = TaggedNotifier(
            inner=slack_notifier,
            tags={"env": "production", "team": "data-eng"},
        )
    """

    inner: Notifier
    tags: dict[str, str] = field(default_factory=dict)

    def send(self, result: Any) -> None:
        if not self.tags:
            self.inner.send(result)
            return
        enriched = _TaggedResult(_inner=result, _extra_tags=self.tags)
        self.inner.send(enriched)
