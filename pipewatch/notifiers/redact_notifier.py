"""Notifier wrapper that redacts sensitive fields from results before forwarding."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: Any) -> None:
        ...


_DEFAULT_PATTERNS: list[str] = [
    r"password",
    r"secret",
    r"token",
    r"api[_-]?key",
    r"auth",
]

_REDACTED = "[REDACTED]"


@dataclass
class RedactNotifier:
    """Wraps another notifier and scrubs sensitive substrings from error messages."""

    inner: Notifier
    patterns: list[str] = field(default_factory=lambda: list(_DEFAULT_PATTERNS))
    replacement: str = _REDACTED

    def __post_init__(self) -> None:
        self._compiled = [
            re.compile(p, re.IGNORECASE) for p in self.patterns
        ]

    def send(self, result: Any) -> None:
        redacted = _RedactedResult(result, self._redact_text)
        self.inner.send(redacted)

    def _redact_text(self, text: str) -> str:
        for pattern in self._compiled:
            # Redact values that follow a sensitive key in key=value or key: value style
            text = pattern.sub(self.replacement, text)
        return text


class _RedactedResult:
    """Proxy that redacts the error_message attribute of a CheckResult."""

    def __init__(self, wrapped: Any, redact_fn: Any) -> None:
        object.__setattr__(self, "_wrapped", wrapped)
        object.__setattr__(self, "_redact_fn", redact_fn)

    def __getattr__(self, name: str) -> Any:
        value = getattr(object.__getattribute__(self, "_wrapped"), name)
        if name == "error_message" and isinstance(value, str):
            return object.__getattribute__(self, "_redact_fn")(value)
        return value

    def __repr__(self) -> str:
        return f"_RedactedResult({object.__getattribute__(self, '_wrapped')!r})"
