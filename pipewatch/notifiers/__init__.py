"""Notifier sub-package.

Exports the lightweight Notifier protocol used by all concrete notifier
implementations so callers can import it from a single location.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    """Minimal interface every notifier must satisfy."""

    def send(self, result: object) -> None:
        """Send a notification for *result*."""
        ...


__all__ = ["Notifier"]
