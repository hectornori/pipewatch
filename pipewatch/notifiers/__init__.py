"""Notifier sub-package.

Exports the lightweight Notifier protocol used by all concrete notifier
implementations so callers can import it from a single location.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    """Minimal interface every notifier must satisfy.

    Any class that implements a ``send(result: object) -> None`` method
    is considered a valid ``Notifier`` and can be used wherever this
    protocol is expected.  Because the protocol is decorated with
    ``@runtime_checkable``, membership can be verified at runtime via
    ``isinstance(obj, Notifier)``.

    Example::

        class PrintNotifier:
            def send(self, result: object) -> None:
                print(result)

        assert isinstance(PrintNotifier(), Notifier)  # True
    """

    def send(self, result: object) -> None:
        """Send a notification for *result*.

        Parameters
        ----------
        result:
            An arbitrary object describing the pipeline result to be
            communicated (e.g. a status string, a dataclass, or a dict).
        """
        ...


__all__ = ["Notifier"]
