"""Payload transformer notifier — applies a user-supplied transform function
to a CheckResult before forwarding it to an inner notifier.

Useful for enriching, redacting, or reshaping result data before dispatch.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class PayloadTransformer:
    """Wraps an inner notifier and applies *transform* to every result
    before forwarding.

    Args:
        inner:     The downstream notifier.
        transform: A callable that accepts a result and returns a (possibly
                   new) result.  Must not raise; exceptions are caught and
                   the original result is forwarded as a fallback.
    """

    inner: Notifier
    transform: Callable[[object], object]
    _fallback_on_error: bool = field(default=True, repr=False)

    def send(self, result: object) -> None:
        """Transform *result* then forward to the inner notifier."""
        try:
            transformed = self.transform(result)
        except Exception:  # noqa: BLE001
            if self._fallback_on_error:
                transformed = result
            else:
                raise
        self.inner.send(transformed)


def transformer_from_fn(
    inner: Notifier,
    fn: Callable[[object], object],
    *,
    fallback_on_error: bool = True,
) -> PayloadTransformer:
    """Convenience factory for building a :class:`PayloadTransformer`."""
    return PayloadTransformer(
        inner=inner,
        transform=fn,
        _fallback_on_error=fallback_on_error,
    )
