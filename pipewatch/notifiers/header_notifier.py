"""Notifier that injects custom headers/metadata into results before forwarding."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class Notifier(Protocol):
    def send(self, result: Any) -> None:
        ...


@dataclass
class _HeaderedResult:
    """Wraps an existing result and adds extra metadata attributes."""

    _inner: Any
    _headers: dict[str, str]

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._inner, name)

    @property
    def metadata(self) -> dict[str, str]:
        base: dict[str, str] = {}
        if hasattr(self._inner, "metadata"):
            base.update(self._inner.metadata)
        base.update(self._headers)
        return base

    def __repr__(self) -> str:  # pragma: no cover
        return f"_HeaderedResult(inner={self._inner!r}, headers={self._headers!r})"


@dataclass
class HeaderNotifier:
    """Decorates results with a fixed set of key/value headers before
    forwarding to an inner notifier.

    Useful for injecting environment tags, team identifiers, or any
    arbitrary string metadata that downstream notifiers can inspect.
    """

    inner: Notifier
    headers: dict[str, str] = field(default_factory=dict)

    def add_header(self, key: str, value: str) -> None:
        """Add or overwrite a single header entry."""
        if not key:
            raise ValueError("Header key must not be empty.")
        self.headers[key] = value

    def send(self, result: Any) -> None:
        """Wrap *result* with the configured headers and forward."""
        enriched = _HeaderedResult(_inner=result, _headers=dict(self.headers))
        self.inner.send(enriched)


def header_notifier_from_dict(cfg: dict[str, Any], inner: Notifier) -> HeaderNotifier:
    """Build a :class:`HeaderNotifier` from a config mapping.

    Expected keys:
      - ``headers`` (dict[str, str], optional): initial header map.
    """
    raw_headers = cfg.get("headers", {})
    if not isinstance(raw_headers, dict):
        raise TypeError("'headers' must be a mapping of string keys to string values.")
    headers = {str(k): str(v) for k, v in raw_headers.items()}
    return HeaderNotifier(inner=inner, headers=headers)
