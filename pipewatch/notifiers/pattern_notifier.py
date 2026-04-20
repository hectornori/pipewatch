"""Notifier that forwards only when the error message matches a regex pattern."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class PatternNotifier:
    """Wraps an inner notifier and forwards only when the result's error
    message matches *any* of the supplied regex patterns.

    If ``invert`` is True the logic is reversed: the notification is
    forwarded only when **none** of the patterns match (i.e. acts as a
    pattern-based suppressor).
    """

    inner: Notifier
    patterns: list[str] = field(default_factory=list)
    invert: bool = False

    def __post_init__(self) -> None:
        if not self.patterns:
            raise ValueError("At least one pattern must be supplied.")
        self._compiled: list[re.Pattern] = [
            re.compile(p) for p in self.patterns
        ]

    def _matches(self, result) -> bool:
        error: Optional[str] = getattr(result, "error_message", None)
        if error is None:
            return False
        return any(rx.search(error) for rx in self._compiled)

    def send(self, result) -> None:
        matched = self._matches(result)
        should_forward = (not matched) if self.invert else matched
        if should_forward:
            self.inner.send(result)


def pattern_notifier_from_dict(raw: dict, inner: Notifier) -> PatternNotifier:
    """Build a :class:`PatternNotifier` from a config dictionary.

    Expected keys:
        patterns  – list[str], required
        invert    – bool, optional (default False)
    """
    patterns = raw.get("patterns")
    if not patterns or not isinstance(patterns, list):
        raise ValueError("'patterns' must be a non-empty list of strings.")
    invert = bool(raw.get("invert", False))
    return PatternNotifier(inner=inner, patterns=patterns, invert=invert)
